import os
from xml.sax.saxutils import escape

from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


SITE_ORIGIN = 'https://www.thejosephprince.com'

# Public, indexable routes. Auth-gated demo routes (/portal, /dashboard,
# /automations) are deliberately excluded - they only lead to a login wall.
PUBLIC_ROUTES = [
    ('/', '1.0', 'weekly'),
    ('/projects', '0.9', 'monthly'),
    ('/about', '0.8', 'monthly'),
    ('/resume', '0.8', 'monthly'),
    ('/blog', '0.7', 'weekly'),
    ('/ai', '0.6', 'monthly'),
    ('/contact', '0.5', 'yearly'),
]


# Outside static/react_app: Vite empties that directory on every frontend build.
RESUME_PDF_PATH = os.path.join(
    os.path.dirname(__file__),
    'generated', 'joseph-prince-resume.pdf',
)


@ensure_csrf_cookie
def index(request):
    """Serve the React SPA shell. React Router handles all client-side routing."""
    return render(request, 'react_app/index.html')


def resume_pdf(request):
    """Serve the pre-generated resume PDF. Run manage.py generate_resume_pdf to (re)build it."""
    if not os.path.exists(RESUME_PDF_PATH):
        raise Http404(
            'Resume PDF not found. Run: python manage.py generate_resume_pdf'
        )
    return FileResponse(
        open(RESUME_PDF_PATH, 'rb'),
        content_type='application/pdf',
        as_attachment=True,
        filename='joseph-prince-resume.pdf',
    )


def robots_txt(request):
    """Serve a real robots.txt.

    Without an explicit route these fall through to the SPA catch-all and are
    served as text/html, which is not a valid robots.txt or sitemap.
    """
    lines = [
        'User-agent: *',
        'Allow: /',
        # Auth-gated demos - crawling them only reaches a login wall.
        'Disallow: /portal',
        'Disallow: /dashboard',
        'Disallow: /automations',
        'Disallow: /api/',
        'Disallow: /admin/',
        '',
        f'Sitemap: {SITE_ORIGIN}/sitemap.xml',
        '',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


def sitemap_xml(request):
    """Serve a real sitemap.xml covering public routes and published posts."""
    entries = [
        {'loc': f'{SITE_ORIGIN}{path}', 'priority': priority, 'changefreq': freq}
        for path, priority, freq in PUBLIC_ROUTES
    ]

    # Published blog posts. Wrapped defensively: a sitemap should degrade to the
    # static routes rather than 500 if the blog tables or Supabase are unhappy.
    try:
        from apps.blog.models import Post

        posts = Post.objects.filter(published=True).only('slug', 'updated_at')
        for post in posts:
            entries.append({
                'loc': f'{SITE_ORIGIN}/blog/{post.slug}',
                'priority': '0.6',
                'changefreq': 'yearly',
                'lastmod': post.updated_at.date().isoformat() if post.updated_at else None,
            })
    except Exception:  # noqa: BLE001 - never let the blog break discovery
        pass

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for entry in entries:
        xml.append('  <url>')
        xml.append(f'    <loc>{escape(entry["loc"])}</loc>')
        if entry.get('lastmod'):
            xml.append(f'    <lastmod>{entry["lastmod"]}</lastmod>')
        xml.append(f'    <changefreq>{entry["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{entry["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    xml.append('')

    return HttpResponse('\n'.join(xml), content_type='application/xml; charset=utf-8')
