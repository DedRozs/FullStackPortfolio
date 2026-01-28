"""Intraday analysis service for extracting session metrics from 1-minute bars.

This service processes stored intraday bars to generate session progression
context for the AI content generator, including:
- High/low timing
- Session phases (opening drive, mid-session, closing action)
- Volume distribution
- Key price action events
- Raw 1-minute bar data for authentic price action narrative
"""
import logging
import platform
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import List, Optional
from zoneinfo import ZoneInfo

from apps.trading.infrastructure.models import IntradayBarModel
from apps.trading.domain.tick_validation import create_tick_validator

logger = logging.getLogger(__name__)

ET = ZoneInfo('America/New_York')
UTC = ZoneInfo('UTC')

# Cross-platform time format (%-I on Unix, %#I on Windows)
_TIME_FMT = "%#I:%M %p" if platform.system() == "Windows" else "%-I:%M %p"


@dataclass(frozen=True)
class MinuteBar:
    """A single 1-minute OHLCV bar for prompt context."""
    time_et: str  # "9:30 AM", "10:15 AM", etc.
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    
    @property
    def change(self) -> Decimal:
        return self.close - self.open
    
    @property
    def range(self) -> Decimal:
        return self.high - self.low
    
    def to_line(self) -> str:
        """Format as a single line for prompt."""
        direction = "▲" if self.change > 0 else "▼" if self.change < 0 else "─"
        return f"{self.time_et}: {self.open} → {self.close} ({self.change:+.2f}) {direction} vol:{self.volume:,}"


@dataclass
class SessionPhase:
    """Summary of a trading session phase."""
    name: str  # e.g., "Opening 30min", "Mid-Session", "Final Hour"
    start_time: datetime
    end_time: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: int
    bar_count: int
    
    @property
    def range_points(self) -> Decimal:
        return self.high_price - self.low_price
    
    @property
    def change_points(self) -> Decimal:
        return self.close_price - self.open_price
    
    @property
    def direction(self) -> str:
        if self.change_points > 0:
            return "bullish"
        elif self.change_points < 0:
            return "bearish"
        return "flat"


@dataclass
class PriceExtreme:
    """Information about a session high or low."""
    price: Decimal
    timestamp: datetime
    time_et: str  # Human-readable time like "10:35 AM ET"
    is_high: bool
    phase: str  # Which phase this occurred in


@dataclass
class SessionProgression:
    """Complete session progression analysis.
    
    This dataclass contains all the intraday context needed for
    the AI content generator to write accurate price action narrative.
    """
    instrument: str
    session_date: date
    
    # RTH overall summary
    rth_open: Decimal
    rth_high: Decimal
    rth_low: Decimal
    rth_close: Decimal
    rth_volume: int
    
    # Overnight session (if available)
    overnight_high: Optional[Decimal] = None
    overnight_low: Optional[Decimal] = None
    overnight_close: Optional[Decimal] = None
    overnight_volume: Optional[int] = None
    
    # Gap analysis
    gap_points: Optional[Decimal] = None  # RTH open vs prior close
    gap_direction: Optional[str] = None  # "gap_up", "gap_down", "flat"
    gap_filled: Optional[bool] = None
    
    # High/low timing
    session_high_info: Optional[PriceExtreme] = None
    session_low_info: Optional[PriceExtreme] = None
    
    # Session phases (CME futures schedule)
    opening_30min: Optional[SessionPhase] = None     # 9:30 AM - 10:00 AM
    mid_session: Optional[SessionPhase] = None       # 10:00 AM - 3:00 PM
    final_hour: Optional[SessionPhase] = None        # 3:00 PM - 4:00 PM (cash close)
    post_cash: Optional[SessionPhase] = None         # 4:00 PM - 5:00 PM (extended)
    
    # Volume distribution
    am_volume_pct: Optional[float] = None  # % volume before noon
    pm_volume_pct: Optional[float] = None  # % volume after noon
    
    # Price action characteristics
    opening_drive_type: Optional[str] = None  # "gap_and_go", "fade", "chop", "trend"
    closing_action: Optional[str] = None  # "strong_close", "weak_close", "neutral"
    
    # Significant bars (high volume, large range)
    reversal_bars: list = field(default_factory=list)
    
    # Raw 1-minute bars for AI context (sampled every 5 min by default)
    rth_bars: List[MinuteBar] = field(default_factory=list)
    overnight_bars: List[MinuteBar] = field(default_factory=list)
    
    def to_prompt_context(self, include_raw_bars: bool = True) -> str:
        """Format as context string for AI prompt.
        
        Args:
            include_raw_bars: Whether to include the raw bar data. 
                Defaults to True for rich price action narrative.
        """
        lines = [
            f"## Intraday Session Progression for {self.instrument}",
            f"Session Date: {self.session_date}",
            "",
            "### RTH Summary",
            f"Open: {self.rth_open} | High: {self.rth_high} | Low: {self.rth_low} | Close: {self.rth_close}",
            f"Total Volume: {self.rth_volume:,}",
        ]
        
        if self.overnight_high is not None:
            lines.extend([
                "",
                "### Overnight Session",
                f"Overnight High: {self.overnight_high}",
                f"Overnight Low: {self.overnight_low}",
                f"Overnight Close: {self.overnight_close}",
            ])
        
        if self.gap_points is not None:
            lines.extend([
                "",
                f"### Gap Analysis",
                f"Gap: {self.gap_points:+.2f} points ({self.gap_direction})",
                f"Gap Filled: {'Yes' if self.gap_filled else 'No'}",
            ])
        
        if self.session_high_info:
            lines.extend([
                "",
                "### High/Low Timing",
                f"Session High: {self.session_high_info.price} at {self.session_high_info.time_et} ({self.session_high_info.phase})",
                f"Session Low: {self.session_low_info.price} at {self.session_low_info.time_et} ({self.session_low_info.phase})",
            ])
        
        if self.opening_30min:
            lines.extend([
                "",
                "### Session Phases",
                f"**Opening 30min** ({self.opening_drive_type or 'unknown'}):",
                f"  Range: {self.opening_30min.range_points:.2f} pts, Direction: {self.opening_30min.direction}",
                f"  Open: {self.opening_30min.open_price} → Close: {self.opening_30min.close_price}",
            ])
        
        if self.mid_session:
            lines.extend([
                f"**Mid-Session (10:00 AM - 3:00 PM):**",
                f"  Range: {self.mid_session.range_points:.2f} pts, Direction: {self.mid_session.direction}",
            ])
        
        if self.final_hour:
            lines.extend([
                f"**Final Hour (3:00 PM - 4:00 PM, Cash Close)** ({self.closing_action or 'unknown'}):",
                f"  Range: {self.final_hour.range_points:.2f} pts, Direction: {self.final_hour.direction}",
                f"  4:00 PM Close: {self.final_hour.close_price}",
            ])
        
        if self.post_cash:
            lines.extend([
                f"**Post-Cash (4:00 PM - 5:00 PM, Extended):**",
                f"  Range: {self.post_cash.range_points:.2f} pts, Direction: {self.post_cash.direction}",
                f"  5:00 PM Settlement: {self.post_cash.close_price}",
            ])
        
        if self.am_volume_pct is not None:
            lines.extend([
                "",
                "### Volume Distribution",
                f"AM Volume (before noon): {self.am_volume_pct:.1f}%",
                f"PM Volume (after noon): {self.pm_volume_pct:.1f}%",
            ])
        
        # Include all 1-minute bar data for authentic price action narrative
        if include_raw_bars:
            if self.overnight_bars:
                lines.extend([
                    "",
                    f"### Overnight Price Action ({len(self.overnight_bars)} bars, 1-minute)",
                    "Time | Open → Close (Change) | Volume",
                    "---|---|---",
                ])
                for bar in self.overnight_bars:
                    lines.append(bar.to_line())
            
            if self.rth_bars:
                lines.extend([
                    "",
                    f"### RTH Price Action ({len(self.rth_bars)} bars, 1-minute)",
                    "Time | Open → Close (Change) | Volume",
                    "---|---|---",
                ])
                for bar in self.rth_bars:
                    lines.append(bar.to_line())
        
        return "\n".join(lines)


class IntradayAnalysisService:
    """Service for analyzing stored intraday bar data."""
    
    def analyze_session(
        self,
        instrument: str,
        session_date: date,
        prior_close: Optional[Decimal] = None,
    ) -> Optional[SessionProgression]:
        """Analyze a trading session's intraday progression.
        
        Args:
            instrument: Yahoo Finance symbol (e.g., 'ES=F')
            session_date: The trading date to analyze
            prior_close: Prior session close price for gap calculation
        
        Returns:
            SessionProgression with full analysis, or None if no data
        """
        # Fetch all bars for the session
        bars = list(IntradayBarModel.objects.filter(
            instrument=instrument,
            session_date=session_date,
        ).order_by('timestamp'))
        
        if not bars:
            logger.warning(f"No intraday bars found for {instrument} on {session_date}")
            return None
        
        # Safety net: Filter any erroneous ticks that slipped through import
        # This should rarely filter anything if sync_service did its job
        validator = create_tick_validator(instrument, use_db_reference=True)
        original_count = len(bars)
        bars = validator.filter_bars(bars, session_date=session_date, log_filtered=True)
        
        if len(bars) < original_count:
            logger.warning(
                f"Analysis filtered {original_count - len(bars)} erroneous bars "
                f"for {instrument} {session_date} (should have been caught at import)"
            )
        
        if not bars:
            logger.warning(f"All bars filtered as erroneous for {instrument} on {session_date}")
            return None
        
        # Separate overnight and RTH bars
        overnight_bars = [b for b in bars if b.session_type == 'overnight']
        rth_bars = [b for b in bars if b.session_type == 'rth']
        
        if not rth_bars:
            logger.warning(f"No RTH bars found for {instrument} on {session_date}")
            return None
        
        # Calculate RTH summary
        rth_open = rth_bars[0].open_price
        rth_close = rth_bars[-1].close_price
        rth_high = max(b.high_price for b in rth_bars)
        rth_low = min(b.low_price for b in rth_bars)
        rth_volume = sum(b.volume for b in rth_bars)
        
        progression = SessionProgression(
            instrument=instrument,
            session_date=session_date,
            rth_open=rth_open,
            rth_high=rth_high,
            rth_low=rth_low,
            rth_close=rth_close,
            rth_volume=rth_volume,
        )
        
        # Overnight analysis
        if overnight_bars:
            progression.overnight_high = max(b.high_price for b in overnight_bars)
            progression.overnight_low = min(b.low_price for b in overnight_bars)
            progression.overnight_close = overnight_bars[-1].close_price
            progression.overnight_volume = sum(b.volume for b in overnight_bars)
        
        # Gap analysis
        if prior_close is not None:
            progression.gap_points = rth_open - prior_close
            if progression.gap_points > Decimal('0.5'):
                progression.gap_direction = "gap_up"
                progression.gap_filled = rth_low <= prior_close
            elif progression.gap_points < Decimal('-0.5'):
                progression.gap_direction = "gap_down"
                progression.gap_filled = rth_high >= prior_close
            else:
                progression.gap_direction = "flat"
                progression.gap_filled = None
        
        # Find high/low timing
        high_bar = max(rth_bars, key=lambda b: b.high_price)
        low_bar = min(rth_bars, key=lambda b: b.low_price)
        
        progression.session_high_info = self._create_extreme_info(
            high_bar, is_high=True, session_date=session_date
        )
        progression.session_low_info = self._create_extreme_info(
            low_bar, is_high=False, session_date=session_date
        )
        
        # Analyze session phases
        progression.opening_30min = self._analyze_phase(
            rth_bars, "Opening 30min",
            start_time=time(9, 30), end_time=time(10, 0),
            session_date=session_date,
        )
        progression.mid_session = self._analyze_phase(
            rth_bars, "Mid-Session",
            start_time=time(10, 0), end_time=time(15, 0),
            session_date=session_date,
        )
        progression.final_hour = self._analyze_phase(
            rth_bars, "Final Hour",
            start_time=time(15, 0), end_time=time(16, 0),
            session_date=session_date,
        )
        progression.post_cash = self._analyze_phase(
            rth_bars, "Post-Cash",
            start_time=time(16, 0), end_time=time(17, 0),
            session_date=session_date,
        )
        
        # Volume distribution
        noon_et = datetime.combine(session_date, time(12, 0), tzinfo=ET).astimezone(UTC)
        am_volume = sum(b.volume for b in rth_bars if b.timestamp < noon_et)
        pm_volume = sum(b.volume for b in rth_bars if b.timestamp >= noon_et)
        if rth_volume > 0:
            progression.am_volume_pct = (am_volume / rth_volume) * 100
            progression.pm_volume_pct = (pm_volume / rth_volume) * 100
        
        # Classify opening drive
        if progression.opening_30min:
            progression.opening_drive_type = self._classify_opening_drive(
                progression.opening_30min,
                progression.gap_points,
            )
        
        # Classify closing action
        if progression.final_hour:
            progression.closing_action = self._classify_closing_action(
                progression.final_hour,
                rth_open, rth_close,
            )
        
        # Include all raw bars for AI context (o3 has 200K context window)
        # RTH: ~390 bars, Overnight: ~1050 bars = ~30K tokens total
        progression.rth_bars = self._convert_bars(rth_bars)
        if overnight_bars:
            progression.overnight_bars = self._convert_bars(overnight_bars)
        
        return progression
    
    def get_overnight_bars(
        self,
        instrument: str,
        session_date: date,
    ) -> List[MinuteBar]:
        """Get overnight session bars as of current time for pre-market context.
        
        This retrieves bars from 6:00 PM the prior evening through now (or RTH open).
        Used for pre-market briefing to show overnight price action.
        
        Args:
            instrument: Futures symbol (e.g., 'ES=F')
            session_date: The trading date (bars from prior evening 6PM onward)
        
        Returns:
            List of MinuteBar for overnight session
        """
        # Overnight for session_date started at 6PM on (session_date - 1 day)
        prior_day = session_date - timedelta(days=1)
        overnight_start_utc = datetime.combine(
            prior_day, time(23, 0), tzinfo=UTC  # 6PM ET = 11PM UTC (winter)
        )
        # Cap at 9:30 AM ET on session_date
        rth_open_utc = datetime.combine(
            session_date, time(14, 30), tzinfo=UTC  # 9:30 AM ET = 2:30 PM UTC
        )
        
        # Fetch overnight bars
        bars = list(IntradayBarModel.objects.filter(
            instrument=instrument,
            session_date=session_date,
            session_type='overnight',
        ).order_by('timestamp'))
        
        if not bars:
            logger.debug(f"No overnight bars found for {instrument} on {session_date}")
            return []
        
        return self._convert_bars(bars)
    
    def _convert_bars(
        self,
        bars: list[IntradayBarModel],
    ) -> List[MinuteBar]:
        """Convert ORM bars to MinuteBar dataclasses for prompt context.
        
        Args:
            bars: List of 1-minute bars from database
        
        Returns:
            List of MinuteBar dataclasses
        """
        converted = []
        for bar in bars:
            bar_time_utc = bar.timestamp
            if bar_time_utc.tzinfo is None:
                bar_time_utc = bar_time_utc.replace(tzinfo=UTC)
            bar_time_et = bar_time_utc.astimezone(ET)
            
            converted.append(MinuteBar(
                time_et=bar_time_et.strftime(_TIME_FMT),
                open=bar.open_price,
                high=bar.high_price,
                low=bar.low_price,
                close=bar.close_price,
                volume=bar.volume,
            ))
        return converted
    
    def _create_extreme_info(
        self,
        bar: IntradayBarModel,
        is_high: bool,
        session_date: date,
    ) -> PriceExtreme:
        """Create a PriceExtreme from a bar."""
        bar_time_utc = bar.timestamp
        if bar_time_utc.tzinfo is None:
            bar_time_utc = bar_time_utc.replace(tzinfo=UTC)
        
        bar_time_et = bar_time_utc.astimezone(ET)
        time_str = bar_time_et.strftime(_TIME_FMT) + " ET"
        
        # Determine phase
        bar_time_local = bar_time_et.time()
        if bar_time_local < time(10, 0):
            phase = "Opening 30min"
        elif bar_time_local < time(15, 0):
            phase = "Mid-Session"
        elif bar_time_local < time(16, 0):
            phase = "Final Hour"
        else:
            phase = "Post-Cash"
        
        return PriceExtreme(
            price=bar.high_price if is_high else bar.low_price,
            timestamp=bar_time_utc,
            time_et=time_str,
            is_high=is_high,
            phase=phase,
        )
    
    def _analyze_phase(
        self,
        rth_bars: list[IntradayBarModel],
        name: str,
        start_time: time,
        end_time: time,
        session_date: date,
    ) -> Optional[SessionPhase]:
        """Analyze a specific session phase."""
        start_dt = datetime.combine(session_date, start_time, tzinfo=ET).astimezone(UTC)
        end_dt = datetime.combine(session_date, end_time, tzinfo=ET).astimezone(UTC)
        
        phase_bars = [
            b for b in rth_bars
            if start_dt <= b.timestamp < end_dt
        ]
        
        if not phase_bars:
            return None
        
        return SessionPhase(
            name=name,
            start_time=start_dt,
            end_time=end_dt,
            open_price=phase_bars[0].open_price,
            high_price=max(b.high_price for b in phase_bars),
            low_price=min(b.low_price for b in phase_bars),
            close_price=phase_bars[-1].close_price,
            volume=sum(b.volume for b in phase_bars),
            bar_count=len(phase_bars),
        )
    
    def _classify_opening_drive(
        self,
        opening_phase: SessionPhase,
        gap_points: Optional[Decimal],
    ) -> str:
        """Classify the opening 30 minutes behavior."""
        change = opening_phase.change_points
        range_pts = opening_phase.range_points
        
        # Gap and go: gap direction continues
        if gap_points is not None and abs(gap_points) > Decimal('2'):
            if gap_points > 0 and change > Decimal('2'):
                return "gap_and_go"
            elif gap_points < 0 and change < Decimal('-2'):
                return "gap_and_go"
            elif (gap_points > 0 and change < Decimal('-1')) or \
                 (gap_points < 0 and change > Decimal('1')):
                return "fade"
        
        # Trending: significant directional move
        if abs(change) > range_pts * Decimal('0.6'):
            return "trend"
        
        # Chop: range bound, no clear direction
        return "chop"
    
    def _classify_closing_action(
        self,
        final_hour: SessionPhase,
        rth_open: Decimal,
        rth_close: Decimal,
    ) -> str:
        """Classify the final hour behavior."""
        final_change = final_hour.change_points
        day_change = rth_close - rth_open
        
        # Strong close: final hour accelerated in day's direction
        if day_change > 0 and final_change > Decimal('2'):
            return "strong_close"
        elif day_change < 0 and final_change < Decimal('-2'):
            return "strong_close"
        
        # Weak close: final hour reversed day's direction
        if day_change > 0 and final_change < Decimal('-1'):
            return "weak_close"
        elif day_change < 0 and final_change > Decimal('1'):
            return "weak_close"
        
        return "neutral"
    
    def has_data_for_session(self, instrument: str, session_date: date) -> bool:
        """Check if we have intraday data stored for a session."""
        return IntradayBarModel.objects.filter(
            instrument=instrument,
            session_date=session_date,
        ).exists()
    
    def get_available_sessions(
        self,
        instrument: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[date]:
        """Get list of dates with stored intraday data."""
        queryset = IntradayBarModel.objects.filter(instrument=instrument)
        
        if start_date:
            queryset = queryset.filter(session_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(session_date__lte=end_date)
        
        return list(
            queryset.values_list('session_date', flat=True)
            .distinct()
            .order_by('session_date')
        )
