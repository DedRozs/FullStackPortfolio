"""Management command to check and ensure data availability before content generation.

This command verifies that all required intraday bar data is present in the database
before attempting to generate trading posts. It can optionally fetch missing data.

Usage:
    # Check data availability for today
    python manage.py ensure_trading_data
    
    # Check and fetch missing data
    python manage.py ensure_trading_data --fetch-missing
    
    # Check specific date and instruments
    python manage.py ensure_trading_data --date 2026-01-27 --instruments ES NQ
    
    # Check for weekly recap (needs full week of data)
    python manage.py ensure_trading_data --week-start 2026-01-20
"""
import logging
from datetime import date, timedelta
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from apps.trading.infrastructure.market_data.local_market_data import LocalMarketDataService
from apps.trading.domain.value_objects import Instrument

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and ensure trading data is available before content generation'
    
    DEFAULT_INSTRUMENTS = ['ES', 'NQ', 'RTY', 'YM']
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Session date to check (YYYY-MM-DD). Defaults to yesterday.',
        )
        parser.add_argument(
            '--week-start',
            type=str,
            help='Week start (Monday) for weekly recap data check.',
        )
        parser.add_argument(
            '--instruments',
            nargs='+',
            choices=['ES', 'NQ', 'RTY', 'YM'],
            help='Instruments to check (default: all)',
        )
        parser.add_argument(
            '--fetch-missing',
            action='store_true',
            help='Automatically fetch missing data from Databento',
        )
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='Show detailed information about data status',
        )
    
    def handle(self, *args, **options):
        service = LocalMarketDataService()
        show_details = options.get('show_details', False) or options.get('verbosity', 1) > 1
        
        # Determine date(s) to check
        if options.get('week_start'):
            try:
                week_start = date.fromisoformat(options['week_start'])
                if week_start.weekday() != 0:
                    raise CommandError(
                        f"Week start must be a Monday, got {week_start.strftime('%A')}"
                    )
                # Check all 5 trading days
                dates_to_check = [week_start + timedelta(days=i) for i in range(5)]
            except ValueError as e:
                raise CommandError(f"Invalid date format: {e}")
        elif options.get('date'):
            try:
                dates_to_check = [date.fromisoformat(options['date'])]
            except ValueError as e:
                raise CommandError(f"Invalid date format: {e}")
        else:
            # Default to yesterday
            dates_to_check = [date.today() - timedelta(days=1)]
        
        # Determine instruments
        if options.get('instruments'):
            instruments = [Instrument.from_short_name(i) for i in options['instruments']]
        else:
            instruments = [Instrument.from_short_name(i) for i in self.DEFAULT_INSTRUMENTS]
        
        show_details = options.get('show_details', False) or options.get('verbosity', 1) > 1
        fetch_missing = options.get('fetch_missing', False)
        
        self.stdout.write(f"Checking data for {len(instruments)} instruments over {len(dates_to_check)} date(s)")
        self.stdout.write(f"  Instruments: {[i.short_name for i in instruments]}")
        self.stdout.write(f"  Dates: {dates_to_check[0]} to {dates_to_check[-1]}")
        self.stdout.write("")
        
        missing_data: List[tuple] = []  # (instrument, date)
        
        for session_date in dates_to_check:
            # Skip weekends
            if session_date.weekday() >= 5:
                if show_details:
                    self.stdout.write(f"  {session_date}: Weekend - skipped")
                continue
            
            for instrument in instruments:
                bar_counts = service.get_bar_count(instrument, session_date)
                has_rth = bar_counts['rth'] > 0
                has_overnight = bar_counts['overnight'] > 0
                
                if has_rth:
                    status = self.style.SUCCESS("✓ Ready")
                    details = f"RTH: {bar_counts['rth']} bars"
                    if has_overnight:
                        details += f", Overnight: {bar_counts['overnight']} bars"
                    
                    if show_details:
                        # Also check data integrity
                        validation = service.validate_data_integrity(instrument, session_date)
                        if not validation['valid']:
                            status = self.style.WARNING("⚠ Issues")
                            details += f" | Issues: {', '.join(validation['issues'])}"
                else:
                    status = self.style.ERROR("✗ Missing")
                    details = "No RTH data"
                    missing_data.append((instrument, session_date))
                
                if show_details or not has_rth:
                    self.stdout.write(
                        f"  {session_date} {instrument.short_name}: {status} ({details})"
                    )
        
        self.stdout.write("")
        
        if not missing_data:
            self.stdout.write(self.style.SUCCESS("All data is available!"))
            return
        
        # Report missing data
        self.stdout.write(self.style.WARNING(f"Missing data for {len(missing_data)} instrument-date combinations:"))
        
        # Group by date for more efficient fetch commands
        dates_by_instrument = {}
        for instrument, session_date in missing_data:
            short = instrument.value.replace('=F', '')
            if short not in dates_by_instrument:
                dates_by_instrument[short] = set()
            dates_by_instrument[short].add(session_date)
        
        for short_name, dates in dates_by_instrument.items():
            sorted_dates = sorted(dates)
            if len(sorted_dates) == 1:
                cmd = f"python manage.py fetch_intraday_bars --date {sorted_dates[0]} --instruments {short_name}"
            else:
                cmd = f"python manage.py fetch_intraday_bars --start-date {sorted_dates[0]} --end-date {sorted_dates[-1]} --instruments {short_name}"
            self.stdout.write(f"  {cmd}")
        
        if fetch_missing:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("Fetching missing data from Databento..."))
            
            # Collect all dates and instruments to fetch
            all_missing_dates = set()
            all_missing_instruments = set()
            for instrument, session_date in missing_data:
                all_missing_dates.add(session_date)
                all_missing_instruments.add(instrument.value.replace('=F', ''))
            
            sorted_dates = sorted(all_missing_dates)
            
            try:
                if len(sorted_dates) == 1:
                    call_command(
                        'fetch_intraday_bars',
                        date=sorted_dates[0].isoformat(),
                        instruments=list(all_missing_instruments),
                    )
                else:
                    call_command(
                        'fetch_intraday_bars',
                        start_date=sorted_dates[0].isoformat(),
                        end_date=sorted_dates[-1].isoformat(),
                        instruments=list(all_missing_instruments),
                    )
                
                self.stdout.write(self.style.SUCCESS("Data fetch completed!"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fetch failed: {e}"))
                raise CommandError(f"Failed to fetch data: {e}")
        else:
            self.stdout.write("")
            self.stdout.write("Run with --fetch-missing to automatically fetch the missing data.")
