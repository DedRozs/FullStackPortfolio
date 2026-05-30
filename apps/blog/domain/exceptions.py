class SlugConflictError(Exception):
    """Raised when a Post slug already exists for a different Post."""


class PostNotFoundError(Exception):
    """Raised when a Post with the requested ID or slug does not exist."""


class TagNameConflictError(Exception):
    """Raised when a Tag name already exists in the blog bounded context."""


class PublishInvariantError(Exception):
    """Raised when publishing a Post that violates a publish invariant."""
