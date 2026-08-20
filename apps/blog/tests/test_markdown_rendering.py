"""
Unit tests for the Markdown rendering filter. No database, no HTTP.
"""
import pytest

from apps.blog.templatetags.markdown_tags import render_markdown


@pytest.mark.parametrize('value', ['', None])
def test_empty_input_renders_nothing(value):
    assert render_markdown(value) == ''


def test_headings_and_emphasis_become_html():
    html = render_markdown('## A heading\n\nSome **bold** text.')
    assert '<h2' in html
    assert '<strong>bold</strong>' in html
    assert '##' not in html


def test_fenced_python_is_syntax_highlighted():
    html = render_markdown('```python\nx = 1\n```')
    assert 'codehilite' in html


def test_mermaid_fence_becomes_a_mermaid_pre_block():
    """The client renderer finds diagrams by this exact shape."""
    html = render_markdown('```mermaid\nflowchart TD\n  A --> B\n```')
    assert '<pre class="mermaid">' in html
    assert 'flowchart TD' in html
    # It must not be claimed by the syntax highlighter.
    assert 'codehilite' not in html


def test_mermaid_arrows_are_escaped_not_treated_as_markup():
    html = render_markdown('```mermaid\nflowchart TD\n  A --> B\n```')
    assert '--&gt;' in html


def test_a_mermaid_block_and_a_code_block_coexist():
    html = render_markdown(
        '```mermaid\nflowchart TD\n  A --> B\n```\n\n```python\nx = 1\n```'
    )
    assert '<pre class="mermaid">' in html
    assert 'codehilite' in html


def test_tables_render():
    html = render_markdown('| Gate | Passes when |\n| --- | --- |\n| 1 | Validated |')
    assert '<table>' in html
    assert '<td>Validated</td>' in html


def test_blockquotes_render():
    assert '<blockquote>' in render_markdown('> quoted claim')


def test_output_is_marked_safe_so_templates_do_not_double_escape():
    from django.utils.safestring import SafeString

    assert isinstance(render_markdown('plain'), SafeString)
