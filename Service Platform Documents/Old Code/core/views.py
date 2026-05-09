from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden
import os
from .models import Preference
from django.conf import settings


@login_required
def dashboard_view(request):
    """
    Main dashboard view for the core application.
    """
    # Compute local date using user's timezone preference
    from datetime import datetime, timezone as dt_timezone
    import zoneinfo
    
    try:
        tz_pref = Preference.objects.filter(key='l10n_timezone').first()
        if tz_pref and tz_pref.value:
            local_tz = zoneinfo.ZoneInfo(tz_pref.value)
        else:
            local_tz = zoneinfo.ZoneInfo('America/Chicago')
    except Exception:
        local_tz = dt_timezone.utc
    
    local_now = datetime.now(dt_timezone.utc).astimezone(local_tz)
    today_date = local_now.strftime('%A, %B ') + _ordinal(local_now.day) + local_now.strftime(', %Y')
    
    context = {
        # Placeholder data for future widgets
        "recent_items": [],
        "notifications": [],
        "today_date": today_date,
    }

    # System Health Check: Verify Critical Paths
    path_prefs = Preference.objects.filter(data_type='path')
    for p in path_prefs:
        path_value = p.value
        if path_value:
            # Resolve MEDIA_URL to MEDIA_ROOT for existence check
            if path_value.startswith(settings.MEDIA_URL):
                # Remove MEDIA_URL prefix and prepend MEDIA_ROOT
                rel_path = path_value[len(settings.MEDIA_URL):]
                # Handle potential leading slash in rel_path
                if rel_path.startswith('/'):
                    rel_path = rel_path[1:]
                check_path = os.path.join(settings.MEDIA_ROOT, rel_path)
            else:
                check_path = path_value
                
            if not os.path.exists(check_path):
                context['notifications'].append({
                    'level': 'danger', 
                    'message': f"Critical Path Missing: {p.name} ({path_value}) does not exist on the server."
                })

    return render(request, "core/dashboard.html", context)


def _ordinal(n):
    """Return day with ordinal suffix (1st, 2nd, 3rd, etc.)."""
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_home_view(request):
    """
    Landing page for the custom Administration Area.
    """
    return render(request, "core/admin_home.html")

from .models import Preference
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def preference_list_view(request):
    preferences = Preference.objects.filter(is_active=True).order_by('preference_group', 'name')
    
    # Dynamic Grouping based on the restored 'preference_group' field
    grouped_prefs = {}
    
    # Define standard order for known groups
    group_order = ['General', 'Localization', 'Branding', 'Security', 'System']
    
    # Initialize ordered groups
    for g in group_order:
        grouped_prefs[g] = []
        
    for p in preferences:
        group = p.preference_group or 'Other'
        if group not in grouped_prefs:
            grouped_prefs[group] = []
        grouped_prefs[group].append(p)
             
    # Clean up empty groups
    grouped_prefs = {k: v for k, v in grouped_prefs.items() if v}
    
    return render(request, "core/preference_list.html", {"grouped_preferences": grouped_prefs})

from .constants import COUNTRY_DEFAULTS
from django.core.files.storage import default_storage

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def preference_update_view(request, pk):
    pref = get_object_or_404(Preference, pk=pk)
    
    # SECURITY: Prevent editing sealed/locked preferences
    if not pref.is_editable or pref.is_locked:
        return HttpResponseForbidden("This preference is locked by system policy and cannot be edited.")
    
    # 1. Determine Input Type & Choices
    widget_type = 'text'
    choices = None
    
    # Use the restored 'input_type' field if available, fallback to data_type/key logic
    if pref.input_type == 'select' and pref.key == 'loc_default_country':
        widget_type = 'select'
        choices = [(k, v['name']) for k, v in COUNTRY_DEFAULTS.items()]
    
    elif pref.input_type == 'timezone' or pref.key == 'loc_timezone':
        widget_type = 'select'
        country_pref = Preference.objects.filter(key='loc_default_country').first()
        current_country = country_pref.value if country_pref else 'US'
        if current_country in COUNTRY_DEFAULTS:
             t_zones = COUNTRY_DEFAULTS[current_country]['timezones']
             choices = [(tz, tz) for tz in t_zones]
        else:
             choices = [(pref.value, pref.value)]
             
    elif pref.input_type == 'currency' or pref.key == 'finance_default_currency':
        widget_type = 'select'
        choices = [('USD', 'USD'), ('PHP', 'PHP'), ('EUR', 'EUR'), ('GBP', 'GBP')]
        
    elif pref.input_type == 'file_upload':
        widget_type = 'file'

    elif pref.input_type == 'textarea':
        widget_type = 'textarea'
        
    elif pref.data_type == 'boolean':
        widget_type = 'select'
        choices = [('true', 'Yes'), ('false', 'No')]
        
    elif pref.data_type == 'password' or pref.is_secret:
        widget_type = 'password'
        
    elif pref.data_type == 'path' and 'logo' in pref.key:
        widget_type = 'file'

    
    if request.method == "POST":
        new_value = request.POST.get('value')
        
        # Handle File Upload
        if widget_type == 'file' and request.FILES.get('value'):
             uploaded_file = request.FILES['value']
             # Save to logos directory
             path = default_storage.save(f'logos/{uploaded_file.name}', uploaded_file)
             new_value = default_storage.url(path)
        
        if new_value is not None:
            pref.value = new_value
            pref.save()
            
            # TRIGGER CASCADES
            if pref.key == 'loc_default_country' and new_value in COUNTRY_DEFAULTS:
                data = COUNTRY_DEFAULTS[new_value]
                # Update Currency
                Preference.objects.filter(key='finance_default_currency').update(value=data['currency'])
                Preference.objects.filter(key='finance_currency_symbol').update(value=data['symbol'])
                # Update Phone
                Preference.objects.filter(key='loc_default_phone_code').update(value=data['phone_code'])
                Preference.objects.filter(key='loc_default_phone_format').update(value=data['phone_format'])
                # Update Date
                Preference.objects.filter(key='loc_date_format').update(value=data['date_format'])
                # Update Timezone (Set to first one)
                if data['timezones']:
                     Preference.objects.filter(key='loc_timezone').update(value=data['timezones'][0])
                     
                messages.success(request, f"Country updated to {data['name']}. Related settings (Currency, Phone, Date, Timezone) auto-updated.")
            else:
                messages.success(request, f"Preference '{pref.name}' updated.")
                
            return redirect('preference_list')
            
    return render(request, "core/preference_form.html", {
        "pref": pref, 
        "widget_type": widget_type, 
        "choices": choices
    })
