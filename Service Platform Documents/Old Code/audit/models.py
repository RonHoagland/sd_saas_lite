"""
Audit Models - Sessions and Event Logging

Implements Platform Core Sessions and Event Logging Specification.
Provides accountability, troubleshooting, and auditing capabilities.
"""

import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


class Session(models.Model):
    """
    User Session record per Platform Core Sessions specification.
    
    Created on every login attempt (successful or failed).
    Immutable once written (except for setting ended_at/end_reason).
    """
    
    AUTH_RESULT_CHOICES = [
        ('success', 'Success'),
        ('failure', 'Failure'),
    ]
    
    END_REASON_CHOICES = [
        ('logout', 'Logout'),
        ('timeout', 'Timeout'),
        ('admin_invalidate', 'Admin Invalidate'),
        ('auth_failure', 'Auth Failure'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,  # Allow deletion of users with only login records
        null=True,
        blank=True,
        help_text="User (null if authentication failed)"
    )
    
    attempted_username = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Username entered at login (required when user is null)"
    )
    
    auth_result = models.CharField(
        max_length=10,
        choices=AUTH_RESULT_CHOICES,
        help_text="Authentication result"
    )
    
    auth_failure_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason for authentication failure"
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Session start timestamp"
    )
    
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Session end timestamp"
    )
    
    end_reason = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=END_REASON_CHOICES,
        help_text="Reason session ended"
    )
    
    client_info = models.TextField(
        null=True,
        blank=True,
        help_text="User agent or client information"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of client"
    )
    
    user_snapshot = models.JSONField(
        null=True,
        blank=True,
        help_text="Snapshot of user info at login (user_id, username, display_name, roles)"
    )
    
    class Meta:
        verbose_name = "Session"
        verbose_name_plural = "Sessions"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['started_at']),
            models.Index(fields=['ended_at']),
            models.Index(fields=['auth_result']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Session {self.id} - {self.user.username} - {self.auth_result}"
        return f"Session {self.id} - {self.attempted_username} - {self.auth_result}"


class UserTransaction(models.Model):
    """
    User Transaction event record per Platform Core Sessions specification.
    
    Records discrete user-triggered system events.
    V1: Create and Delete operations only.
    Immutable (append-only).
    """
    
    EVENT_TYPE_CHOICES = [
        ('create', 'Create'),
        ('delete', 'Delete'),
        ('update', 'Update'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    session = models.ForeignKey(
        Session,
        on_delete=models.PROTECT,
        help_text="Session in which event occurred"
    )
    
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        help_text="User who performed the action"
    )
    
    event_ts = models.DateTimeField(
        auto_now_add=True,
        help_text="Event timestamp"
    )
    
    event_type = models.CharField(
        max_length=10,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event"
    )
    
    entity_type = models.CharField(
        max_length=100,
        help_text="Logical entity/table name (e.g., Client, Contact, Invoice)"
    )
    
    entity_id = models.UUIDField(
        help_text="UUID of the record created or deleted"
    )
    
    reason_text = models.TextField(
        null=True,
        blank=True,
        help_text="Reason for action (required for some delete operations)"
    )
    
    summary = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Short human-readable description"
    )
    
    class Meta:
        verbose_name = "User Transaction"
        verbose_name_plural = "User Transactions"
        ordering = ['-event_ts']
        indexes = [
            models.Index(fields=['session']),
            models.Index(fields=['user']),
            models.Index(fields=['event_ts']),
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['event_type']),
        ]
    
    @property
    def local_timestamp_display(self):
        """
        Return the event timestamp formatted in the users preferred timezone.
        Returns a string to avoid Django template re-conversion to UTC.
        """
        try:
            import zoneinfo
            from datetime import timezone as dt_timezone
            from core.models import Preference
            
            # Default to UTC
            tz = dt_timezone.utc
            
            # Try to get preference
            pref = Preference.objects.filter(key='loc_timezone').first()
            if pref and pref.value:
                try:
                    tz = zoneinfo.ZoneInfo(pref.value)
                except Exception:
                    pass
            
            # Convert
            if self.event_ts:
                local_dt = self.event_ts.astimezone(tz)
                return local_dt.strftime('%Y-%m-%d %I:%M:%S %p')
            return "—"
            
        except Exception:
            # Fallback
            if self.event_ts:
                return self.event_ts.strftime('%Y-%m-%d %I:%M:%S %p')
            return "—"

    def __str__(self):
        return f"{self.event_type.upper()} - {self.entity_type} ({self.entity_id}) by {self.user.username}"
