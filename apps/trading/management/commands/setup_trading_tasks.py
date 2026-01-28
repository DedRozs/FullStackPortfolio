"""
Management command to set up scheduled tasks for trading content generation.

This command is run during deployment to ensure the trading task schedule is populated.
It's idempotent - running it multiple times won't create duplicate schedules.

Trading Post Schedule (all times Eastern / New York):
- 5:30 PM ET: Fetch intraday bars from Databento (after 5:00 PM settlement)
- 6:00 PM ET: Generate post-market recaps for all instruments
- 6:30 AM ET: Generate pre-market briefings for all instruments
- 9:00 AM ET Saturday: Generate weekly recaps

Note: CME equity index futures trade Sunday 6 PM - Friday 5 PM ET.
      RTH (Regular Trading Hours) is 9:30 AM - 4:00 PM ET.
      Settlement is at 5:00 PM ET.
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Set up scheduled tasks for automated trading content generation'
    
    # Define all scheduled tasks
    # Using CRON for precise scheduling: minute hour day-of-month month day-of-week
    # Times are in UTC. Eastern Time = UTC-5 (EST) or UTC-4 (EDT)
    # Using America/New_York timezone in the schedule
    SCHEDULED_TASKS = [
        {
            'name': 'fetch_trading_intraday_bars',
            'func': 'apps.trading.application.content_generation.tasks.fetch_daily_intraday_bars',
            'schedule_type': Schedule.CRON,
            # 5:30 PM ET Monday-Friday (22:30 UTC during EST, 21:30 during EDT)
            # Using 22:30 UTC which covers most of the year adequately
            'cron': '30 22 * * 1-5',
            'repeats': -1,
        },
        {
            'name': 'generate_trading_postmarket',
            'func': 'apps.trading.application.content_generation.tasks.generate_postmarket_posts',
            'schedule_type': Schedule.CRON,
            # 6:00 PM ET Monday-Friday (23:00 UTC during EST)
            'cron': '0 23 * * 1-5',
            'repeats': -1,
        },
        {
            'name': 'generate_trading_premarket',
            'func': 'apps.trading.application.content_generation.tasks.generate_premarket_posts',
            'schedule_type': Schedule.CRON,
            # 6:30 AM ET Monday-Friday (11:30 UTC during EST)
            'cron': '30 11 * * 1-5',
            'repeats': -1,
        },
        {
            'name': 'generate_trading_weekly_recap',
            'func': 'apps.trading.application.content_generation.tasks.generate_weekly_recaps',
            'schedule_type': Schedule.CRON,
            # 9:00 AM ET Saturday (14:00 UTC during EST)
            'cron': '0 14 * * 6',
            'repeats': -1,
        },
        {
            'name': 'trading_health_check',
            'func': 'apps.trading.application.content_generation.tasks.trading_health_check',
            'schedule_type': Schedule.CRON,
            # Daily at 7:00 AM ET (12:00 UTC during EST)
            'cron': '0 12 * * *',
            'repeats': -1,
        },
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing trading schedules before creating new ones',
        )
        parser.add_argument(
            '--clear-all',
            action='store_true',
            help='Clear ALL schedules (including blog schedules) before creating',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            dest='list_schedules',
            help='List all current schedules',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if options['list_schedules']:
            self._list_schedules()
            return
        
        if options['clear_all']:
            if dry_run:
                self.stdout.write('Would delete all existing schedules')
            else:
                deleted_count = Schedule.objects.all().delete()[0]
                self.stdout.write(
                    self.style.WARNING(f'Deleted {deleted_count} existing schedules')
                )
        elif options['clear']:
            if dry_run:
                self.stdout.write('Would delete trading schedules only')
            else:
                # Only delete trading-related schedules
                trading_names = [t['name'] for t in self.SCHEDULED_TASKS]
                deleted_count = Schedule.objects.filter(name__in=trading_names).delete()[0]
                self.stdout.write(
                    self.style.WARNING(f'Deleted {deleted_count} trading schedules')
                )
        
        created = 0
        updated = 0
        
        for task in self.SCHEDULED_TASKS:
            name = task['name']
            
            # Check if schedule already exists
            existing = Schedule.objects.filter(name=name).first()
            
            if existing:
                if dry_run:
                    self.stdout.write(f'Would update: {name}')
                else:
                    # Update existing schedule
                    existing.func = task['func']
                    existing.schedule_type = task['schedule_type']
                    existing.cron = task['cron']
                    existing.repeats = task['repeats']
                    existing.save()
                    self.stdout.write(f'Updated: {name}')
                updated += 1
            else:
                if dry_run:
                    self.stdout.write(f'Would create: {name} ({task["cron"]})')
                else:
                    # Create new schedule
                    Schedule.objects.create(
                        name=name,
                        func=task['func'],
                        schedule_type=task['schedule_type'],
                        cron=task['cron'],
                        repeats=task['repeats'],
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created: {name}'))
                created += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nDry run complete. Would create {created}, update {updated} schedules.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSetup complete. Created {created}, updated {updated} schedules.'
                )
            )
        
        self.stdout.write('\nTrading Schedule Summary (times in UTC):')
        self._print_schedule_summary()
    
    def _list_schedules(self):
        """List all current schedules."""
        schedules = Schedule.objects.all().order_by('name')
        
        if not schedules:
            self.stdout.write('No schedules configured.')
            return
        
        self.stdout.write(f'\nCurrent Schedules ({schedules.count()} total):')
        self.stdout.write('-' * 70)
        
        for s in schedules:
            status = '✓ Active' if s.repeats != 0 else '✗ Inactive'
            cron = s.cron if s.cron else 'N/A'
            self.stdout.write(f'{s.name}')
            self.stdout.write(f'  Function: {s.func}')
            self.stdout.write(f'  Cron: {cron}')
            self.stdout.write(f'  Status: {status}')
            self.stdout.write('')
    
    def _print_schedule_summary(self):
        """Print a human-readable schedule summary."""
        schedule_info = [
            ('fetch_trading_intraday_bars', '22:30 UTC (5:30 PM ET)', 'Mon-Fri'),
            ('generate_trading_postmarket', '23:00 UTC (6:00 PM ET)', 'Mon-Fri'),
            ('generate_trading_premarket', '11:30 UTC (6:30 AM ET)', 'Mon-Fri'),
            ('generate_trading_weekly_recap', '14:00 UTC (9:00 AM ET)', 'Saturday'),
            ('trading_health_check', '12:00 UTC (7:00 AM ET)', 'Daily'),
        ]
        
        for name, time, days in schedule_info:
            self.stdout.write(f'  • {name}: {time} ({days})')
