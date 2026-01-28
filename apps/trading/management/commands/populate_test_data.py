"""Populate database with market data for testing.

This command fetches intraday bar data from Databento for the specified
date range, enabling local testing of the content generation pipeline.

Usage:
    # Populate last 2 weeks for all instruments
    python manage.py populate_test_data
    
    # Populate specific date range
    python manage.py populate_test_data --start 2026-01-19 --end 2026-01-28
    
    # Populate only ES
    python manage.py populate_test_data --instruments ES
"""
import logging
from datetime import date, timedelta
from typing import List

from django.core.management.base import BaseCommand, CommandError

from apps.trading.domain.value_objects import Instrument
from apps.trading.infrastructure.market_data.sync_service import (
    MarketDataSyncService,
    DataFetchError,
)
from apps.trading.infrastructure.models import IntradayBarModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate database with market data from Databento for testing"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--start',
            type=str,
            help='Start date (YYYY-MM-DD). Default: 2 weeks ago',
        )
        parser.add_argument(
            '--end',
            type=str,
            help='End date (YYYY-MM-DD). Default: today',
        )
        parser.add_argument(
            '--instruments',
            type=str,
            nargs='+',
            default=['ES', 'NQ'],
            help='Instruments to fetch (ES, NQ). Default: ES NQ',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-fetch even if local data exists',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fetched without actually fetching',
        )
    
    def handle(self, *args, **options):
        # Parse dates
        today = date.today()
        
        if options['start']:
            start_date = date.fromisoformat(options['start'])
        else:
            # Default: 2 weeks ago (Monday of 2 weeks ago)
            two_weeks_ago = today - timedelta(days=14)
            # Find the Monday
            start_date = two_weeks_ago - timedelta(days=two_weeks_ago.weekday())
        
        if options['end']:
            end_date = date.fromisoformat(options['end'])
        else:
            end_date = today
        
        # Don't fetch future dates
        if end_date > today:
            end_date = today
        
        # Parse instruments
        instrument_map = {
            'ES': Instrument.ES,
            'NQ': Instrument.NQ,
        }
        
        instruments: List[Instrument] = []
        for name in options['instruments']:
            name_upper = name.upper()
            if name_upper not in instrument_map:
                raise CommandError(f"Unknown instrument: {name}. Valid: ES, NQ")
            instruments.append(instrument_map[name_upper])
        
        self.stdout.write(
            f"\n{'='*60}\n"
            f"Market Data Population\n"
            f"{'='*60}\n"
            f"Date Range: {start_date} to {end_date}\n"
            f"Instruments: {', '.join(i.short_name for i in instruments)}\n"
            f"Force Re-fetch: {options['force']}\n"
            f"Dry Run: {options['dry_run']}\n"
            f"{'='*60}\n"
        )
        
        # Create sync service
        sync_service = MarketDataSyncService()
        
        # Generate list of trading days
        trading_days = []
        current = start_date
        while current <= end_date:
            # Skip weekends
            if current.weekday() < 5:  # Mon-Fri
                trading_days.append(current)
            current += timedelta(days=1)
        
        self.stdout.write(f"Trading days to process: {len(trading_days)}\n")
        
        # Track results
        fetched = 0
        skipped = 0
        failed = 0
        
        for instrument in instruments:
            self.stdout.write(f"\n{instrument.display_name} ({instrument.short_name}):\n")
            
            for session_date in trading_days:
                # Check if data exists
                has_data = sync_service.has_local_data(instrument, session_date)
                bar_count = IntradayBarModel.objects.filter(
                    instrument=instrument.value,
                    session_date=session_date,
                ).count()
                
                if has_data and not options['force']:
                    self.stdout.write(
                        f"  {session_date}: " 
                        f"{self.style.SUCCESS('EXISTS')} ({bar_count} bars)"
                    )
                    skipped += 1
                    continue
                
                if options['dry_run']:
                    self.stdout.write(
                        f"  {session_date}: "
                        f"{self.style.WARNING('WOULD FETCH')} (current: {bar_count} bars)"
                    )
                    continue
                
                # Delete existing if force
                if options['force'] and bar_count > 0:
                    IntradayBarModel.objects.filter(
                        instrument=instrument.value,
                        session_date=session_date,
                    ).delete()
                    self.stdout.write(
                        f"  {session_date}: Deleted {bar_count} existing bars..."
                    )
                
                # Fetch from Databento
                try:
                    success = sync_service.ensure_session_data(
                        instrument=instrument,
                        session_date=session_date,
                        include_overnight=True,
                    )
                    
                    if success:
                        new_count = IntradayBarModel.objects.filter(
                            instrument=instrument.value,
                            session_date=session_date,
                        ).count()
                        self.stdout.write(
                            f"  {session_date}: "
                            f"{self.style.SUCCESS('FETCHED')} ({new_count} bars)"
                        )
                        fetched += 1
                    else:
                        self.stdout.write(
                            f"  {session_date}: "
                            f"{self.style.ERROR('FAILED')} (no data returned)"
                        )
                        failed += 1
                        
                except DataFetchError as e:
                    self.stdout.write(
                        f"  {session_date}: "
                        f"{self.style.ERROR('ERROR')}: {e}"
                    )
                    failed += 1
                except Exception as e:
                    self.stdout.write(
                        f"  {session_date}: "
                        f"{self.style.ERROR('ERROR')}: {type(e).__name__}: {e}"
                    )
                    failed += 1
        
        # Summary
        self.stdout.write(
            f"\n{'='*60}\n"
            f"Summary\n"
            f"{'='*60}\n"
            f"Fetched: {fetched}\n"
            f"Skipped (already exists): {skipped}\n"
            f"Failed: {failed}\n"
            f"{'='*60}\n"
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("\nDry run - no data was actually fetched.\n")
            )
