"""Guards for the pre-generated resume PDF.

The PDF at apps/react_app/generated/ is built locally by
`manage.py generate_resume_pdf` (which needs ironpdf, a requirements-dev.txt
dependency) and committed. The server only ever streams that committed file.

That creates a silent failure mode: edit resume_pdf.html, forget to regenerate,
and the web page at /resume looks right while the downloadable PDF is stale.
Nothing surfaces it - recruiters just get the old version.

These tests close that gap using hashes recorded in the manifest at generation
time, so they need only Django. No ironpdf, which is what lets them run in CI.
"""
import json
import os
import re

from django.test import TestCase
from django.urls import reverse

from apps.react_app.management.commands.generate_resume_pdf import (
    ASSET_PATH,
    MANIFEST_PATH,
    TEMPLATE_NAME,
    render_source,
    sha256_file,
    sha256_text,
)

REGENERATE = (
    'Run `python manage.py generate_resume_pdf` and commit both '
    'the PDF and the manifest.'
)


class ResumePdfFreshnessTests(TestCase):
    """Fail loudly when the committed PDF no longer matches the template."""

    def setUp(self):
        if not os.path.exists(MANIFEST_PATH):
            self.fail(f'Missing manifest: {MANIFEST_PATH}. {REGENERATE}')
        with open(MANIFEST_PATH, encoding='utf-8') as handle:
            self.manifest = json.load(handle)

    def test_pdf_asset_exists_and_is_a_pdf(self):
        self.assertTrue(
            os.path.exists(ASSET_PATH), f'Missing PDF: {ASSET_PATH}. {REGENERATE}'
        )
        with open(ASSET_PATH, 'rb') as handle:
            self.assertEqual(
                handle.read(5), b'%PDF-', 'Committed asset is not a valid PDF.'
            )

    def test_manifest_records_the_expected_template(self):
        self.assertEqual(self.manifest.get('template'), TEMPLATE_NAME)

    def test_template_has_not_changed_since_the_pdf_was_generated(self):
        """The important one: catches an edited template with a stale PDF."""
        current = sha256_text(render_source())
        self.assertEqual(
            current,
            self.manifest.get('source_sha256'),
            f'{TEMPLATE_NAME} has changed since the PDF was generated, so the '
            f'downloadable PDF is stale. {REGENERATE}',
        )

    def test_committed_pdf_matches_the_manifest(self):
        """Catches a PDF swapped or corrupted without regenerating the manifest."""
        self.assertEqual(
            sha256_file(ASSET_PATH),
            self.manifest.get('pdf_sha256'),
            f'The committed PDF does not match its manifest hash. {REGENERATE}',
        )


class ResumePdfViewTests(TestCase):
    """The endpoint that serves the PDF."""

    def test_serves_pdf_as_an_attachment(self):
        response = self.client.get(reverse('resume_pdf'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('joseph-prince-resume.pdf', response['Content-Disposition'])
        response.close()

    def test_pdf_route_is_not_swallowed_by_the_spa_catch_all(self):
        """core/urls.py registers this before the `^.*$` SPA route - keep it that way."""
        response = self.client.get('/resume/pdf/')
        self.assertEqual(response['Content-Type'], 'application/pdf')
        response.close()


class CrawlerFileTests(TestCase):
    """robots.txt and sitemap.xml.

    These previously fell through to the SPA catch-all and were served as
    text/html with a 200 status - which looks fine to a status-code check but
    means the site had no robots.txt and no sitemap at all. Assert on
    content-type and body, never on the status code alone.
    """

    def test_robots_is_plain_text_not_the_spa_shell(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('text/plain'))
        body = response.content.decode()
        self.assertNotIn('<!DOCTYPE html>', body)
        self.assertIn('User-agent: *', body)

    def test_robots_advertises_the_sitemap(self):
        body = self.client.get('/robots.txt').content.decode()
        self.assertIn('Sitemap: https://www.thejosephprince.com/sitemap.xml', body)

    def test_robots_excludes_auth_gated_demo_routes(self):
        body = self.client.get('/robots.txt').content.decode()
        for path in ('/portal', '/dashboard', '/automations'):
            self.assertIn(f'Disallow: {path}', body)

    def test_sitemap_is_xml_not_the_spa_shell(self):
        response = self.client.get('/sitemap.xml')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Type'].startswith('application/xml'))
        body = response.content.decode()
        self.assertNotIn('<!DOCTYPE html>', body)
        self.assertTrue(body.startswith('<?xml version="1.0"'))

    def test_sitemap_is_wellformed_and_lists_public_routes(self):
        import xml.etree.ElementTree as ET

        body = self.client.get('/sitemap.xml').content.decode()
        root = ET.fromstring(body)  # raises if malformed
        ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        locs = {el.text for el in root.findall('.//s:loc', ns)}

        for path in ('/', '/projects', '/about', '/resume', '/blog'):
            self.assertIn(f'https://www.thejosephprince.com{path}', locs)

    def test_sitemap_omits_auth_gated_routes(self):
        body = self.client.get('/sitemap.xml').content.decode()
        for path in ('/portal', '/dashboard', '/automations'):
            self.assertNotIn(f'https://www.thejosephprince.com{path}<', body)


class StructuredDataTests(TestCase):
    """The Person schema is the main lever against the namesake collision."""

    def test_person_schema_carries_disambiguating_fields(self):
        import json
        import re

        html = self.client.get('/').content.decode()
        blocks = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S
        )
        self.assertTrue(blocks, 'No JSON-LD block found.')

        graph = json.loads(blocks[0])['@graph']  # raises if the JSON is invalid
        person = next(n for n in graph if n['@type'] == 'Person')

        self.assertIn('knowsAbout', person)
        self.assertIn('Django', person['knowsAbout'])
        self.assertIn('worksFor', person)
        self.assertIn('alumniOf', person)
        self.assertIn('address', person)

    def test_title_carries_technical_qualifiers(self):
        html = self.client.get('/').content.decode()
        title = re.search(r'<title>(.*?)</title>', html, re.S).group(1)
        self.assertIn('Software Engineer', title)
        # A bare "Joseph Prince | Full Stack Developer" loses to the namesake.
        self.assertTrue(any(t in title for t in ('Python', 'Django')))
