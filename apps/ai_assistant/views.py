import json
import logging

import anthropic as anthropic_sdk
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI assistant representing Joseph Prince, a Full Stack Developer and
technology leader based in the United States.

== Background ==
Joseph is currently the Chief Technology Officer at Sports Thread (2023 - Present), where he
owns architecture, scalability, and security across the full platform. He sets technical direction,
leads engineering execution, and remains hands-on writing and reviewing production code.
Previously he held the roles of VP of Engineering (2022-2023) and Director of Engineering
(2021-2022) at the same company.

== Technical Stack ==
Primary languages and frameworks: Python, Django, React, TypeScript.
Infrastructure and cloud: Google Cloud Platform (App Engine, Cloud Run, Cloud SQL), Docker, CI/CD.
Databases: MySQL, PostgreSQL.
Patterns and practices: Clean Architecture, Domain-Driven Design, REST APIs, event-driven systems.
Integrations: OpenAI API, Anthropic API, Twilio, SendGrid, Google Cloud Storage.

== Credentials ==
- B.S. Computer Science (Data Science) - Colorado Technical University
- Certified Scrum Master (CSM) - Scrum Alliance
- Certified Scrum Product Owner (CSPO) - Scrum Alliance
- Certified Scrum Developer (CSD) - Scrum Alliance

== Availability ==
Joseph is open to senior developer roles and consulting engagements. The best way to reach him
is through the Contact page on this portfolio site.

== Instructions ==
Answer questions about Joseph's background, skills, experience, projects, and availability.
Keep responses concise and professional. If asked about something outside Joseph's background
or this portfolio, politely redirect the conversation back to relevant topics.
Do not fabricate specific project names, client names, or salary figures that are not provided above.

== Formatting ==
Format all responses using Markdown. Use headers (##, ###) for sections, bullet lists (-) for
enumerated items, and **bold** for emphasis. Always use proper block-level list syntax with each
item on its own line - never inline dashes as separators. Keep responses well-structured and
easy to scan.
"""

# Models offered to the frontend, keyed by the string the client sends.
OPENAI_MODELS = {
    'gpt-4o': 'gpt-4o',
}

ANTHROPIC_MODELS = {
    'claude-sonnet-4-6': 'claude-sonnet-4-6',
}

ALL_MODELS = {**OPENAI_MODELS, **ANTHROPIC_MODELS}
DEFAULT_MODEL = 'gpt-4o'

MAX_MESSAGES = 20
MAX_CONTENT_LENGTH = 2000
MAX_TOKENS = 500


def _is_valid_message(msg: object) -> bool:
    """Return True if msg is a dict with an allowed role and a non-empty string content."""
    if not isinstance(msg, dict):
        return False
    if msg.get('role') not in ('user', 'assistant'):
        return False
    content = msg.get('content', '')
    return isinstance(content, str) and 0 < len(content.strip()) <= MAX_CONTENT_LENGTH


def _call_openai(model_id: str, messages: list[dict]) -> str:
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OPENAI_API_KEY is not configured.')
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model_id,
        messages=[{'role': 'system', 'content': SYSTEM_PROMPT}] + messages,
        max_tokens=MAX_TOKENS,
        temperature=0.7,
    )
    return completion.choices[0].message.content or ''


def _call_anthropic(model_id: str, messages: list[dict]) -> str:
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY is not configured.')
    client = anthropic_sdk.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model_id,
        system=SYSTEM_PROMPT,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )
    return response.content[0].text if response.content else ''


@csrf_exempt
@require_POST
def chat(request):
    """Accept a conversation history and a model choice; return the next assistant reply."""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    raw_messages = body.get('messages', [])
    model_key = body.get('model', DEFAULT_MODEL)

    if not isinstance(raw_messages, list) or not raw_messages:
        return JsonResponse({'error': 'messages must be a non-empty list.'}, status=400)

    if len(raw_messages) > MAX_MESSAGES:
        return JsonResponse(
            {'error': f'Conversation exceeds the {MAX_MESSAGES}-message limit.'},
            status=400,
        )

    if not all(_is_valid_message(m) for m in raw_messages):
        return JsonResponse({'error': 'One or more messages are malformed.'}, status=400)

    if model_key not in ALL_MODELS:
        return JsonResponse({'error': f'Unknown model "{model_key}".'}, status=400)

    normalized = [{'role': m['role'], 'content': m['content'].strip()} for m in raw_messages]
    model_id = ALL_MODELS[model_key]

    try:
        if model_key in OPENAI_MODELS:
            reply = _call_openai(model_id, normalized)
        else:
            reply = _call_anthropic(model_id, normalized)
    except ValueError as exc:
        logger.error('%s', exc)
        return JsonResponse({'error': 'AI service is not configured.'}, status=503)
    except (OpenAIError, anthropic_sdk.APIError) as exc:
        logger.exception('AI provider error: %s', exc)
        return JsonResponse({'error': 'AI service request failed.'}, status=502)

    return JsonResponse({'reply': reply, 'model': model_key})
