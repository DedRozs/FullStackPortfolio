"""
Management command to generate trading blog posts.

Usage:
    python manage.py generate_trading_content --instruments ES --post-types post_market
    python manage.py generate_trading_content --instruments ES NQ RTY --post-types post_market --date 2025-01-17
    python manage.py generate_trading_content --instruments ES --post-types weekly_recap --week-start 2025-01-13
    python manage.py generate_trading_content --all-instruments --post-types pre_market post_market
"""
from __future__ import annotations

from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.trading.application.content_generation.pipeline import (
    TradingContentPipeline,
    PipelineResult,
)
from apps.trading.infrastructure.repositories import (
    DjangoTradingPostRepository,
    DjangoMarketSessionRepository,
    DjangoWeeklySessionRepository,
    DjangoPriceLevelRepository,
)
from apps.shared.infrastructure.event_bus import get_event_bus
from apps.trading.domain.value_objects import Instrument, PostType


class Command(BaseCommand):
    help = 'Generate trading blog posts for specified instruments and post types'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--instruments',
            nargs='+',
            choices=['ES', 'NQ', 'RTY', 'YM'],
            help='Instruments to generate posts for (e.g., ES NQ RTY YM)',
        )
        parser.add_argument(
            '--all-instruments',
            action='store_true',
            help='Generate for all instruments (ES, NQ, RTY, YM)',
        )
        parser.add_argument(
            '--post-types',
            nargs='+',
            choices=['pre_market', 'post_market', 'weekly_recap'],
            required=True,
            help='Post types to generate',
        )
        parser.add_argument(
            '--date',
            type=str,
            help='Session date in YYYY-MM-DD format (default: today)',
        )
        parser.add_argument(
            '--week-start',
            type=str,
            help='Week start date for weekly recap (Monday) in YYYY-MM-DD format',
        )
        parser.add_argument(
            '--skip-review',
            action='store_true',
            help='Skip the multi-model review step',
        )
        parser.add_argument(
            '--publish',
            action='store_true',
            help='Automatically publish the generated posts',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Delete existing posts and regenerate (use with caution)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be generated without actually generating',
        )
    
    def handle(self, *args, **options):
        # Check for OpenAI API key
        if not settings.OPENAI_API_KEY:
            raise CommandError(
                'OPENAI_API_KEY is not configured. '
                'Please set it in your .env file.'
            )
        
        # Determine instruments
        if options['all_instruments']:
            instruments = [Instrument.ES, Instrument.NQ, Instrument.RTY, Instrument.YM]
        elif options['instruments']:
            instruments = [Instrument.from_short_name(i) for i in options['instruments']]
        else:
            raise CommandError(
                'Please specify --instruments or --all-instruments'
            )
        
        # Parse date
        if options['date']:
            try:
                session_date = date.fromisoformat(options['date'])
            except ValueError:
                raise CommandError(f"Invalid date format: {options['date']}")
        else:
            session_date = date.today()
        
        # Parse week start for weekly recap
        week_start = None
        if 'weekly_recap' in options['post_types']:
            if options['week_start']:
                try:
                    week_start = date.fromisoformat(options['week_start'])
                    # Validate it's a Monday
                    if week_start.weekday() != 0:
                        raise CommandError(
                            f"Week start must be a Monday, got {week_start.strftime('%A')}"
                        )
                except ValueError:
                    raise CommandError(f"Invalid week-start format: {options['week_start']}")
            else:
                # Default to current week's Monday
                week_start = session_date - timedelta(days=session_date.weekday())
        
        # Parse post types
        post_types = [PostType(pt) for pt in options['post_types']]
        
        # Dry run - just show what would happen
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No posts will be generated'))
            self.stdout.write(f'Instruments: {[i.short_name for i in instruments]}')
            self.stdout.write(f'Post types: {[pt.value for pt in post_types]}')
            self.stdout.write(f'Session date: {session_date}')
            if week_start:
                self.stdout.write(f'Week start: {week_start}')
            self.stdout.write(f'Skip review: {options["skip_review"]}')
            self.stdout.write(f'Auto publish: {options["publish"]}')
            self.stdout.write(f'Force regenerate: {options["force"]}')
            return
        
        # Create pipeline with all dependencies
        try:
            pipeline = TradingContentPipeline(
                post_repository=DjangoTradingPostRepository(),
                session_repository=DjangoMarketSessionRepository(),
                weekly_repository=DjangoWeeklySessionRepository(),
                level_repository=DjangoPriceLevelRepository(),
                event_bus=get_event_bus(),
                skip_review=options['skip_review'],
            )
        except Exception as e:
            raise CommandError(f'Failed to initialize pipeline: {e}')
        
        self.stdout.write(
            f'Generating {len(instruments)} instrument(s) × {len(post_types)} post type(s)...'
        )
        
        # Handle --force: delete existing posts before regenerating
        if options['force']:
            self.stdout.write(self.style.WARNING('FORCE mode: Deleting existing posts...'))
            from apps.trading.infrastructure.models import TradingPostModel
            
            for pt in post_types:
                for inst in instruments:
                    if pt == PostType.WEEKLY_RECAP:
                        # For weekly recap, use week_start
                        target_date = week_start if week_start else session_date
                        deleted, _ = TradingPostModel.objects.filter(
                            instrument=inst.value,
                            post_type=pt.value,
                            session_date=target_date,
                        ).delete()
                    else:
                        deleted, _ = TradingPostModel.objects.filter(
                            instrument=inst.value,
                            post_type=pt.value,
                            session_date=session_date,
                        ).delete()
                    
                    if deleted:
                        self.stdout.write(f'  Deleted {deleted} existing {inst.short_name} {pt.value} post(s)')
        
        # Execute for each post type
        results: list[PipelineResult] = []
        auto_publish = options['publish']
        
        try:
            for pt in post_types:
                if pt == PostType.PRE_MARKET:
                    results.extend(
                        pipeline.generate_premarket_posts(
                            session_date=session_date,
                            instruments=instruments,
                            auto_publish=auto_publish,
                        )
                    )
                elif pt == PostType.POST_MARKET:
                    results.extend(
                        pipeline.generate_postmarket_posts(
                            session_date=session_date,
                            instruments=instruments,
                            auto_publish=auto_publish,
                        )
                    )
                elif pt == PostType.WEEKLY_RECAP:
                    if not week_start:
                        week_start = session_date - timedelta(days=session_date.weekday())
                    results.extend(
                        pipeline.generate_weekly_recaps(
                            week_start_date=week_start,
                            instruments=instruments,
                            auto_publish=auto_publish,
                        )
                    )
        except Exception as e:
            raise CommandError(f'Pipeline failed: {e}')
        
        # Report results
        success_count = sum(1 for r in results if r.success)
        fail_count = len(results) - success_count
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'=== Generation Complete ==='))
        self.stdout.write(f'Successful: {success_count}')
        self.stdout.write(f'Failed: {fail_count}')
        
        for result in results:
            if result.success:
                status = 'PUBLISHED' if result.published else 'DRAFT'
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ {result.instrument.short_name} {result.post_type.value}: '
                    f'{result.title[:50]}... [{status}]'
                ))
                if result.reviewed:
                    self.stdout.write(f'    Review score: {result.review_quality_score:.1f}/10')
            else:
                self.stdout.write(self.style.ERROR(
                    f'  ✗ {result.instrument.short_name} {result.post_type.value}: '
                    f'{result.error_message}'
                ))
