import os

from django.http import FileResponse, Http404
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


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
