from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import UserTransaction, Session
from core.utils import apply_sorting

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def audit_log_view(request):
    logs = UserTransaction.objects.all().select_related('user', 'session')
    
    # Sorting
    logs, sort_field, sort_dir = apply_sorting(
        logs,
        request,
        allowed_fields=['event_ts', 'user__username', 'event_type', 'entity_type', 'summary'],
        default_sort='event_ts',
        default_dir='desc'
    )
    
    return render(request, "audit/activity_log.html", {
        "logs": logs,
        "current_sort": sort_field,
        "current_dir": sort_dir
    })
