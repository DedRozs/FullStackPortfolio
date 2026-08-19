"""
Unit tests for CanonicalHostRedirectMiddleware: alternate production
hostnames 301 to the canonical www host; dev, canonical, and appspot
hosts pass through. No I/O - the middleware is exercised directly.
"""
import pytest
from django.http import HttpResponse
from django.test import RequestFactory

from core.middleware import CANONICAL_HOST, CanonicalHostRedirectMiddleware

_PASSTHROUGH = HttpResponse('ok')


def _middleware():
    return CanonicalHostRedirectMiddleware(lambda request: _PASSTHROUGH)


@pytest.mark.parametrize(
    'host', ['thejosephprince.com', 'portfolio.thejosephprince.com']
)
def test_alternate_production_hosts_redirect_permanently(host, settings):
    settings.ALLOWED_HOSTS = ['*']
    request = RequestFactory().get('/blog/?page=2', HTTP_HOST=host)
    response = _middleware()(request)
    assert response.status_code == 301
    assert response['Location'] == f'https://{CANONICAL_HOST}/blog/?page=2'


@pytest.mark.parametrize(
    'host',
    [
        'localhost',
        'www.thejosephprince.com',
        'ai-fullstack-portfolio.uc.r.appspot.com',
    ],
)
def test_canonical_and_internal_hosts_pass_through(host, settings):
    settings.ALLOWED_HOSTS = ['*']
    request = RequestFactory().get('/', HTTP_HOST=host)
    response = _middleware()(request)
    assert response is _PASSTHROUGH
