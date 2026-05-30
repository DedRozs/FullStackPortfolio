from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def index(request):
    """Serve the React SPA shell. React Router handles all client-side routing."""
    return render(request, 'react_app/index.html')
