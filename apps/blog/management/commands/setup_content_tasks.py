"""
Management command to set up scheduled tasks for content generation.

This command is run during deployment to ensure the task schedule is populated.
It's idempotent - running it multiple times won't create duplicate schedules.

Blog Post Schedule: 1 post daily at 10 AM MST (5 PM UTC)
- Daily 6 AM MST (1 PM UTC): Generate 2-3 fresh topic ideas (builds backlog)
- Daily 10 AM MST (5 PM UTC): Publish one blog post from the backlog
"""
from django.core.management.base import BaseCommand
from django_q.models import Schedule


class Command(BaseCommand):
    help = 'Set up scheduled tasks for automated content generation'
    
    # Define all scheduled tasks
    # Using CRON for precise scheduling: minute hour day-of-month month day-of-week
    # MST = UTC-7, so 10 AM MST = 17:00 UTC, 6 AM MST = 13:00 UTC
    SCHEDULED_TASKS = [
        {
            'name': 'generate_daily_ideas',
            'func': 'apps.blog.application.content_generation.tasks.generate_daily_ideas',
            'schedule_type': Schedule.CRON,
            'cron': '0 13 * * *',  # Daily at 1 PM UTC (6 AM MST)
            'repeats': -1,
        },
        {
            'name': 'publish_daily_blog',
            'func': 'apps.blog.application.content_generation.tasks.process_pending_idea',
            'schedule_type': Schedule.CRON,
            'cron': '0 17 * * *',  # Daily at 5 PM UTC (10 AM MST)
            'repeats': -1,
        },
        {
            'name': 'cleanup_old_ideas',
            'func': 'apps.blog.application.content_generation.tasks.cleanup_old_ideas',
            'schedule_type': Schedule.CRON,
            'cron': '0 10 * * 0',  # Every Sunday at 3 AM MST (10 AM UTC)
            'repeats': -1,
        },
        {
            'name': 'content_pipeline_health_check',
            'func': 'apps.blog.application.content_generation.tasks.health_check',
            'schedule_type': Schedule.CRON,
            'cron': '0 7 * * *',  # Daily at midnight MST (7 AM UTC)
            'repeats': -1,
        },
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing schedules before creating new ones',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if options['clear']:
            if dry_run:
                self.stdout.write('Would delete all existing schedules')
            else:
                deleted_count = Schedule.objects.all().delete()[0]
                self.stdout.write(self.style.WARNING(f'Deleted {deleted_count} existing schedules'))
        
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
                    existing.minutes = task.get('minutes', 0)
                    existing.repeats = task.get('repeats', -1)
                    existing.save()
                    self.stdout.write(f'Updated: {name}')
                updated += 1
            else:
                if dry_run:
                    self.stdout.write(f'Would create: {name}')
                else:
                    # Create new schedule
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Calculate next run time
                    next_run = timezone.now()
                    if 'next_run_hour' in task:
                        next_run = next_run.replace(
                            hour=task['next_run_hour'],
                            minute=task.get('next_run_minute', 0),
                            second=0,
                            microsecond=0
                        )
                        # If the time has passed today, schedule for tomorrow
                        if next_run <= timezone.now():
                            next_run += timedelta(days=1)
                    
                    Schedule.objects.create(
                        name=name,
                        func=task['func'],
                        schedule_type=task['schedule_type'],
                        minutes=task.get('minutes', 0),
                        repeats=task.get('repeats', -1),
                        next_run=next_run,
                    )
                    self.stdout.write(self.style.SUCCESS(f'Created: {name}'))
                created += 1
        
        # Summary
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\nDry run complete. Would create {created}, update {updated} schedules.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nSetup complete. Created {created}, updated {updated} schedules.'
            ))
            
            # Show current schedules
            self.stdout.write('\nCurrent schedules:')
            for schedule in Schedule.objects.all():
                self.stdout.write(f'  - {schedule.name}: {schedule.schedule_type} (next: {schedule.next_run})')
