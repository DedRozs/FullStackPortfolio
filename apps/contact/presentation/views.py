"""API views for the Contact bounded context.

Views handle HTTP concerns and delegate to application services.
They should be thin - no business logic here.
"""
import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.contact.application.commands import CreateContactMessageCommand
from apps.contact.application.queries import GetAllMessagesQuery
from apps.contact.application.services import ContactApplicationService, ContactMessageDTO
from apps.contact.infrastructure.repositories import DjangoContactMessageRepository
from apps.shared.infrastructure.event_bus import get_event_bus


def get_contact_service() -> ContactApplicationService:
    """Factory function for dependency injection.
    
    In a larger app, use a proper DI container.
    """
    return ContactApplicationService(
        repository=DjangoContactMessageRepository(),
        event_bus=get_event_bus(),
    )


@method_decorator(csrf_exempt, name='dispatch')
class ContactMessageListView(View):
    """API endpoint for contact messages."""
    
    def get(self, request) -> JsonResponse:
        """List all messages (admin use)."""
        service = get_contact_service()
        query = GetAllMessagesQuery()
        messages = service.get_all_messages(query)
        
        return JsonResponse({
            'messages': [ContactMessageDTO.from_entity(m).__dict__ for m in messages]
        })
    
    def post(self, request) -> JsonResponse:
        """Create a new contact message."""
        try:
            data = json.loads(request.body)
            
            command = CreateContactMessageCommand(
                name=data.get('name', ''),
                email=data.get('email', ''),
                message=data.get('message', ''),
            )
            
            service = get_contact_service()
            message_id = service.create_message(command)
            
            return JsonResponse({
                'success': True,
                'message_id': str(message_id),
            }, status=201)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
            }, status=400)
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON',
            }, status=400)
