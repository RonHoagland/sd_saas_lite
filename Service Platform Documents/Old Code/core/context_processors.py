"""
Context processors for core app.

Makes key preferences available to all templates.
"""
from core.models import Preference


def branding(request):
    """Inject branding preferences into every template context."""
    logo_url = ''
    ui_theme_color = None
    try:
        # Logo
        pref = Preference.objects.filter(key='company_logo_digital').first()
        if pref and pref.value:
            logo_url = pref.value
            
        # Theme Color
        color_pref = Preference.objects.filter(key='ui_theme_color').first()
        if color_pref and color_pref.value:
            ui_theme_color = color_pref.value
            
    except Exception:
        pass

    return {
        'logo_url': logo_url,
        'ui_theme_color': ui_theme_color,
    }
