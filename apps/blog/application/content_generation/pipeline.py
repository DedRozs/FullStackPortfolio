"""Main content generation pipeline - orchestrates all stages."""
import logging
from datetime import datetime
from typing import List, Tuple
from uuid import UUID

from django.conf import settings
from django.utils import timezone

from apps.blog.domain.entities import (
    BlogPost, BlogIdea, IdeaStatus, PostStatus,
    GenerationStage, ContentGenerationLog
)
from apps.blog.domain.value_objects import Slug, Tag, PostContent
from apps.blog.application.content_generation.idea_generator import (
    IdeaGeneratorService, EXPERTISE_AREAS
)
from apps.blog.application.content_generation.content_creator import ContentCreatorService
from apps.blog.application.content_generation.proofreader import ProofreaderService

logger = logging.getLogger(__name__)


class ContentPipeline:
    """Orchestrates the full content generation pipeline.
    
    Pipeline stages:
    1. Generate ideas (if needed)
    2. Pick a pending idea
    3. Generate content
    4. Proofread and polish
    5. Publish if approved
    """
    
    AUTHOR_NAME = "Joseph Prince"
    
    def __init__(
        self,
        idea_repository,  # BlogIdeaRepository
        post_repository,  # BlogPostRepository
        log_repository,   # ContentGenerationLogRepository
        openai_api_key: str | None = None,
    ):
        self.idea_repo = idea_repository
        self.post_repo = post_repository
        self.log_repo = log_repository
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
        
        # Initialize services
        self.idea_generator = IdeaGeneratorService(self.openai_api_key)
        self.content_creator = ContentCreatorService(self.openai_api_key)
        self.proofreader = ProofreaderService(self.openai_api_key)
    
    def run_full_pipeline(self, num_posts: int = 1) -> List[UUID]:
        """Run the complete content generation pipeline.
        
        Args:
            num_posts: Number of posts to generate
        
        Returns:
            List of created BlogPost IDs
        """
        created_posts = []
        
        for i in range(num_posts):
            logger.info(f"Starting pipeline run {i+1}/{num_posts}")
            
            try:
                post_id = self._process_single_post()
                if post_id:
                    created_posts.append(post_id)
                    logger.info(f"Successfully created post: {post_id}")
                else:
                    logger.warning(f"Pipeline run {i+1} did not produce a post")
            except Exception as e:
                logger.error(f"Pipeline run {i+1} failed: {e}")
        
        return created_posts
    
    def _process_single_post(self) -> UUID | None:
        """Process a single post through the pipeline."""
        
        # Step 1: Get or create an idea
        idea = self._get_or_create_idea()
        if not idea:
            logger.error("No ideas available and couldn't generate new ones")
            return None
        
        logger.info(f"Processing idea: {idea.topic}")
        idea.start_processing()
        self.idea_repo.save(idea)
        
        try:
            # Step 2: Generate content
            content, content_log = self.content_creator.generate_content(idea)
            self.log_repo.save(content_log)
            
            if not content:
                idea.fail("Content generation failed")
                self.idea_repo.save(idea)
                return None
            
            # Step 3: Proofread
            proofread_result, proofread_log = self.proofreader.proofread(idea, content)
            self.log_repo.save(proofread_log)
            
            if not proofread_result:
                idea.fail("Proofreading failed")
                self.idea_repo.save(idea)
                return None
            
            if not proofread_result.approved:
                idea.reject(f"Quality score {proofread_result.quality_score} below threshold")
                self.idea_repo.save(idea)
                logger.warning(f"Idea rejected: {idea.topic} (score: {proofread_result.quality_score})")
                return None
            
            # Step 4: Create and publish blog post
            post = self._create_blog_post(idea, proofread_result)
            self.post_repo.save(post)
            
            # Log publishing
            publish_log = ContentGenerationLog(
                idea_id=idea.id,
                stage=GenerationStage.PUBLISHING,
                model_used="system",
                success=True,
                output_preview=f"Published: {post.title}",
            )
            self.log_repo.save(publish_log)
            
            # Mark idea as completed
            idea.complete(post.id)
            self.idea_repo.save(idea)
            
            return post.id
            
        except Exception as e:
            logger.error(f"Pipeline failed for idea {idea.id}: {e}")
            idea.fail(str(e))
            self.idea_repo.save(idea)
            return None
    
    def _get_or_create_idea(self) -> BlogIdea | None:
        """Get a pending idea or generate new ones."""
        # Try to get a pending idea
        pending_ideas = self.idea_repo.find_by_status(IdeaStatus.PENDING)
        
        if pending_ideas:
            return pending_ideas[0]
        
        # Generate new ideas
        logger.info("No pending ideas, generating new ones...")
        
        # Get existing topics to avoid duplicates
        existing_topics = self._get_existing_topics()
        
        new_ideas = self.idea_generator.generate_ideas(
            num_ideas=5,
            existing_topics=existing_topics,
        )
        
        if not new_ideas:
            return None
        
        # Filter out duplicates
        for idea in new_ideas:
            if not self.idea_generator.check_duplicate(idea.topic, existing_topics):
                self.idea_repo.save(idea)
                existing_topics.append(idea.topic)
        
        # Return the first new idea
        pending_ideas = self.idea_repo.find_by_status(IdeaStatus.PENDING)
        return pending_ideas[0] if pending_ideas else None
    
    def _get_existing_topics(self) -> List[str]:
        """Get list of existing blog post titles and idea topics."""
        existing = []
        
        # Get published posts
        posts = self.post_repo.find_all_published()
        existing.extend([p.title for p in posts])
        
        # Get completed/processing ideas
        for status in [IdeaStatus.COMPLETED, IdeaStatus.PROCESSING, IdeaStatus.PENDING]:
            ideas = self.idea_repo.find_by_status(status)
            existing.extend([i.topic for i in ideas])
        
        return existing
    
    def _create_blog_post(self, idea: BlogIdea, proofread_result) -> BlogPost:
        """Create a BlogPost entity from proofread content."""
        # Get tags from idea keywords (proofread_result doesn't have tags)
        tag_strings = idea.keywords[:5] if idea.keywords else ['technology']
        
        tags = []
        for t in tag_strings[:5]:
            try:
                # Clean and validate tag
                tag_value = t.strip().lower().replace(' ', '-')
                if len(tag_value) >= 2:
                    tags.append(Tag(tag_value))
            except ValueError:
                continue
        
        # Ensure at least one tag
        if not tags:
            tags = [Tag('technology')]
        
        post = BlogPost(
            title=proofread_result.title,
            content=PostContent(proofread_result.content),
            author_name=self.AUTHOR_NAME,
            tags=tags,
            meta_description=proofread_result.meta_description,
        )
        
        # Auto-publish
        post.publish()
        
        return post
    
    def generate_ideas_only(self, num_ideas: int = 5) -> List[BlogIdea]:
        """Generate and save new ideas without processing them.
        
        Useful for building up an idea backlog.
        """
        existing_topics = self._get_existing_topics()
        
        new_ideas = self.idea_generator.generate_ideas(
            num_ideas=num_ideas,
            existing_topics=existing_topics,
        )
        
        saved_ideas = []
        for idea in new_ideas:
            if not self.idea_generator.check_duplicate(idea.topic, existing_topics):
                self.idea_repo.save(idea)
                saved_ideas.append(idea)
                existing_topics.append(idea.topic)
        
        logger.info(f"Generated and saved {len(saved_ideas)} new ideas")
        return saved_ideas
