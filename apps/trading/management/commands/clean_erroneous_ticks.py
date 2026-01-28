"""Clean erroneous tick data from the database.

This command applies tick validation to existing intraday bars and removes
any that fail validation. Use this after importing data from Databento
to clean any bad ticks that may have been stored.

Usage:
    # Dry run - show what would be deleted
    python manage.py clean_erroneous_ticks --dry-run
    
    # Actually delete bad ticks
    python manage.py clean_erroneous_ticks
    
    # Clean only specific instrument
    python manage.py clean_erroneous_ticks --instruments ES
"""
import logging
from typing import List

from django.core.management.base import BaseCommand, CommandError

from apps.trading.domain.value_objects import Instrument
from apps.trading.domain.tick_validation import create_tick_validator
from apps.trading.infrastructure.models import IntradayBarModel

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Clean erroneous tick data from the database"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--instruments',
            type=str,
            nargs='+',
            default=['ES', 'NQ'],
            help='Instruments to clean (ES, NQ). Default: ES NQ',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
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
            f"Erroneous Tick Cleanup\n"
            f"{'='*60}\n"
            f"Instruments: {', '.join(i.short_name for i in instruments)}\n"
            f"Dry Run: {options['dry_run']}\n"
            f"{'='*60}\n"
        )
        
        total_deleted = 0
        
        for instrument in instruments:
            self.stdout.write(f"\n{instrument.display_name} ({instrument.value}):\n")
            
            # Get all bars for this instrument
            bars = list(IntradayBarModel.objects.filter(
                instrument=instrument.value,
            ).order_by('session_date', 'timestamp'))
            
            if not bars:
                self.stdout.write(f"  No bars found.\n")
                continue
            
            self.stdout.write(f"  Total bars: {len(bars):,}\n")
            
            # Create validator and filter (uses DB reference for dynamic bounds)
            validator = create_tick_validator(instrument.value, use_db_reference=True)
            valid_bars = validator.filter_bars(bars, log_filtered=False)
            
            # Find bars to delete (those not in valid set)
            valid_ids = {b.id for b in valid_bars}
            bad_bars = [b for b in bars if b.id not in valid_ids]
            
            if not bad_bars:
                self.stdout.write(
                    f"  {self.style.SUCCESS('All bars valid')} - nothing to clean\n"
                )
                continue
            
            self.stdout.write(
                f"  {self.style.WARNING(f'Found {len(bad_bars)} erroneous bars')}\n"
            )
            
            # Show sample of bad bars
            for bar in bad_bars[:5]:
                self.stdout.write(
                    f"    - {bar.session_date} {bar.timestamp.strftime('%H:%M')}: "
                    f"O={bar.open_price} H={bar.high_price} L={bar.low_price} C={bar.close_price}\n"
                )
            if len(bad_bars) > 5:
                self.stdout.write(f"    ... and {len(bad_bars) - 5} more\n")
            
            if options['dry_run']:
                self.stdout.write(
                    f"  {self.style.WARNING('DRY RUN')} - would delete {len(bad_bars)} bars\n"
                )
            else:
                # Actually delete
                bad_ids = [b.id for b in bad_bars]
                deleted_count, _ = IntradayBarModel.objects.filter(id__in=bad_ids).delete()
                total_deleted += deleted_count
                self.stdout.write(
                    f"  {self.style.SUCCESS(f'Deleted {deleted_count} bars')}\n"
                )
        
        # Summary
        self.stdout.write(
            f"\n{'='*60}\n"
            f"Summary\n"
            f"{'='*60}\n"
        )
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("Dry run - no data was actually deleted.\n")
            )
        else:
            self.stdout.write(f"Total deleted: {total_deleted:,} bars\n")
