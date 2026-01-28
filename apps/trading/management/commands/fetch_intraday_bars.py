"""Management command to fetch and store intraday bar data from Databento.

This command fetches 1-minute OHLCV bars for the previous trading day
and stores them in the database. Designed to be run daily via cron/task scheduler.

Usage:
    # Fetch yesterday's data for all instruments
    python manage.py fetch_intraday_bars
    
    # Fetch specific date
    python manage.py fetch_intraday_bars --date 2026-01-27
    
    # Fetch specific instruments only
    python manage.py fetch_intraday_bars --instruments ES NQ
    
    # Estimate cost without fetching
    python manage.py fetch_intraday_bars --dry-run
    
    # Backfill a date range
    python manage.py fetch_intraday_bars --start-date 2026-01-20 --end-date 2026-01-27
"""
import logging
from datetime import date, timedelta
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.trading.infrastructure.market_data.databento_client import DatabentoClient
from apps.trading.infrastructure.models import IntradayBarModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch intraday bar data from Databento and store in database'
    
    # Default instruments to fetch
    DEFAULT_INSTRUMENTS = ['ES=F', 'NQ=F', 'RTY=F', 'YM=F']
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to fetch (YYYY-MM-DD). Defaults to yesterday.',
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date for backfill range (YYYY-MM-DD).',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date for backfill range (YYYY-MM-DD).',
        )
        parser.add_argument(
            '--instruments',
            nargs='+',
            type=str,
            help='Instruments to fetch (e.g., ES NQ RTY). Defaults to all.',
        )
        parser.add_argument(
            '--include-overnight',
            action='store_true',
            default=True,
            help='Include overnight session data (default: True).',
        )
        parser.add_argument(
            '--skip-overnight',
            action='store_true',
            default=False,
            help='Skip overnight session, fetch RTH only.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Estimate cost without fetching data.',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-fetch even if data already exists for the date.',
        )
    
    def handle(self, *args, **options):
        client = DatabentoClient()
        
        if not client.api_key:
            raise CommandError(
                "Databento API key not configured. "
                "Set DATABENTO_API_KEY environment variable."
            )
        
        # Determine date range
        dates_to_fetch = self._get_dates_to_fetch(options)
        
        if not dates_to_fetch:
            self.stdout.write(self.style.WARNING("No dates to fetch."))
            return
        
        # Determine instruments
        instrument_args = options.get('instruments')
        if instrument_args:
            # Convert shorthand to Yahoo symbols
            instruments = []
            for i in instrument_args:
                if '=' not in i:
                    instruments.append(f"{i}=F")
                else:
                    instruments.append(i)
        else:
            instruments = self.DEFAULT_INSTRUMENTS
        
        include_overnight = not options.get('skip_overnight', False)
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)
        
        self.stdout.write(
            f"{'[DRY RUN] ' if dry_run else ''}"
            f"Fetching {len(instruments)} instruments for {len(dates_to_fetch)} dates"
        )
        self.stdout.write(f"  Instruments: {', '.join(instruments)}")
        self.stdout.write(f"  Dates: {dates_to_fetch[0]} to {dates_to_fetch[-1]}")
        self.stdout.write(f"  Include overnight: {include_overnight}")
        
        total_cost = 0.0
        total_bars = 0
        
        for session_date in dates_to_fetch:
            for instrument in instruments:
                # Check if we already have data
                if not force:
                    existing_count = IntradayBarModel.objects.filter(
                        instrument=instrument,
                        session_date=session_date,
                    ).count()
                    
                    if existing_count > 0:
                        self.stdout.write(
                            f"  Skipping {instrument} {session_date}: "
                            f"{existing_count} bars already exist"
                        )
                        continue
                
                if dry_run:
                    # Just estimate cost
                    cost = client.estimate_cost(
                        instrument=instrument,
                        session_date=session_date,
                        include_overnight=include_overnight,
                    )
                    if cost is not None:
                        total_cost += cost
                        self.stdout.write(
                            f"  {instrument} {session_date}: ~${cost:.4f}"
                        )
                    else:
                        self.stdout.write(
                            f"  {instrument} {session_date}: Unable to estimate"
                        )
                else:
                    # Actually fetch and store
                    bars_stored = self._fetch_and_store(
                        client=client,
                        instrument=instrument,
                        session_date=session_date,
                        include_overnight=include_overnight,
                        force=force,
                    )
                    total_bars += bars_stored
        
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"\nEstimated total cost: ${total_cost:.4f}")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\nStored {total_bars} bars total")
            )
    
    def _get_dates_to_fetch(self, options) -> list[date]:
        """Determine which dates to fetch based on command options."""
        if options.get('date'):
            # Single date specified
            try:
                d = date.fromisoformat(options['date'])
                return [d]
            except ValueError as e:
                raise CommandError(f"Invalid date format: {e}")
        
        if options.get('start_date') or options.get('end_date'):
            # Date range specified
            try:
                start = date.fromisoformat(options['start_date']) if options.get('start_date') else date.today() - timedelta(days=7)
                end = date.fromisoformat(options['end_date']) if options.get('end_date') else date.today() - timedelta(days=1)
            except ValueError as e:
                raise CommandError(f"Invalid date format: {e}")
            
            if start > end:
                raise CommandError("Start date must be before end date")
            
            # Generate all weekdays in range
            dates = []
            current = start
            while current <= end:
                # Skip weekends (Saturday=5, Sunday=6)
                if current.weekday() < 5:
                    dates.append(current)
                current += timedelta(days=1)
            
            return dates
        
        # Default: yesterday (if weekday) or last Friday
        yesterday = date.today() - timedelta(days=1)
        
        # If yesterday was Sunday, go back to Friday
        if yesterday.weekday() == 6:  # Sunday
            yesterday = yesterday - timedelta(days=2)
        elif yesterday.weekday() == 5:  # Saturday
            yesterday = yesterday - timedelta(days=1)
        
        return [yesterday]
    
    def _fetch_and_store(
        self,
        client: DatabentoClient,
        instrument: str,
        session_date: date,
        include_overnight: bool,
        force: bool,
    ) -> int:
        """Fetch bars from Databento and store in database.
        
        Returns:
            Number of bars stored
        """
        self.stdout.write(f"  Fetching {instrument} {session_date}...")
        
        bars = client.fetch_session_bars(
            instrument=instrument,
            session_date=session_date,
            include_overnight=include_overnight,
        )
        
        if not bars:
            self.stdout.write(
                self.style.WARNING(f"    No data returned for {instrument} {session_date}")
            )
            return 0
        
        # Delete existing if force
        if force:
            deleted, _ = IntradayBarModel.objects.filter(
                instrument=instrument,
                session_date=session_date,
            ).delete()
            if deleted:
                self.stdout.write(f"    Deleted {deleted} existing bars")
        
        # Bulk create
        bar_models = [
            IntradayBarModel(
                instrument=instrument,
                timestamp=bar.timestamp,
                open_price=bar.open_price,
                high_price=bar.high_price,
                low_price=bar.low_price,
                close_price=bar.close_price,
                volume=bar.volume,
                session_date=bar.session_date,
                session_type=bar.session_type,
            )
            for bar in bars
        ]
        
        with transaction.atomic():
            IntradayBarModel.objects.bulk_create(
                bar_models,
                ignore_conflicts=True,  # Skip duplicates
            )
        
        self.stdout.write(
            self.style.SUCCESS(f"    Stored {len(bars)} bars for {instrument} {session_date}")
        )
        
        return len(bars)
