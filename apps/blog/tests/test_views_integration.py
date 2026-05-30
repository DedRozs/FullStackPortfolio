"""
Integration tests for blog views.
Tests view behavior using Django's test client against an in-memory SQLite database.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.blog.models import Post, Tag


def _make_user(username='author', **kwargs):
    User = get_user_model()
    return User.objects.create_user(username=username, password='testpass123', **kwargs)


def _make_tag(name='Python'):
    tag = Tag.objects.create(name=name)
    return tag


def _make_post(
    title='Test Post',
    slug='test-post',
    excerpt='A short summary for the test post.',
    body='Some body content that is long enough to read.',
    status='published',
    author=None,
    reading_time_minutes=1,
    published_at=None,
    tags=None,
):
    if published_at is None and status == 'published':
        published_at = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    obj = Post.objects.create(
        title=title,
        slug=slug,
        excerpt=excerpt,
        body=body,
        status=status,
        author=author,
        reading_time_minutes=reading_time_minutes,
        published_at=published_at,
    )
    if tags:
        obj.tags.set(tags)
    return obj


class TestBlogListView(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = _make_user()

    def test_list_returns_200(self):
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)

    def test_list_shows_only_published_posts(self):
        published = _make_post(
            title='Published Post', slug='published-post', author=self.author
        )
        _make_post(
            title='Draft Post',
            slug='draft-post',
            status='draft',
            author=self.author,
        )
        response = self.client.get(reverse('blog:post_list'))
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        slugs = [p.slug for p in posts]
        self.assertIn('published-post', slugs)
        self.assertNotIn('draft-post', slugs)

    def test_list_excludes_drafts_from_unauthenticated_users(self):
        _make_post(
            title='Draft Post', slug='draft-post', status='draft', author=self.author
        )
        response = self.client.get(reverse('blog:post_list'))
        posts = response.context['posts']
        self.assertEqual(len(posts), 0)

    def test_list_pagination_page_obj_in_context(self):
        for i in range(3):
            _make_post(
                title=f'Post {i}',
                slug=f'post-{i}',
                author=self.author,
            )
        response = self.client.get(reverse('blog:post_list'))
        self.assertIn('page_obj', response.context)

    def test_list_returns_paginated_page_2(self):
        """With more than PAGE_SIZE=10 posts, page 2 should return the overflow."""
        for i in range(12):
            _make_post(
                title=f'Post {i:02d}',
                slug=f'post-{i:02d}',
                author=self.author,
            )
        response = self.client.get(reverse('blog:post_list') + '?page=2')
        self.assertEqual(response.status_code, 200)
        posts = response.context['posts']
        self.assertEqual(len(posts), 2)

    def test_list_invalid_page_param_defaults_to_1(self):
        _make_post(slug='the-post', author=self.author)
        response = self.client.get(reverse('blog:post_list') + '?page=abc')
        self.assertEqual(response.status_code, 200)


class TestBlogDetailView(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = _make_user()

    def test_detail_published_post_returns_200(self):
        _make_post(slug='my-post', author=self.author)
        response = self.client.get(reverse('blog:post_detail', kwargs={'slug': 'my-post'}))
        self.assertEqual(response.status_code, 200)

    def test_detail_draft_returns_404_for_unauthenticated(self):
        _make_post(slug='draft-post', status='draft', author=self.author)
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'draft-post'})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_nonexistent_slug_returns_404(self):
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'does-not-exist'})
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_post_in_context(self):
        _make_post(title='Hello World', slug='hello-world', author=self.author)
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'hello-world'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('post', response.context)
        post_dto = response.context['post']
        self.assertEqual(post_dto.title, 'Hello World')

    def test_detail_reading_time_present_in_dto(self):
        _make_post(
            slug='read-post',
            body='word ' * 400,
            author=self.author,
            reading_time_minutes=2,
        )
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'read-post'})
        )
        post_dto = response.context['post']
        self.assertEqual(post_dto.reading_time_minutes, 2)

    def test_detail_draft_accessible_when_staff(self):
        """Only staff users can access draft posts via the public URL."""
        staff_user = _make_user(username='staff_member', is_staff=True)
        _make_post(slug='draft-post', status='draft', author=self.author)
        self.client.login(username='staff_member', password='testpass123')
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'draft-post'})
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_draft_returns_404_for_authenticated_non_staff(self):
        """A logged-in non-staff user must not see draft posts."""
        _make_post(slug='draft-post-ns', status='draft', author=self.author)
        self.client.login(username='author', password='testpass123')
        response = self.client.get(
            reverse('blog:post_detail', kwargs={'slug': 'draft-post-ns'})
        )
        self.assertEqual(response.status_code, 404)


class TestRSSFeed(TestCase):
    def setUp(self):
        self.client = Client()
        self.author = _make_user()

    def test_feed_returns_200(self):
        response = self.client.get(reverse('blog:post_feed'))
        self.assertEqual(response.status_code, 200)

    def test_feed_content_type_is_xml(self):
        response = self.client.get(reverse('blog:post_feed'))
        self.assertIn('xml', response['Content-Type'])

    def test_feed_contains_published_posts(self):
        _make_post(title='RSS Post', slug='rss-post', author=self.author)
        response = self.client.get(reverse('blog:post_feed'))
        self.assertContains(response, 'RSS Post')

    def test_feed_excludes_draft_posts(self):
        _make_post(title='Draft', slug='draft-rss', status='draft', author=self.author)
        response = self.client.get(reverse('blog:post_feed'))
        self.assertNotContains(response, 'Draft')

    def test_feed_is_valid_rss(self):
        """RSS feed must have the rss root element."""
        response = self.client.get(reverse('blog:post_feed'))
        content = response.content.decode('utf-8')
        self.assertIn('<rss', content)
