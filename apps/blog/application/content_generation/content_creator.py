"""Content creation service - generates full blog posts from ideas."""
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from django.conf import settings

from apps.blog.domain.entities import BlogIdea, GenerationStage, ContentGenerationLog

logger = logging.getLogger(__name__)

# Path to reference samples
REFERENCE_SAMPLES_DIR = Path(__file__).parent.parent.parent / "reference_samples"


@dataclass
class GeneratedContent:
    """Result of content generation."""
    title: str
    content: str  # Markdown
    meta_description: str
    tags: list[str]
    input_tokens: int
    output_tokens: int


class ContentCreatorService:
    """Service for creating blog post content from ideas using AI."""
    
    AUTHOR_NAME = "Joseph Prince"  # Your name for byline
    
    # Using o3-mini for 128k context - needed to fit all reference samples + output
    def __init__(self, openai_api_key: str | None = None, model: str = "o3-mini"):
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.model = model
        self._client = None
        self._reference_samples = None
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.openai_api_key)
        return self._client
    
    def generate_content(self, idea: BlogIdea) -> Tuple[GeneratedContent | None, ContentGenerationLog]:
        """Generate full blog post content from an idea.
        
        Args:
            idea: BlogIdea entity with topic and keywords
        
        Returns:
            Tuple of (GeneratedContent or None, ContentGenerationLog)
        """
        start_time = time.time()
        
        prompt = self._build_content_prompt(idea)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=8000,  # Increased for longer, detailed posts
            )
            
            duration = time.time() - start_time
            content_text = response.choices[0].message.content
            
            # Parse the generated content
            generated = self._parse_content(content_text, idea)
            
            log = ContentGenerationLog(
                idea_id=idea.id,
                stage=GenerationStage.CONTENT_CREATION,
                model_used=self.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                duration_seconds=duration,
                success=True,
                output_preview=content_text[:500],
            )
            
            logger.info(f"Generated content for: {idea.topic} ({response.usage.total_tokens} tokens)")
            return generated, log
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Content generation failed: {e}")
            
            log = ContentGenerationLog(
                idea_id=idea.id,
                stage=GenerationStage.CONTENT_CREATION,
                model_used=self.model,
                duration_seconds=duration,
                success=False,
                error_message=str(e),
            )
            
            return None, log
    
    def _load_reference_samples(self) -> str:
        """Load reference writing samples for style matching."""
        if self._reference_samples is not None:
            return self._reference_samples
        
        samples = []
        # Load all sample files in full - o3-mini has 128k context
        if REFERENCE_SAMPLES_DIR.exists():
            for filepath in sorted(REFERENCE_SAMPLES_DIR.glob("*.md")):
                content = filepath.read_text(encoding="utf-8")
                # Strip markdown code fence if present
                content = content.strip()
                if content.startswith("```markdown"):
                    content = content[11:]
                if content.endswith("```"):
                    content = content[:-3]
                samples.append(f"=== {filepath.stem} ===\n{content.strip()}")
        
        self._reference_samples = "\n\n".join(samples) if samples else ""
        return self._reference_samples
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for content generation."""
        reference_text = self._load_reference_samples()
        
        base_prompt = f"""You are {self.AUTHOR_NAME}, writing for your professional portfolio blog.

CONTENT APPROACH - Objective Analysis:
- Write OBJECTIVE thought leadership pieces analyzing industry topics
- DO NOT fabricate personal anecdotes or work experiences
- DO NOT reference "my company", "my team", "when I was..." stories
- Instead: analyze trends, discuss tradeoffs, reference public examples (open source projects, well-known companies, published research)
- You can reference: industry patterns, common scenarios teams face, published case studies, general observations
- Frame insights as analysis, not personal narrative

VOICE & STYLE (match these samples of my actual writing):

{reference_text}

KEY CHARACTERISTICS OF MY WRITING:
- Analytical and precise - I examine topics from multiple angles
- I use technical terms correctly without over-explaining
- I write in complete, flowing sentences - not choppy fragments
- I acknowledge limitations, tradeoffs, and "it depends" scenarios
- I ask genuine questions and express curiosity
- Conversational but professional tone
- I take clear stances backed by reasoning

AVOID THESE AI PATTERNS:
- Em dashes (—) - use regular dashes (-) or rewrite
- "crucial", "vital", "comprehensive", "landscape", "realm", "delve", "foster"
- "In today's...", "It's worth noting", "At the end of the day", "Let's dive in"
- Starting multiple sentences with "This", "That", "These"
- Excessive bullet points - I prefer prose paragraphs
- Overly formal headers - keep them natural

CONTENT REQUIREMENTS:
- Opinion/analysis piece, NOT a tutorial
- NO code snippets or implementation details
- NO fabricated personal stories - use objective analysis instead
- Reference real companies/projects/research when helpful (Google, Stripe, Linux kernel, etc.)
- Take a clear stance on something
- 800-1200 words in Markdown (no code blocks)"""

        return base_prompt

    def _build_content_prompt(self, idea: BlogIdea) -> str:
        """Build the prompt for content generation."""
        keywords_str = ", ".join(idea.keywords) if idea.keywords else "general tech topics"
        
        return f"""Write a blog post on: {idea.topic}

Keywords to weave in naturally: {keywords_str}
Area: {idea.expertise_area}

Write in my voice (see the samples in the system prompt). This should read like something I actually wrote - analytical, technically precise, connecting ideas to real experience.

Format your response as:
---CONTENT---
[The full blog post in Markdown - no code blocks]

---META_DESCRIPTION---
[150-160 character SEO description]

---TAGS---
tag1, tag2, tag3
"""

    def _parse_content(self, raw_content: str, idea: BlogIdea) -> GeneratedContent:
        """Parse the AI response into structured content."""
        content = ""
        meta_description = ""
        tags = idea.keywords.copy() if idea.keywords else []
        
        # Split by markers
        if "---CONTENT---" in raw_content:
            parts = raw_content.split("---CONTENT---")
            if len(parts) > 1:
                remaining = parts[1]
                
                if "---META_DESCRIPTION---" in remaining:
                    content_parts = remaining.split("---META_DESCRIPTION---")
                    content = content_parts[0].strip()
                    
                    if len(content_parts) > 1:
                        meta_remaining = content_parts[1]
                        
                        if "---TAGS---" in meta_remaining:
                            meta_parts = meta_remaining.split("---TAGS---")
                            meta_description = meta_parts[0].strip()
                            
                            if len(meta_parts) > 1:
                                tags_str = meta_parts[1].strip()
                                tags = [t.strip() for t in tags_str.split(",")]
                        else:
                            meta_description = meta_remaining.strip()
                else:
                    content = remaining.strip()
        else:
            # Fallback: treat entire response as content
            content = raw_content.strip()
        
        # Generate meta description if not provided
        if not meta_description:
            meta_description = content[:157] + "..." if len(content) > 160 else content
        
        return GeneratedContent(
            title=idea.topic,
            content=content,
            meta_description=meta_description[:300],
            tags=tags[:5],
            input_tokens=0,  # Will be set from API response
            output_tokens=0,
        )
