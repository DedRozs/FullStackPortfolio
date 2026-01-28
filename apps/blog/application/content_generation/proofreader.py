"""Proofreading service - reviews and polishes AI-generated content."""
import logging
import time
from dataclasses import dataclass
from typing import Tuple

from django.conf import settings

from apps.blog.domain.entities import BlogIdea, GenerationStage, ContentGenerationLog
from apps.blog.application.content_generation.content_creator import GeneratedContent

logger = logging.getLogger(__name__)


@dataclass
class ProofreadResult:
    """Result of proofreading."""
    content: str  # Polished Markdown content
    title: str  # Possibly improved title
    meta_description: str
    quality_score: float  # 0-10 rating
    improvements_made: list[str]
    approved: bool  # Whether content passes quality threshold
    input_tokens: int
    output_tokens: int


class ProofreaderService:
    """Service for proofreading and polishing AI-generated content.
    
    Uses a different model/approach to review content for:
    - Grammar and clarity
    - Technical accuracy
    - SEO optimization
    - Engagement and readability
    """
    
    QUALITY_THRESHOLD = 7.0  # Minimum score to auto-publish
    
    def __init__(self, openai_api_key: str | None = None, model: str = "gpt-5-mini"):
        self.openai_api_key = openai_api_key or getattr(settings, 'OPENAI_API_KEY', '')
        self.model = model
        self._client = None
    
    @property
    def client(self):
        """Lazy load OpenAI client."""
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.openai_api_key)
        return self._client
    
    def proofread(
        self, 
        idea: BlogIdea, 
        content: GeneratedContent
    ) -> Tuple[ProofreadResult | None, ContentGenerationLog]:
        """Proofread and polish the generated content.
        
        Args:
            idea: Original BlogIdea
            content: Generated content to review
        
        Returns:
            Tuple of (ProofreadResult or None, ContentGenerationLog)
        """
        start_time = time.time()
        
        prompt = self._build_proofread_prompt(content)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=5000,
                response_format={"type": "json_object"}
            )
            
            duration = time.time() - start_time
            response_text = response.choices[0].message.content
            
            # Parse the proofread result
            import json
            result_data = json.loads(response_text)
            
            result = ProofreadResult(
                content=result_data.get('polished_content', content.content),
                title=result_data.get('title', content.title),
                meta_description=result_data.get('meta_description', content.meta_description),
                quality_score=float(result_data.get('quality_score', 5.0)),
                improvements_made=result_data.get('improvements', []),
                approved=float(result_data.get('quality_score', 0)) >= self.QUALITY_THRESHOLD,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
            )
            
            log = ContentGenerationLog(
                idea_id=idea.id,
                stage=GenerationStage.PROOFREADING,
                model_used=self.model,
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                duration_seconds=duration,
                success=True,
                output_preview=f"Score: {result.quality_score}/10, Approved: {result.approved}",
            )
            
            logger.info(
                f"Proofread complete: {idea.topic} - "
                f"Score: {result.quality_score}/10, Approved: {result.approved}"
            )
            return result, log
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Proofreading failed: {e}")
            
            log = ContentGenerationLog(
                idea_id=idea.id,
                stage=GenerationStage.PROOFREADING,
                model_used=self.model,
                duration_seconds=duration,
                success=False,
                error_message=str(e),
            )
            
            return None, log
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for proofreading."""
        return """You are an editor who makes AI-generated text sound human.

Your PRIMARY job is removing AI writing patterns:
- Replace em dashes (—) with simple dashes (-) or rewrite
- Remove "crucial", "vital", "comprehensive", "landscape", "realm", "delve", "foster"
- Remove "In today's", "In the world of", "When it comes to", "It's worth noting"
- Remove "At the end of the day", "In conclusion", "Let's dive in"
- Fix sentences starting with "This is", "That is", "These are" repeatedly
- Break up long compound sentences into shorter ones
- Convert excessive bullet points into prose paragraphs
- Make headers casual ("The real issue" not "Understanding Key Challenges")

Secondary: fix grammar, improve flow, check accuracy.

Rate 1-10 where 10 = sounds completely human-written.
Respond only with valid JSON."""

    def _build_proofread_prompt(self, content: GeneratedContent) -> str:
        """Build the prompt for proofreading."""
        return f"""Edit this blog post to sound human, not AI-generated:

**Title:** {content.title}
**Meta Description:** {content.meta_description}
**Tags:** {', '.join(content.tags)}

**Content:**
{content.content}

FIND AND FIX these AI patterns:
1. Em dashes (—) - replace with dashes (-) or rewrite
2. Words: "crucial", "comprehensive", "landscape", "delve", "realm", "foster", "vital"
3. Phrases: "In today's", "It's worth noting", "At the end of the day", "Let's dive"
4. Excessive bullet points - convert some to paragraphs
5. Overly formal headers - make casual
6. Long compound sentences - break them up
7. Generic statements - make specific or cut

Also fix grammar and improve flow.

JSON response:
{{
    "title": "improved title (no em dashes, no AI buzzwords)",
    "polished_content": "full edited markdown (no code blocks)",
    "meta_description": "150-160 chars, natural language",
    "quality_score": 8.5,
    "improvements": ["list of changes made"],
    "technical_concerns": []
}}"""
