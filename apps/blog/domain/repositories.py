"""Repository interfaces for the Blog bounded context."""
from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from apps.blog.domain.entities import BlogPost, PostStatus
from apps.blog.domain.value_objects import Slug, Tag


class BlogPostRepository(ABC):
    """Abstract repository for BlogPost aggregate.
    
    Provides collection-like interface for blog posts.
    """
    
    @abstractmethod
    def save(self, post: BlogPost) -> None:
        """Persist a blog post."""
        pass
    
    @abstractmethod
    def find_by_id(self, post_id: UUID) -> BlogPost | None:
        """Find a post by its ID."""
        pass
    
    @abstractmethod
    def find_by_slug(self, slug: Slug) -> BlogPost | None:
        """Find a post by its slug."""
        pass
    
    @abstractmethod
    def find_all_published(self, limit: int = 10, offset: int = 0) -> List[BlogPost]:
        """Find all published posts, ordered by publish date."""
        pass
    
    @abstractmethod
    def find_by_tag(self, tag: Tag, limit: int = 10, offset: int = 0) -> List[BlogPost]:
        """Find published posts with a specific tag."""
        pass
    
    @abstractmethod
    def find_all(self, status: PostStatus | None = None) -> List[BlogPost]:
        """Find all posts, optionally filtered by status."""
        pass
    
    @abstractmethod
    def delete(self, post: BlogPost) -> None:
        """Delete a blog post."""
        pass
    
    @abstractmethod
    def count_published(self) -> int:
        """Count total published posts."""
        pass
    
    @abstractmethod
    def get_all_tags(self) -> List[Tag]:
        """Get all unique tags from published posts."""
        pass
    
    @abstractmethod
    def search(
        self, 
        search_term: str, 
        tag: Tag | None = None,
        limit: int = 10, 
        offset: int = 0
    ) -> List[BlogPost]:
        """Search published posts by title and content."""
        pass
    
    @abstractmethod
    def count_search_results(self, search_term: str, tag: Tag | None = None) -> int:
        """Count total search results."""
        pass
