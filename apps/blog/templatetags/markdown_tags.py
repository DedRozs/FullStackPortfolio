"""
Markdown rendering for post bodies.

Rendering is a presentation concern, so it lives in the template layer rather
than in the domain or application layers - those stay free of Markdown, Django,
and every other framework dependency.
"""

from __future__ import annotations

import re
from html import escape
from xml.etree.ElementTree import Element  # noqa: F401  (documents the tree API in use)

import markdown
from django import template
from django.utils.safestring import mark_safe
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

register = template.Library()

_MERMAID_OPEN = re.compile(r'^\s*```+\s*mermaid\s*$', re.IGNORECASE)
_FENCE_CLOSE = re.compile(r'^\s*```+\s*$')


class _MermaidPreprocessor(Preprocessor):
    """Turn ```mermaid fences into <pre class="mermaid"> before highlighting.

    codehilite claims every fenced block and rewrites it into a .codehilite
    wrapper, discarding the language class. Diagrams have to be recognisable in
    the final HTML, so they are lifted out first and stashed as raw HTML.
    """

    def run(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(lines):
            if not _MERMAID_OPEN.match(lines[i]):
                out.append(lines[i])
                i += 1
                continue
            i += 1
            body: list[str] = []
            while i < len(lines) and not _FENCE_CLOSE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1  # consume the closing fence
            diagram = escape('\n'.join(body))
            out.append(self.md.htmlStash.store(f'<pre class="mermaid">{diagram}</pre>'))
        return out


class MermaidExtension(Extension):
    def extendMarkdown(self, md) -> None:
        # Ahead of fenced_code (25) so codehilite never sees these blocks.
        md.preprocessors.register(_MermaidPreprocessor(md), 'mermaid_blocks', 30)


# fenced_code + codehilite give Pygments-highlighted code blocks; mermaid fences
# are intercepted earlier by MermaidExtension and never reach the highlighter.
_EXTENSIONS = [
    MermaidExtension(),
    'markdown.extensions.fenced_code',
    'markdown.extensions.codehilite',
    'markdown.extensions.tables',
    'markdown.extensions.toc',
    'markdown.extensions.attr_list',
    'markdown.extensions.sane_lists',
    'markdown.extensions.smarty',
]

_EXTENSION_CONFIGS = {
    'markdown.extensions.codehilite': {
        # Emit CSS classes instead of inline styles so the theme lives in the
        # stylesheet, and never abort rendering over an unknown language.
        'noclasses': False,
        'guess_lang': False,
        'pygments_style': 'monokai',
    },
    'markdown.extensions.toc': {
        'permalink': False,
    },
}


@register.filter(name='render_markdown')
def render_markdown(value: str | None) -> str:
    """Render a Markdown post body to HTML.

    The only authors are staff writing through the admin, so raw HTML in a post
    body is authored content rather than untrusted input and is passed through.
    """
    if not value:
        return ''
    html = markdown.markdown(
        value,
        extensions=_EXTENSIONS,
        extension_configs=_EXTENSION_CONFIGS,
        output_format='html',
    )
    return mark_safe(html)
