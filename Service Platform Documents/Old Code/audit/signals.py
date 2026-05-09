from django.db.models.signals import post_save, post_delete, pre_save
from django.contrib.auth.signals import user_logged_in, user_login_failed, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.apps import apps
from django.conf import settings

from core.models import BaseModel, Preference
from backup.models import BackupSettings
from .models import UserTransaction, Session
from .middleware import get_current_user

# --- SESSION LOGGING (Login/Logout) ---

def get_client_ip(request):
    """Get IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    """Create session on successful login."""
    Session.objects.create(
        user=user,
        auth_result='success',
        ip_address=get_client_ip(request),
        client_info=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_login_failed)
def log_user_login_failed(sender, credentials, request, **kwargs):
    """Create session on failed login."""
    Session.objects.create(
        attempted_username=credentials.get('username', ''),
        auth_result='failure',
        auth_failure_reason='Invalid credentials', # Generic reason for now
        ip_address=get_client_ip(request),
        client_info=request.META.get('HTTP_USER_AGENT', '')
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    """End session on logout."""
    if not user: return
    
    # Find active session
    session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
    if session:
        session.ended_at = timezone.now()
        session.end_reason = 'logout'
        session.save()


# Models to exclude from generic audit logging to reduce noise
EXCLUDED_MODELS = [
    'audit.UserTransaction',
    'audit.Session',
    'admin.LogEntry',
    'sessions.Session',
    'contenttypes.ContentType',
    'auth.Permission',
]

def should_audit_model(sender):
    """Check if model should be audited."""
    # Only audit models inheriting from BaseModel (our standard)
    if not issubclass(sender, BaseModel):
        return False
        
    label = f"{sender._meta.app_label}.{sender.__name__}"
    if label in EXCLUDED_MODELS:
        return False
        
    return True

@receiver(post_save)
def audit_create(sender, instance, created, **kwargs):
    """Log record creation."""
    if not created or not should_audit_model(sender):
        return
        
    user = get_current_user()
    
    # Try to fall back to instance.created_by if available and middleware failed
    if not user and hasattr(instance, 'created_by') and instance.created_by:
        user = instance.created_by
        
    # If still no user (system action), verify if we should log it as system? 
    # For now, require user for strict attribution or assume system if None?
    # Spec says "User Transaction", implying user action. 
    # If no user found, we might ship it with a system user if critical? 
    # Let's try to get system user from DB if user is None.
    
    if not user:
        # Avoid circular import or complex lookups if possible, 
        # but for now we skip creating "UserTransaction" if no user is identifiable.
        return

    # Create transaction
    # Find session? Currently simplistic link. 
    # Ideally middleware would provide session too, but for v1 we duplicate user_id.
    # Note: Spec requires session_id. We might need to look up active session for user.
    # For now, finding the latest active session for this user is a heuristic.
    
    session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
    
    # If no open session found (e.g. CLI or background task), we might need to skip or create dummy?
    # To satisfy FK constraint, we need A session.
    if not session:
        return 

    UserTransaction.objects.create(
        session=session,
        user=user,
        event_type='create',
        entity_type=sender._meta.verbose_name,
        entity_id=instance.id,
        summary=f"Created {sender._meta.verbose_name} {instance}"
    )

@receiver(post_delete)
def audit_delete(sender, instance, **kwargs):
    """Log record deletion."""
    if not should_audit_model(sender):
        return

    user = get_current_user()
    if not user:
        return

    session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
    if not session:
        return 

    UserTransaction.objects.create(
        session=session,
        user=user,
        event_type='delete',
        entity_type=sender._meta.verbose_name,
        entity_id=instance.id,
        summary=f"Deleted {sender._meta.verbose_name} {instance}"
    )

# --- UPDATE AUDITING (Specific Models Only) ---

@receiver(pre_save, sender=Preference)
@receiver(pre_save, sender=BackupSettings)
def capture_previous_state(sender, instance, **kwargs):
    """Capture state before save for update comparison."""
    if not instance.pk:
        return
        
    try:
        current = sender.objects.get(pk=instance.pk)
        instance._original_state = current
    except sender.DoesNotExist:
        pass

@receiver(post_save, sender=Preference)
def audit_preference_update(sender, instance, created, **kwargs):
    """Log changes to Preference values."""
    if created or not hasattr(instance, '_original_state'):
        return
        
    original = instance._original_state
    
    if original.value != instance.value:
        user = get_current_user()
        if not user: return
        
        session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
        if not session: return

        # Truncate values if too long for summary
        old_val = (original.value[:50] + '...') if len(original.value) > 50 else original.value
        new_val = (instance.value[:50] + '...') if len(instance.value) > 50 else instance.value

        UserTransaction.objects.create(
            session=session,
            user=user,
            event_type='update',
            entity_type="Preference",
            entity_id=instance.id,
            summary=f"Changed '{instance.name}' from '{old_val}' to '{new_val}'"
        )

@receiver(post_save, sender=BackupSettings)
def audit_backup_settings_update(sender, instance, created, **kwargs):
    """Log changes to Backup Settings."""
    if created or not hasattr(instance, '_original_state'):
        return
        
    original = instance._original_state
    changes = []
    
    # Check specific fields
    if original.schedule_time != instance.schedule_time:
        changes.append(f"Schedule: {original.schedule_time} -> {instance.schedule_time}")
    
    if original.retention_count != instance.retention_count:
        changes.append(f"Retention: {original.retention_count} -> {instance.retention_count}")
        
    if original.is_enabled != instance.is_enabled:
        changes.append(f"Enabled: {original.is_enabled} -> {instance.is_enabled}")
        
    if original.backup_path != instance.backup_path:
        changes.append(f"Path changed") # Path might be long, keep summary short
    
    if changes:
        user = get_current_user()
        if not user: return
        
        session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
        if not session: return

        summary_text = "Updated Settings: " + ", ".join(changes)
        
        UserTransaction.objects.create(
            session=session,
            user=user,
            event_type='update',
            entity_type="Backup Settings",
            entity_id=instance.id,
            summary=summary_text[:490] # Safe truncate
        )

# --- USER MODEL AUDITING (Special Case) ---
from django.contrib.auth.models import User

@receiver(pre_save, sender=User)
def capture_user_previous_state(sender, instance, **kwargs):
    """Capture User state before save."""
    if not instance.pk:
        return
    try:
        current = User.objects.get(pk=instance.pk)
        instance._original_state = current
    except User.DoesNotExist:
        pass

@receiver(post_save, sender=User)
def audit_user_save(sender, instance, created, **kwargs):
    """Log User creation and updates."""
    user = get_current_user()
    if not user or not user.is_authenticated: return
    
    session = Session.objects.filter(user=user, ended_at__isnull=True).order_by('-started_at').first()
    if not session: return

    if created:
        UserTransaction.objects.create(
            session=session,
            user=user,
            event_type='create',
            entity_type="User",
            entity_id=instance.id,
            summary=f"Created User '{instance.username}'"
        )
    elif hasattr(instance, '_original_state'):
        original = instance._original_state
        changes = []
        
        if original.username != instance.username:
            changes.append(f"Username: '{original.username}' -> '{instance.username}'")
        if original.email != instance.email:
            changes.append(f"Email: '{original.email}' -> '{instance.email}'")
        if original.is_active != instance.is_active:
            status = "Active" if instance.is_active else "Inactive"
            changes.append(f"Status changed to {status}")
        if original.is_staff != instance.is_staff:
            status = "Staff" if instance.is_staff else "Non-Staff"
            changes.append(f"Staff status changed to {status}")
            
        if changes:
            UserTransaction.objects.create(
                session=session,
                user=user,
                event_type='update',
                entity_type="User",
                entity_id=instance.id,
                summary="Updated User: " + ", ".join(changes)
            )
