"""
Request middleware for the core project.
"""

from django.http import HttpResponsePermanentRedirect

# The one hostname all public traffic should converge on. Alternate hosts
# (bare apex, legacy portfolio subdomain) stay mapped in App Engine so old
# links keep working, but every request to them is 301-redirected here.
CANONICAL_HOST = 'www.thejosephprince.com'
REDIRECT_HOSTS = frozenset({
    'thejosephprince.com',
    'portfolio.thejosephprince.com',
})


class CanonicalHostRedirectMiddleware:
    """Permanently redirect alternate production hostnames to the canonical one.

    Only hostnames explicitly listed in REDIRECT_HOSTS are redirected, so
    localhost, the appspot.com host (cron and health traffic), and test
    clients pass through untouched.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().partition(':')[0].lower()
        if host in REDIRECT_HOSTS:
            return HttpResponsePermanentRedirect(
                f'https://{CANONICAL_HOST}{request.get_full_path()}'
            )
        return self.get_response(request)
