"""Template helpers for ServizDesk UI block partials.

These are small utilities the block partials (templates/blocks/_*.html)
depend on. Load with `{% load sd_ui %}` at the top of any template that
needs them.
"""
from django import template

register = template.Library()


@register.filter(name='lookup')
def lookup(d, key):
    """Look up a value in a dict by a dynamic key.

    Django templates can't do `{{ dict[variable] }}` natively. Used by the
    List Block partial to pull a row's column value when iterating columns
    by their `key`.
    """
    if d is None:
        return ''
    try:
        return d[key]
    except (KeyError, TypeError):
        return getattr(d, key, '')


@register.filter(name='sd_accent_css')
def sd_accent_css(value):
    """Convert a §3.1 accent token (or raw hex escape hatch) to a CSS color expression.

    Token names map to the universal accent palette via `--sd-accent-<token>`
    custom properties defined in site.css. Raw hex values pass through as-is.

    Examples:
        sd_accent_css('warning') -> 'var(--sd-accent-warning)'
        sd_accent_css('#a855f7') -> '#a855f7'
        sd_accent_css(None)      -> 'var(--sd-accent-brand)'
    """
    if not value:
        return 'var(--sd-accent-brand)'
    if value.startswith('#'):
        return value
    return f'var(--sd-accent-{value})'
