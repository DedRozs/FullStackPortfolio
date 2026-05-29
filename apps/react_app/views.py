from django.shortcuts import render


def index(request):
    """Serve the React SPA shell. React Router handles all client-side routing."""
    return render(request, 'react_app/index.html')
