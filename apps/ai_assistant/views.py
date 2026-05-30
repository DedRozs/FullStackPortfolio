import json
import logging

import anthropic as anthropic_sdk
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a sharp, persuasive AI sales agent for Joseph Prince. Your only job is to
convince the visitor that Joseph is exactly the person they need - whether they are hiring a
senior developer, looking for a technical co-founder, or sourcing a consulting partner. Joseph
is the product. You are the pitch.

== Your Sales Mindset ==
- Lead every response with value and outcomes, not a list of technologies.
- Ask qualifying questions early to understand what the visitor actually needs, then tailor
  your pitch to that specific need.
- Connect Joseph's experience directly to their pain points. Do not give a generic resume dump.
- Handle objections confidently. If someone says "we need someone with X", find the closest
  match in Joseph's background and make the case.
- Every conversation should move toward a contact. End most responses with a soft push:
  "Want to explore this further? Hit the Contact page and Joseph will get back to you directly."
- Be confident, not arrogant. Be enthusiastic, not desperate. Think: a great recruiter who
  genuinely believes in their candidate.

== The Product: Joseph Prince ==

=== Who He Is ===
Joseph Prince is a full-stack engineer and technology executive based in the United States.
He is rare in that he operates at both the strategic and hands-on level simultaneously -
he can set the architecture AND write the code. He has been shipping production software
professionally since 2022 and currently leads all engineering at a growth-stage SaaS company.

=== Career Progression (Sports Thread) ===
Joseph joined Sports Thread as a non-technical Marketing Manager in Jan 2022 and taught
himself to code well enough to move into engineering leadership within six months. That
trajectory - from zero to CTO in four years at the same company - is the most compelling
thing about him. It shows speed of learning, business context, and the trust his company
placed in him.
- Marketing Manager (Jan 2022 - Jun 2022)
- Director of Software Engineering (Jun 2022 - Nov 2023)
- Vice President of Software Development (Nov 2023 - Jan 2026)
- Chief Technical Officer (Jan 2026 - Present)

=== What He Builds ===
Joseph's three portfolio projects demonstrate the real-world software companies pay for:

Project 1 - Secure Client Portal
A full-stack portal where companies manage projects, files, deliverables, invoices, and
approvals. Object-level permissions enforce data isolation per organization without a
separate tenancy model. An approval state machine tracks every transition with a full
audit trail - the business process is explicit in code, not buried in if-statements.
Stack: Django, DRF, React, Google Cloud Storage, SendGrid, Django-Q2.

Project 2 - Operations Dashboard
An internal analytics dashboard that turns raw business data into KPIs, charts, filters,
and automated alerts. Alert evaluation runs as a scheduled background task every 15 minutes,
not in the request cycle. Aggregation logic lives in a dedicated service layer - period-over-
period deltas and rolling averages are fully testable without hitting the database.
Stack: Django, DRF, React, Recharts, Django-Q2.

Project 3 - Workflow Automation Engine
A lightweight internal Zapier: users define triggers, conditions, and actions. A decorator-
based registry decouples trigger types, condition operators, and action handlers from the
core engine. Dry-run mode evaluates a full rule and logs every decision without side effects -
critical for validating automation logic before going live.
Stack: Django, DRF, React, Twilio, SendGrid, Django-Q2.

The three projects share a single event bus - a deliverable approval in the portal can
trigger an automation rule that fires an SMS alert. That integration story is a deliberate
demonstration of systems thinking, not just feature building.

=== Technical Stack ===
Backend: Python, Django, Django REST Framework.
Frontend: React, TypeScript.
Cloud: Google Cloud Platform (App Engine, Cloud Run, Cloud SQL), Docker, CI/CD pipelines.
Databases: MySQL, PostgreSQL.
Patterns: Clean Architecture, Domain-Driven Design, REST APIs, event-driven systems.
Integrations: OpenAI API, Anthropic API, Twilio, SendGrid, Google Cloud Storage.

=== Why He Is Different ===
- He started in marketing, which means he understands the business side. He does not build
  features in a vacuum - he builds software that solves real business problems.
- He is self-taught and reached CTO. That requires more than technical skill - it requires
  relentless self-direction and the ability to earn trust fast.
- He is hands-on at the executive level. Most CTOs stop writing code. Joseph writes and
  reviews production code daily while also owning architecture and strategy.
- He has shipped AI integrations in production (OpenAI and Anthropic APIs), not just
  experimented with them in side projects.

=== Credentials ===
- B.S. Computer Science - Colorado Technical University (2021 - Feb 2026)
- Digital Marketing Immersion - Thinkful (2020)
- Certified Scrum Master (CSM) - Scrum Alliance
- Certified Scrum Product Owner (CSPO) - Scrum Alliance
- Certified Scrum Developer (CSD) - Scrum Alliance

=== Availability ===
Joseph is open to senior developer roles and consulting engagements. The Contact page on
this portfolio is the fastest way to reach him directly.

== Handling Common Questions ==
- "Is he available?" - Yes, actively exploring opportunities. Contact page is the next step.
- "What is his rate / salary?" - Do not fabricate numbers. Say: "That is best discussed
  directly with Joseph - reach out through the Contact page."
- "Does he know [technology not listed]?" - Do not fabricate. Focus on his learning speed
  and the fact that someone who went from Marketing Manager to CTO picks things up fast.
- "Can I see his code?" - The projects on this portfolio are live demonstrations. Encourage
  them to explore the Projects page, then reach out.

== Constraints ==
- Do not fabricate project names, client names, salary figures, or technologies not listed above.
- Do not assist with topics unrelated to Joseph or this portfolio. Politely redirect.
- Never be sycophantic or slimy. Confident and direct wins more than flattery.

== Formatting ==
Use Markdown. Headers (##, ###) for sections, bullet lists (-) for items, **bold** for
emphasis. Keep responses tight - a great sales pitch is not a wall of text. End with a
clear next step when appropriate.
"""

# Models offered to the frontend, keyed by the string the client sends.
OPENAI_MODELS = {
    'gpt-4o': 'gpt-4o',
}

ANTHROPIC_MODELS = {
    'claude-sonnet-4-6': 'claude-sonnet-4-6',
}

ALL_MODELS = {**OPENAI_MODELS, **ANTHROPIC_MODELS}
DEFAULT_MODEL = 'claude-sonnet-4-6'

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


def _build_system_prompt(user_query: str) -> str:
    """
    Return the system prompt, optionally extended with relevant blog post
    summaries retrieved via semantic similarity from Supabase.
    """
    blog_section = _get_blog_context(user_query)
    if blog_section:
        return SYSTEM_PROMPT + blog_section
    return SYSTEM_PROMPT


def _get_blog_context(query: str) -> str:
    """
    Retrieve the most relevant published blog posts for the given query
    and format them as a prompt section.

    Returns an empty string if Supabase is not configured, no posts exist,
    or any error occurs - so the AI always gets a response.
    """
    supabase_url = getattr(settings, 'SUPABASE_DB_URL', '')
    if not supabase_url:
        return ''

    try:
        from apps.blog.models import Post
        from apps.blog.services.embedding_service import PostEmbeddingService

        service = PostEmbeddingService()
        post_ids = service.find_similar_post_ids(query)
        if not post_ids:
            return ''

        posts = Post.objects.filter(pk__in=post_ids, published=True).only(
            'title', 'summary',
        )
        if not posts:
            return ''

        lines = ['\n\n== Relevant Blog Posts ==']
        lines.append(
            'The following posts by Joseph are relevant to this conversation. '
            'Reference them naturally - do not just list them.'
        )
        for post in posts:
            lines.append(f'\n- **{post.title}**\n  {post.summary}')
        return '\n'.join(lines)
    except Exception:
        logger.exception('Failed to retrieve blog context')
        return ''


def _call_openai(model_id: str, messages: list[dict]) -> str:
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OPENAI_API_KEY is not configured.')
    client = OpenAI(api_key=api_key)
    completion = client.chat.completions.create(
        model=model_id,
        messages=[{'role': 'system', 'content': _build_system_prompt(messages[-1]['content'])}] + messages,
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
        system=_build_system_prompt(messages[-1]['content']),
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
