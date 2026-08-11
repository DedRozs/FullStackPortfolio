import hashlib
import json
import os
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string


TEMPLATE_NAME = 'react_app/resume_pdf.html'

# Outside static/react_app: Vite empties that directory on every frontend build.
GENERATED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'generated',
)
ASSET_PATH = os.path.join(GENERATED_DIR, 'joseph-prince-resume.pdf')

# Records what the committed PDF was built from. The freshness test in
# apps/react_app/tests.py re-renders the template, re-hashes it, and fails if
# either hash drifts - so editing resume_pdf.html without regenerating the PDF
# breaks CI instead of silently shipping a stale download. The check needs only
# Django (no ironpdf), which is why it can run in CI at all.
MANIFEST_PATH = os.path.join(GENERATED_DIR, 'resume-pdf.manifest.json')


def render_source() -> str:
    """Render the resume template. Shared with the freshness test."""
    # SafeString.__str__ returns self, so str() cannot strip it; encode/decode
    # forces a plain str, which the pythonnet bridge requires.
    return render_to_string(TEMPLATE_NAME).encode('utf-8').decode('utf-8')


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Command(BaseCommand):
    help = (
        'Render the resume HTML template to a PDF and write it to static assets. '
        'Local only: needs `pip install -r requirements-dev.txt` (ironpdf). '
        'Commit the regenerated PDF - the server streams the committed file.'
    )

    def handle(self, *args, **options):
        # Deferred so this module stays importable without ironpdf installed,
        # which is why it can live in requirements-dev.txt rather than
        # requirements.txt. Django imports every command module on startup.
        try:
            from ironpdf import ChromePdfRenderer, License
        except ImportError as exc:
            raise SystemExit(
                'ironpdf is not installed. It is a local-only dependency:\n'
                '    pip install -r requirements-dev.txt'
            ) from exc

        License.LicenseKey = os.environ.get('IRON_PDF_KEY', '')

        html = render_source()

        renderer = ChromePdfRenderer()
        renderer.RenderingOptions.MarginTop = 0
        renderer.RenderingOptions.MarginBottom = 0
        renderer.RenderingOptions.MarginLeft = 0
        renderer.RenderingOptions.MarginRight = 0

        pdf = renderer.RenderHtmlAsPdf(html)

        os.makedirs(GENERATED_DIR, exist_ok=True)
        # SaveAs writes from the .NET side, avoiding lossy BinaryData marshaling.
        pdf.SaveAs(ASSET_PATH)

        size = os.path.getsize(ASSET_PATH)
        if size == 0:
            self.stderr.write(self.style.ERROR('Generated PDF is empty.'))
            raise SystemExit(1)

        # Write the manifest last: if rendering fails above, a stale manifest is
        # better than one that claims a PDF which was never written.
        manifest = {
            'template': TEMPLATE_NAME,
            'source_sha256': sha256_text(html),
            'pdf_sha256': sha256_file(ASSET_PATH),
            'pdf_bytes': size,
            'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        }
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as handle:
            json.dump(manifest, handle, indent=2, sort_keys=True)
            handle.write('\n')

        self.stdout.write(self.style.SUCCESS(f'PDF written to {ASSET_PATH} ({size} bytes)'))
        self.stdout.write(f'Manifest written to {MANIFEST_PATH}')
        self.stdout.write(
            self.style.WARNING('Commit both files - CI fails if they drift from the template.')
        )
