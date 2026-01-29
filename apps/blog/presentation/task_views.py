"""
HTTP endpoints for scheduled tasks triggered by GAE Cron.

These views execute long-running tasks directly (not via Django Q).
GAE Cron has a 10-minute timeout, which is sufficient for blog generation.
"""
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.blog.application.content_generation.tasks import (
    generate_daily_ideas,
    process_pending_idea,
    cleanup_old_ideas,
    health_check,
)


def verify_cron_request(request):
    """
    Verify request is from GAE Cron (has X-Appengine-Cron header).
    
    In production, GAE adds this header which can't be spoofed externally.
    In development, we'll allow it through.
    """
    from django.conf import settings
    
    if settings.DEBUG:
        return True
    
    return request.META.get('HTTP_X_APPENGINE_CRON') == 'true'


@method_decorator(csrf_exempt, name='dispatch')
class GenerateIdeasTaskView(View):
    """Generate blog post ideas (triggered by cron)."""
    
    def post(self, request):
        if not verify_cron_request(request):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            result = generate_daily_ideas()
            return JsonResponse({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class PublishBlogTaskView(View):
    """Process and publish a pending blog post (triggered by cron)."""
    
    def post(self, request):
        if not verify_cron_request(request):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            result = process_pending_idea()
            return JsonResponse({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class CleanupIdeasTaskView(View):
    """Cleanup old blog ideas (triggered by cron)."""
    
    def post(self, request):
        if not verify_cron_request(request):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            result = cleanup_old_ideas()
            return JsonResponse({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckTaskView(View):
    """Health check for content pipeline (triggered by cron)."""
    
    def post(self, request):
        if not verify_cron_request(request):
            return JsonResponse({'error': 'Unauthorized'}, status=403)
        
        try:
            result = health_check()
            return JsonResponse({
                'status': 'success',
                'result': result
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'error': str(e)
            }, status=500)
