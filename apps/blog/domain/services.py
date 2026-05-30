from __future__ import annotations

import math

from .entities import Post
from .repositories import IPostRepository
from .value_objects import ReadingTime

_WORDS_PER_MINUTE = 200


class ReadingTimeCalculator:
    def calculate(self, body: str) -> ReadingTime:
        word_count = len(body.split())
        minutes = max(1, math.ceil(word_count / _WORDS_PER_MINUTE))
        return ReadingTime(minutes=minutes)


class RelatedPostFinder:
    def __init__(self, post_repository: IPostRepository) -> None:
        self._repo = post_repository

    def find_related(self, post: Post, limit: int = 3) -> list:
        if not post.tag_ids or post.id is None:
            return []
        return self._repo.find_published_by_tag_ids(
            tag_ids=post.tag_ids,
            exclude_post_id=post.id,
            limit=limit,
        )
