import os

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string


# Outside static/react_app: Vite empties that directory on every frontend build.
ASSET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    'generated', 'joseph-prince-resume.pdf',
)


class Command(BaseCommand):
    help = 'Render the resume HTML template to a PDF and write it to static assets.'

    def handle(self, *args, **options):
        from ironpdf import ChromePdfRenderer, License

        License.LicenseKey = os.environ.get('IRON_PDF_KEY', '')

        # SafeString.__str__ returns self, so str() cannot strip it; encode/decode
        # forces a plain str, which the pythonnet bridge requires.
        html = render_to_string('react_app/resume_pdf.html').encode('utf-8').decode('utf-8')

        renderer = ChromePdfRenderer()
        renderer.RenderingOptions.MarginTop = 0
        renderer.RenderingOptions.MarginBottom = 0
        renderer.RenderingOptions.MarginLeft = 0
        renderer.RenderingOptions.MarginRight = 0

        pdf = renderer.RenderHtmlAsPdf(html)

        os.makedirs(os.path.dirname(ASSET_PATH), exist_ok=True)
        # SaveAs writes from the .NET side, avoiding lossy BinaryData marshaling.
        pdf.SaveAs(ASSET_PATH)

        size = os.path.getsize(ASSET_PATH)
        if size == 0:
            self.stderr.write(self.style.ERROR('Generated PDF is empty.'))
            raise SystemExit(1)

        self.stdout.write(self.style.SUCCESS(f'PDF written to {ASSET_PATH} ({size} bytes)'))
