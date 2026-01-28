"""
Management command to manually trigger the content generation pipeline.

Usage:
    python manage.py generate_content --ideas       # Generate new ideas only
    python manage.py generate_content --process     # Process one pending idea
    python manage.py generate_content --full        # Generate ideas and process one
    python manage.py generate_content --count 5     # Generate 5 ideas
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from apps.blog.application.content_generation.pipeline import ContentPipeline
from apps.blog.application.content_generation.idea_generator import IdeaGeneratorService
from apps.blog.infrastructure.repositories import (
    DjangoBlogPostRepository,
    DjangoBlogIdeaRepository,
    DjangoContentGenerationLogRepository,
)
from apps.blog.domain.entities import IdeaStatus


class Command(BaseCommand):
    help = 'Manually trigger the AI content generation pipeline'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--ideas',
            action='store_true',
            help='Generate new blog post ideas only',
        )
        parser.add_argument(
            '--process',
            action='store_true',
            help='Process one pending idea through the full pipeline',
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Generate ideas and process one through the pipeline',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=3,
            help='Number of ideas to generate (default: 3)',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all pending ideas',
        )
    
    def handle(self, *args, **options):
        # Check for OpenAI API key
        if not settings.OPENAI_API_KEY:
            raise CommandError(
                'OPENAI_API_KEY is not configured. '
                'Please set it in your .env file.'
            )
        
        idea_repo = DjangoBlogIdeaRepository()
        
        # Handle list command
        if options['list']:
            self._list_pending_ideas(idea_repo)
            return
        
        # Create pipeline
        pipeline = ContentPipeline(
            idea_repository=idea_repo,
            post_repository=DjangoBlogPostRepository(),
            log_repository=DjangoContentGenerationLogRepository(),
            openai_api_key=settings.OPENAI_API_KEY,
        )
        
        # Determine what to do
        if options['ideas']:
            self._generate_ideas(pipeline, options['count'])
        elif options['process']:
            self._process_idea(pipeline)
        elif options['full']:
            self._generate_ideas(pipeline, options['count'])
            self._process_idea(pipeline)
        else:
            self.stdout.write(self.style.WARNING(
                'No action specified. Use --ideas, --process, --full, or --list'
            ))
            self.stdout.write('Run with --help for more information.')
    
    def _list_pending_ideas(self, idea_repo):
        """List all pending ideas."""
        pending = idea_repo.find_by_status(IdeaStatus.PENDING)
        
        if not pending:
            self.stdout.write(self.style.WARNING('No pending ideas found.'))
            return
        
        self.stdout.write(f'Found {len(pending)} pending ideas:\n')
        for i, idea in enumerate(pending, 1):
            self.stdout.write(f'  {i}. {idea.topic}')
            self.stdout.write(f'     Keywords: {", ".join(idea.keywords)}')
            self.stdout.write(f'     Area: {idea.expertise_area}')
            self.stdout.write(f'     Created: {idea.created_at}')
            self.stdout.write('')
    
    def _generate_ideas(self, pipeline: ContentPipeline, count: int):
        """Generate new blog post ideas."""
        self.stdout.write(f'Generating {count} new blog post ideas...')
        
        try:
            ideas = pipeline.generate_ideas_only(num_ideas=count)
            
            self.stdout.write(self.style.SUCCESS(
                f'Successfully generated {len(ideas)} ideas:'
            ))
            for i, idea in enumerate(ideas, 1):
                self.stdout.write(f'  {i}. {idea.topic}')
                self.stdout.write(f'     Keywords: {", ".join(idea.keywords)}')
                self.stdout.write(f'     Area: {idea.expertise_area}')
                self.stdout.write('')
                
        except Exception as e:
            raise CommandError(f'Failed to generate ideas: {e}')
    
    def _process_idea(self, pipeline: ContentPipeline):
        """Process one pending idea through the full pipeline."""
        self.stdout.write('Processing pending idea through content pipeline...')
        
        try:
            post_ids = pipeline.run_full_pipeline(num_posts=1)
            
            if not post_ids:
                self.stdout.write(self.style.WARNING(
                    'No posts created. Check pending ideas or generation logs.'
                ))
                return
            
            post_id = post_ids[0]
            
            # Get the created post
            post = pipeline.post_repo.find_by_id(post_id)
            
            if post:
                self.stdout.write(self.style.SUCCESS(
                    f'✓ Published: {post.title}'
                ))
                self.stdout.write(f'  Slug: {post.slug.value}')
                self.stdout.write(f'  Status: {post.status.value}')
                self.stdout.write(f'  Tags: {", ".join(str(t) for t in post.tags)}')
            else:
                self.stdout.write(self.style.WARNING(
                    f'Post created with ID {post_id} but could not retrieve it'
                ))
                
        except Exception as e:
            raise CommandError(f'Failed to process idea: {e}')
