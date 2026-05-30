"""
Unit tests for blog domain value objects.
No Django imports, no I/O - pure Python only.
"""
from __future__ import annotations

import pytest

from apps.blog.domain.value_objects import (
    Excerpt,
    FeaturedImagePath,
    PostStatus,
    ReadingTime,
    Slug,
)


class TestSlug:
    def test_valid_slug_stores_value(self):
        s = Slug('my-post')
        assert s.value == 'my-post'

    def test_slug_is_normalized_to_lowercase(self):
        s = Slug('My-Post')
        assert s.value == 'my-post'

    def test_slug_strips_whitespace(self):
        s = Slug('  my-post  ')
        assert s.value == 'my-post'

    def test_str_returns_value(self):
        assert str(Slug('hello-world')) == 'hello-world'

    def test_empty_slug_raises(self):
        with pytest.raises(ValueError, match='must not be empty'):
            Slug('')

    def test_whitespace_only_slug_raises(self):
        with pytest.raises(ValueError, match='must not be empty'):
            Slug('   ')

    def test_slug_over_255_chars_raises(self):
        long_val = 'a' * 256
        with pytest.raises(ValueError, match='255 characters'):
            Slug(long_val)

    def test_slug_exactly_255_chars_is_valid(self):
        # 255-char slug: starts a, alternates with -a => 128 segments max
        # Use 255 'a' chars - valid because it's all lowercase
        # Actually the pattern requires segments separated by hyphens
        # Build: 'a-' * 127 + 'a' = 253+1 = no... let's do 'a' * 255
        val = 'a' * 255
        s = Slug(val)
        assert len(s.value) == 255

    def test_slug_with_invalid_chars_raises(self):
        with pytest.raises(ValueError, match='must match'):
            Slug('my post')

    def test_slug_with_uppercase_raises_after_normalization_passes(self):
        # Uppercase is normalized away, so 'MY-POST' -> 'my-post' is valid
        s = Slug('MY-POST')
        assert s.value == 'my-post'

    def test_slug_with_special_chars_raises(self):
        with pytest.raises(ValueError, match='must match'):
            Slug('my_post')

    def test_slug_with_consecutive_hyphens_raises(self):
        with pytest.raises(ValueError, match='must match'):
            Slug('my--post')

    def test_slug_with_leading_hyphen_raises(self):
        with pytest.raises(ValueError, match='must match'):
            Slug('-my-post')

    def test_slug_with_trailing_hyphen_raises(self):
        with pytest.raises(ValueError, match='must match'):
            Slug('my-post-')

    def test_slug_with_numbers_is_valid(self):
        s = Slug('post-2024-01')
        assert s.value == 'post-2024-01'

    def test_slug_equality(self):
        assert Slug('hello') == Slug('hello')

    def test_slug_inequality(self):
        assert Slug('hello') != Slug('world')

    def test_slug_is_frozen(self):
        s = Slug('test')
        with pytest.raises(Exception):
            s.value = 'changed'


class TestExcerpt:
    def test_valid_excerpt_stores_text(self):
        e = Excerpt('A short summary.')
        assert e.text == 'A short summary.'

    def test_excerpt_strips_whitespace(self):
        e = Excerpt('  padded  ')
        assert e.text == 'padded'

    def test_excerpt_strips_html_tags(self):
        e = Excerpt('<p>Hello <strong>world</strong></p>')
        assert e.text == 'Hello world'

    def test_excerpt_strips_html_with_attributes(self):
        e = Excerpt('<a href="https://example.com">Click here</a>')
        assert e.text == 'Click here'

    def test_empty_excerpt_raises(self):
        with pytest.raises(ValueError, match='must not be empty'):
            Excerpt('')

    def test_html_only_excerpt_raises(self):
        with pytest.raises(ValueError, match='must not be empty'):
            Excerpt('<p></p>')

    def test_excerpt_over_500_chars_raises(self):
        with pytest.raises(ValueError, match='500 characters'):
            Excerpt('a' * 501)

    def test_excerpt_exactly_500_chars_is_valid(self):
        e = Excerpt('a' * 500)
        assert len(e.text) == 500

    def test_str_returns_text(self):
        e = Excerpt('summary')
        assert str(e) == 'summary'

    def test_excerpt_is_frozen(self):
        e = Excerpt('summary')
        with pytest.raises(Exception):
            e.text = 'changed'


class TestReadingTime:
    def test_valid_reading_time_stores_minutes(self):
        rt = ReadingTime(minutes=5)
        assert rt.minutes == 5

    def test_reading_time_one_minute_is_valid(self):
        rt = ReadingTime(minutes=1)
        assert rt.minutes == 1

    def test_zero_minutes_raises(self):
        with pytest.raises(ValueError, match='integer >= 1'):
            ReadingTime(minutes=0)

    def test_negative_minutes_raises(self):
        with pytest.raises(ValueError, match='integer >= 1'):
            ReadingTime(minutes=-1)

    def test_str_format(self):
        rt = ReadingTime(minutes=3)
        assert str(rt) == '3 min read'

    def test_equality(self):
        assert ReadingTime(minutes=2) == ReadingTime(minutes=2)

    def test_inequality(self):
        assert ReadingTime(minutes=1) != ReadingTime(minutes=2)


class TestFeaturedImagePath:
    def test_valid_path_stored(self):
        p = FeaturedImagePath('blog/images/hero.jpg')
        assert p.path == 'blog/images/hero.jpg'

    def test_path_stripped_of_whitespace(self):
        p = FeaturedImagePath('  blog/images/hero.jpg  ')
        assert p.path == 'blog/images/hero.jpg'

    def test_empty_path_raises(self):
        with pytest.raises(ValueError, match='must not be empty'):
            FeaturedImagePath('')

    def test_path_starting_with_slash_raises(self):
        with pytest.raises(ValueError, match='must not start with /'):
            FeaturedImagePath('/blog/images/hero.jpg')

    def test_path_with_dotdot_raises(self):
        with pytest.raises(ValueError, match='must not contain'):
            FeaturedImagePath('blog/../secret.jpg')

    def test_str_returns_path(self):
        p = FeaturedImagePath('blog/images/hero.jpg')
        assert str(p) == 'blog/images/hero.jpg'


class TestPostStatus:
    def test_draft_value(self):
        assert PostStatus.DRAFT.value == 'draft'

    def test_published_value(self):
        assert PostStatus.PUBLISHED.value == 'published'
