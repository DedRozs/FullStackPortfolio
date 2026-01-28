"""Tick validation for filtering erroneous market data.

Databento intentionally does not clean erroneous ticks to preserve data
authenticity (see their normalization docs on "ex post cleaning"). However,
these erroneous ticks can corrupt our analysis (e.g., session low showing
52.75 instead of ~7000 for ES futures).

This module provides domain logic for identifying and filtering bad ticks
based on price deviation from surrounding context and dynamic reference prices.

Common causes of erroneous ticks:
- Busted/cancelled trades that weren't removed from feed
- Fat-finger errors that got published before cancellation
- Packet corruption or decoding errors
- Test trades on production feeds

Validation Strategy:
1. OHLC consistency - Basic sanity (high >= low, O/C within H/L)
2. Contextual deviation - Price shouldn't deviate >20% from neighbors
3. Dynamic reference - If no neighbors, compare to recent session median

Reference: https://databento.com/docs/standards-and-conventions/normalization
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Protocol, Callable
from datetime import datetime, date, timedelta
import logging
import statistics

logger = logging.getLogger(__name__)


# Maximum allowed deviation from reference price (as a ratio)
# 20% is generous - real intraday moves rarely exceed 5% even on volatile days
MAX_DEVIATION_RATIO = 0.20

# Fallback: minimum reasonable price for any equity index future
# This is a last-resort sanity check, not the primary filter
MIN_REASONABLE_PRICE = 100.0


class BarLike(Protocol):
    """Protocol for bar-like objects that can be validated."""
    @property
    def open_price(self) -> Decimal: ...
    @property
    def high_price(self) -> Decimal: ...
    @property
    def low_price(self) -> Decimal: ...
    @property
    def close_price(self) -> Decimal: ...
    @property
    def timestamp(self) -> datetime: ...


@dataclass(frozen=True)
class TickValidationResult:
    """Result of tick validation."""
    is_valid: bool
    reason: Optional[str] = None
    
    @classmethod
    def valid(cls) -> 'TickValidationResult':
        return cls(is_valid=True)
    
    @classmethod
    def invalid(cls, reason: str) -> 'TickValidationResult':
        return cls(is_valid=False, reason=reason)


# Type for reference price lookup function (dependency injection)
ReferencePriceLookup = Callable[[str, date], Optional[Decimal]]


class TickValidator:
    """Domain service for validating tick/bar data quality.
    
    This validator filters out erroneous market data that could corrupt
    session analysis. It uses dynamic reference prices rather than
    hardcoded bounds, making it resilient to market level changes over time.
    
    Validation strategies (in order):
    1. OHLC consistency - high >= low, O/C within H/L
    2. Contextual deviation - Compare to neighboring bars in same batch
    3. Dynamic reference - Compare to recent session median from database
    """
    
    def __init__(
        self,
        instrument: str,
        max_deviation_ratio: float = MAX_DEVIATION_RATIO,
        reference_price_lookup: Optional[ReferencePriceLookup] = None,
    ):
        """Initialize validator for a specific instrument.
        
        Args:
            instrument: Yahoo Finance symbol (e.g., 'ES=F')
            max_deviation_ratio: Max allowed deviation from reference (default 0.20 = 20%)
            reference_price_lookup: Optional function to get reference price from DB.
                Signature: (instrument: str, session_date: date) -> Optional[Decimal]
                If not provided, only contextual validation is used.
        """
        self.instrument = instrument
        self.max_deviation_ratio = max_deviation_ratio
        self._reference_lookup = reference_price_lookup
        self._reference_cache: dict[date, Optional[Decimal]] = {}
    
    def get_reference_price(self, session_date: date) -> Optional[Decimal]:
        """Get dynamic reference price for a session.
        
        Returns the median close price from recent sessions, or None if
        no historical data is available.
        """
        if session_date in self._reference_cache:
            return self._reference_cache[session_date]
        
        if self._reference_lookup:
            ref_price = self._reference_lookup(self.instrument, session_date)
            self._reference_cache[session_date] = ref_price
            return ref_price
        
        return None
    
    def validate_bar(
        self,
        bar: BarLike,
        reference_price: Optional[Decimal] = None,
        prev_bar: Optional[BarLike] = None,
        next_bar: Optional[BarLike] = None,
    ) -> TickValidationResult:
        """Validate a single bar against quality checks.
        
        Args:
            bar: The bar to validate
            reference_price: Dynamic reference price for deviation check
            prev_bar: Previous bar for context (optional)
            next_bar: Next bar for context (optional)
            
        Returns:
            TickValidationResult indicating if bar is valid
        """
        # 1. Check OHLC consistency first (always applies)
        if bar.high_price < bar.low_price:
            return TickValidationResult.invalid(
                f"OHLC inconsistent: high ({bar.high_price}) < low ({bar.low_price})"
            )
        
        if bar.open_price > bar.high_price or bar.open_price < bar.low_price:
            return TickValidationResult.invalid(
                f"Open ({bar.open_price}) outside H/L range [{bar.low_price}, {bar.high_price}]"
            )
        
        if bar.close_price > bar.high_price or bar.close_price < bar.low_price:
            return TickValidationResult.invalid(
                f"Close ({bar.close_price}) outside H/L range [{bar.low_price}, {bar.high_price}]"
            )
        
        # 2. Minimum sanity check (catches obviously wrong data like 0 or negative)
        if float(bar.low_price) < MIN_REASONABLE_PRICE:
            return TickValidationResult.invalid(
                f"Low price ({bar.low_price}) below minimum threshold ({MIN_REASONABLE_PRICE})"
            )
        
        # 3. Build reference for deviation check
        # Priority: neighbors > explicit reference > lookup
        context_prices: List[float] = []
        
        if prev_bar:
            context_prices.append(float(prev_bar.close_price))
        if next_bar:
            context_prices.append(float(next_bar.open_price))
        
        if context_prices:
            # Use neighbor context
            ref = statistics.median(context_prices)
        elif reference_price:
            # Use provided reference
            ref = float(reference_price)
        else:
            # No reference available - can only check OHLC consistency
            return TickValidationResult.valid()
        
        # 4. Check deviation from reference
        for price_name, price_val in [
            ('low', bar.low_price),
            ('high', bar.high_price),
        ]:
            deviation = abs(float(price_val) - ref) / ref
            if deviation > self.max_deviation_ratio:
                return TickValidationResult.invalid(
                    f"{price_name} price ({price_val}) deviates {deviation:.1%} "
                    f"from reference ({ref:.2f}), threshold is {self.max_deviation_ratio:.0%}"
                )
        
        return TickValidationResult.valid()
    
    def filter_bars(
        self,
        bars: List[BarLike],
        session_date: Optional[date] = None,
        log_filtered: bool = True,
    ) -> List[BarLike]:
        """Filter a list of bars, removing invalid ones.
        
        Uses a multi-pass approach:
        1. First pass: Check OHLC consistency and minimum price
        2. Second pass: Calculate batch median from pass 1 survivors
        3. Third pass: Check deviation against batch median + neighbors
        
        Args:
            bars: List of bars to filter (should be sorted by timestamp)
            session_date: Optional session date for reference lookup
            log_filtered: Whether to log filtered bars
            
        Returns:
            List of valid bars
        """
        if not bars:
            return []
        
        # Pass 1: Basic sanity checks (OHLC consistency, minimum price)
        pass1_survivors: List[tuple[int, BarLike]] = []
        for i, bar in enumerate(bars):
            result = self._check_basic_sanity(bar)
            if result.is_valid:
                pass1_survivors.append((i, bar))
            elif log_filtered:
                logger.warning(
                    f"Filtered bar (sanity): {self.instrument} "
                    f"{bar.timestamp} - {result.reason}"
                )
        
        if not pass1_survivors:
            return []
        
        # Pass 2: Calculate batch median from survivors (dynamic reference)
        batch_prices = [float(bar.close_price) for _, bar in pass1_survivors]
        batch_median = Decimal(str(statistics.median(batch_prices)))
        
        # Also try to get historical reference if available
        historical_ref = None
        if session_date and self._reference_lookup:
            historical_ref = self.get_reference_price(session_date)
        
        # Use batch median as primary reference, historical as validation
        reference_price = batch_median
        
        # If historical reference differs significantly from batch median,
        # the whole batch might be suspect - log warning but proceed
        if historical_ref:
            batch_vs_hist = abs(float(batch_median) - float(historical_ref)) / float(historical_ref)
            if batch_vs_hist > self.max_deviation_ratio:
                logger.warning(
                    f"Batch median ({batch_median}) differs {batch_vs_hist:.1%} from "
                    f"historical reference ({historical_ref}) for {self.instrument}"
                )
        
        # Pass 3: Check deviation using neighbors + reference
        valid_bars: List[BarLike] = []
        survivor_map = {i: bar for i, bar in pass1_survivors}
        survivor_indices = [i for i, _ in pass1_survivors]
        
        for idx, (orig_idx, bar) in enumerate(pass1_survivors):
            # Find neighboring survivors
            prev_bar = None
            if idx > 0:
                prev_bar = pass1_survivors[idx - 1][1]
            
            next_bar = None
            if idx < len(pass1_survivors) - 1:
                next_bar = pass1_survivors[idx + 1][1]
            
            result = self.validate_bar(bar, reference_price, prev_bar, next_bar)
            if result.is_valid:
                valid_bars.append(bar)
            elif log_filtered:
                logger.warning(
                    f"Filtered bar (deviation): {self.instrument} "
                    f"{bar.timestamp} - {result.reason}"
                )
        
        filtered_count = len(bars) - len(valid_bars)
        if filtered_count > 0:
            logger.info(
                f"Tick validation: Filtered {filtered_count}/{len(bars)} bars "
                f"for {self.instrument} ({filtered_count/len(bars):.1%})"
            )
        
        return valid_bars
    
    def _check_basic_sanity(self, bar: BarLike) -> TickValidationResult:
        """Check basic sanity (OHLC consistency, minimum price)."""
        # OHLC consistency
        if bar.high_price < bar.low_price:
            return TickValidationResult.invalid("high < low")
        
        if bar.open_price > bar.high_price or bar.open_price < bar.low_price:
            return TickValidationResult.invalid("open outside H/L")
        
        if bar.close_price > bar.high_price or bar.close_price < bar.low_price:
            return TickValidationResult.invalid("close outside H/L")
        
        # Minimum sanity
        if float(bar.low_price) < MIN_REASONABLE_PRICE:
            return TickValidationResult.invalid(
                f"low ({bar.low_price}) < min ({MIN_REASONABLE_PRICE})"
            )
        
        return TickValidationResult.valid()


def get_reference_price_from_db(instrument: str, session_date: date) -> Optional[Decimal]:
    """Look up reference price from recent database sessions.
    
    Returns the median close price from the last 5 trading sessions,
    excluding the requested session date.
    
    This function imports Django models lazily to avoid circular imports.
    """
    # Lazy import to avoid circular dependency
    from apps.trading.infrastructure.models import IntradayBarModel
    from django.db.models import Avg
    
    # Look for recent sessions (last 10 calendar days, ~5 trading days)
    start_date = session_date - timedelta(days=10)
    
    # Get average close from recent RTH bars
    result = IntradayBarModel.objects.filter(
        instrument=instrument,
        session_date__gte=start_date,
        session_date__lt=session_date,  # Exclude current session
        session_type='rth',
    ).aggregate(avg_close=Avg('close_price'))
    
    avg_close = result.get('avg_close')
    if avg_close:
        return Decimal(str(avg_close))
    
    return None


def create_tick_validator(
    instrument: str,
    use_db_reference: bool = True,
) -> TickValidator:
    """Factory function for TickValidator.
    
    Args:
        instrument: Yahoo Finance symbol (e.g., 'ES=F')
        use_db_reference: Whether to use database for reference prices
    """
    reference_lookup = get_reference_price_from_db if use_db_reference else None
    return TickValidator(
        instrument=instrument,
        reference_price_lookup=reference_lookup,
    )
