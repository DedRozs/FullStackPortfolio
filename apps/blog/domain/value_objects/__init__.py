"""Blog-specific value objects."""
from dataclasses import dataclass
import re
from typing import List


@dataclass(frozen=True)
class Slug:
    """URL-friendly slug value object.
    
    Validates and normalizes slugs for blog posts.
    """
    value: str
    
    def __post_init__(self) -> None:
        if not self._is_valid_slug(self.value):
            raise ValueError(f"Invalid slug: {self.value}")
    
    @staticmethod
    def _is_valid_slug(slug: str) -> bool:
        """Slug must be lowercase alphanumeric with hyphens."""
        pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        return bool(re.match(pattern, slug)) and len(slug) <= 200
    
    @classmethod
    def from_title(cls, title: str) -> 'Slug':
        """Generate a slug from a title."""
        slug = title.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        slug = slug.strip('-')
        return cls(slug[:200])
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class Tag:
    """Tag value object for categorizing posts."""
    name: str
    
    def __post_init__(self) -> None:
        if not self.name or len(self.name.strip()) < 2:
            raise ValueError("Tag must be at least 2 characters")
        if len(self.name) > 50:
            raise ValueError("Tag must not exceed 50 characters")
    
    @property
    def slug(self) -> str:
        """URL-friendly version of tag."""
        return self.name.lower().replace(' ', '-')
    
    def __str__(self) -> str:
        return self.name.strip()


@dataclass(frozen=True)
class PostContent:
    """Blog post content value object.
    
    Contains the main body of the post in Markdown format.
    """
    markdown: str
    
    def __post_init__(self) -> None:
        if not self.markdown or len(self.markdown.strip()) < 50:
            raise ValueError("Post content must be at least 50 characters")
        if len(self.markdown) > 100000:
            raise ValueError("Post content must not exceed 100,000 characters")
    
    @property
    def excerpt(self) -> str:
        """Generate a short excerpt from content."""
        plain = self.markdown[:300]
        # Remove markdown syntax for excerpt
        plain = re.sub(r'[#*`\[\]()]', '', plain)
        return plain.strip() + '...' if len(self.markdown) > 300 else plain.strip()
    
    @property
    def reading_time_minutes(self) -> int:
        """Estimate reading time based on word count."""
        word_count = len(self.markdown.split())
        return max(1, round(word_count / 200))  # ~200 WPM average
    
    def __str__(self) -> str:
        return self.excerpt
