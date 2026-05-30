"""
Unit tests for blog domain entities (Post, Tag) and domain services.
No Django imports, no I/O - pure Python only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from unittest.mock import MagicMock

import pytest

from apps.blog.domain.entities import Post, Tag
from apps.blog.domain.events import PostPublished, PostUnpublished, PostVectorizationFailed
from apps.blog.domain.exceptions import PublishInvariantError
from apps.blog.domain.repositories import IPostRepository
from apps.blog.domain.services import ReadingTimeCalculator, RelatedPostFinder
from apps.blog.domain.value_objects import (
    Excerpt,
    PostStatus,
    ReadingTime,
    Slug,
)

_NOW = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)


def _make_post(
    title='Test Post',
    slug='test-post',
    excerpt='A short summary for the test post.',
    body='Some body content that is long enough.',
    author_id=1,
    reading_time_minutes=1,
    status=PostStatus.DRAFT,
    id=None,
    tag_ids=None,
):
    return Post(
        title=title,
        slug=Slug(slug),
        excerpt=Excerpt(excerpt),
        body=body,
        author_id=author_id,
        reading_time=ReadingTime(minutes=reading_time_minutes),
        status=status,
        id=id,
        tag_ids=tag_ids or [],
    )


# ------------------------------------------------------------------ #
# Tag entity
# ------------------------------------------------------------------ #

class TestTag:
    def test_tag_stores_name_and_slug(self):
        tag = Tag(name='Python', slug=Slug('python'))
        assert tag.name == 'Python'
        assert tag.slug == Slug('python')

    def test_tag_equality_by_id_when_both_have_ids(self):
        t1 = Tag(name='A', slug=Slug('a'), id=1)
        t2 = Tag(name='B', slug=Slug('b'), id=1)
        assert t1 == t2

    def test_tag_equality_by_slug_when_no_id(self):
        t1 = Tag(name='Python', slug=Slug('python'))
        t2 = Tag(name='Python', slug=Slug('python'))
        assert t1 == t2

    def test_tag_inequality_by_slug(self):
        t1 = Tag(name='Python', slug=Slug('python'))
        t2 = Tag(name='Django', slug=Slug('django'))
        assert t1 != t2

    def test_tag_empty_name_raises(self):
        with pytest.raises(ValueError):
            Tag(name='', slug=Slug('empty'))

    def test_tag_name_over_100_chars_raises(self):
        with pytest.raises(ValueError):
            Tag(name='x' * 101, slug=Slug('x' * 101))

    def test_tag_hashable_with_id(self):
        t = Tag(name='X', slug=Slug('x'), id=7)
        assert hash(t) == hash(7)

    def test_tag_hashable_without_id(self):
        t = Tag(name='X', slug=Slug('x'))
        assert hash(t) == hash(Slug('x'))


# ------------------------------------------------------------------ #
# Post entity - construction
# ------------------------------------------------------------------ #

class TestPostConstruction:
    def test_post_stores_all_fields(self):
        p = _make_post(id=1)
        assert p.title == 'Test Post'
        assert p.status == PostStatus.DRAFT
        assert p.tag_ids == []

    def test_post_empty_title_raises(self):
        with pytest.raises(ValueError, match='must be non-empty'):
            _make_post(title='')

    def test_post_title_over_300_chars_raises(self):
        with pytest.raises(ValueError, match='must be non-empty'):
            _make_post(title='x' * 301)

    def test_post_default_status_is_draft(self):
        p = _make_post()
        assert p.status == PostStatus.DRAFT

    def test_post_pending_events_start_empty(self):
        p = _make_post()
        assert p.collect_events() == []


# ------------------------------------------------------------------ #
# Post.publish
# ------------------------------------------------------------------ #

class TestPostPublish:
    def test_publish_sets_status_published(self):
        p = _make_post()
        p.publish(_NOW)
        assert p.status == PostStatus.PUBLISHED

    def test_publish_sets_published_at(self):
        p = _make_post()
        p.publish(_NOW)
        assert p.published_at == _NOW

    def test_publish_emits_post_published_event(self):
        p = _make_post(id=42)
        p.publish(_NOW)
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], PostPublished)
        assert events[0].post_id == 42
        assert events[0].slug == 'test-post'

    def test_publish_empty_body_raises(self):
        p = _make_post(body='')
        with pytest.raises(PublishInvariantError, match='empty body'):
            p.publish(_NOW)

    def test_publish_collects_and_clears_events(self):
        p = _make_post(id=1)
        p.publish(_NOW)
        first = p.collect_events()
        second = p.collect_events()
        assert len(first) == 1
        assert second == []


# ------------------------------------------------------------------ #
# Post.unpublish
# ------------------------------------------------------------------ #

class TestPostUnpublish:
    def test_unpublish_sets_status_draft(self):
        p = _make_post(status=PostStatus.PUBLISHED, id=1)
        p.published_at = _NOW
        p.unpublish()
        assert p.status == PostStatus.DRAFT

    def test_unpublish_clears_published_at(self):
        p = _make_post(status=PostStatus.PUBLISHED, id=1)
        p.published_at = _NOW
        p.unpublish()
        assert p.published_at is None

    def test_unpublish_emits_event_when_id_set(self):
        p = _make_post(status=PostStatus.PUBLISHED, id=5)
        p.unpublish()
        events = p.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], PostUnpublished)
        assert events[0].post_id == 5

    def test_unpublish_no_event_when_id_none(self):
        p = _make_post(status=PostStatus.PUBLISHED)
        p.unpublish()
        assert p.collect_events() == []


# ------------------------------------------------------------------ #
# Post tag management
# ------------------------------------------------------------------ #

class TestPostTagManagement:
    def test_add_tag_appends_id(self):
        p = _make_post()
        p.add_tag(10)
        assert 10 in p.tag_ids

    def test_add_tag_idempotent(self):
        p = _make_post()
        p.add_tag(10)
        p.add_tag(10)
        assert p.tag_ids.count(10) == 1

    def test_remove_tag_removes_id(self):
        p = _make_post(tag_ids=[10, 20])
        p.remove_tag(10)
        assert 10 not in p.tag_ids
        assert 20 in p.tag_ids

    def test_remove_nonexistent_tag_is_safe(self):
        p = _make_post(tag_ids=[20])
        p.remove_tag(99)
        assert p.tag_ids == [20]


# ------------------------------------------------------------------ #
# ReadingTimeCalculator domain service
# ------------------------------------------------------------------ #

class TestReadingTimeCalculator:
    def setup_method(self):
        self.calc = ReadingTimeCalculator()

    def test_empty_body_returns_1_minute(self):
        rt = self.calc.calculate('')
        assert rt.minutes == 1

    def test_200_words_returns_1_minute(self):
        body = 'word ' * 200
        rt = self.calc.calculate(body)
        assert rt.minutes == 1

    def test_201_words_returns_2_minutes(self):
        body = 'word ' * 201
        rt = self.calc.calculate(body)
        assert rt.minutes == 2

    def test_400_words_returns_2_minutes(self):
        body = 'word ' * 400
        rt = self.calc.calculate(body)
        assert rt.minutes == 2

    def test_401_words_returns_3_minutes(self):
        body = 'word ' * 401
        rt = self.calc.calculate(body)
        assert rt.minutes == 3

    def test_100_words_rounds_up_to_1_minute(self):
        body = 'word ' * 100
        rt = self.calc.calculate(body)
        assert rt.minutes == 1

    def test_returns_reading_time_instance(self):
        rt = self.calc.calculate('hello world')
        assert isinstance(rt, ReadingTime)


# ------------------------------------------------------------------ #
# RelatedPostFinder domain service
# ------------------------------------------------------------------ #

class TestRelatedPostFinder:
    def _make_published_post(self, id, tag_ids):
        return _make_post(
            id=id,
            slug=f'post-{id}',
            tag_ids=tag_ids,
            status=PostStatus.PUBLISHED,
        )

    def test_returns_empty_when_post_has_no_tags(self):
        repo = MagicMock(spec=IPostRepository)
        finder = RelatedPostFinder(repo)
        p = _make_post(id=1, tag_ids=[])
        result = finder.find_related(p)
        assert result == []
        repo.find_published_by_tag_ids.assert_not_called()

    def test_returns_empty_when_post_id_is_none(self):
        repo = MagicMock(spec=IPostRepository)
        finder = RelatedPostFinder(repo)
        p = _make_post(tag_ids=[1, 2])
        result = finder.find_related(p)
        assert result == []
        repo.find_published_by_tag_ids.assert_not_called()

    def test_delegates_to_repository(self):
        repo = MagicMock(spec=IPostRepository)
        related_posts = [self._make_published_post(2, [1])]
        repo.find_published_by_tag_ids.return_value = related_posts
        finder = RelatedPostFinder(repo)
        post = self._make_published_post(1, [1, 2])
        result = finder.find_related(post, limit=3)
        repo.find_published_by_tag_ids.assert_called_once_with(
            tag_ids=[1, 2], exclude_post_id=1, limit=3
        )
        assert result == related_posts

    def test_default_limit_is_3(self):
        repo = MagicMock(spec=IPostRepository)
        repo.find_published_by_tag_ids.return_value = []
        finder = RelatedPostFinder(repo)
        post = self._make_published_post(1, [5])
        finder.find_related(post)
        repo.find_published_by_tag_ids.assert_called_once_with(
            tag_ids=[5], exclude_post_id=1, limit=3
        )


# ------------------------------------------------------------------ #
# Domain events
# ------------------------------------------------------------------ #

class TestPostVectorizationFailedEvent:
    def test_event_is_frozen(self):
        event = PostVectorizationFailed(
            post_id=1,
            slug='test-post',
            error_message='Connection refused',
            failed_at=_NOW,
        )
        with pytest.raises(Exception):
            event.post_id = 99

    def test_event_stores_fields(self):
        event = PostVectorizationFailed(
            post_id=7,
            slug='my-post',
            error_message='Timeout',
            failed_at=_NOW,
        )
        assert event.post_id == 7
        assert event.slug == 'my-post'
        assert event.error_message == 'Timeout'
        assert event.failed_at == _NOW
