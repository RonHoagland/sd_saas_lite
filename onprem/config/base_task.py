# config/base_task.py
# Shared Celery task base classes for SDTA.
# Source: Technical Architecture V2, Section 6.5.
#
# Provides TenantAwareTask — a base class that:
#   - Sets tenant context before task execution (so TenantManager filters work).
#   - Clears tenant context after execution (prevents leakage in worker threads).
#   - Uses the `worker` DB alias for cross-tenant background reads.
#   - Applies standardized retry policies with exponential backoff.
#   - Logs task lifecycle events for observability.
#
# Usage:
#   from config.base_task import TenantAwareTask
#
#   @shared_task(base=TenantAwareTask, bind=True)
#   def my_task(self, tenant_id, ...):
#       # tenant context is already set — TenantManager will filter to this tenant.
#       # Use Model.all_objects for cross-tenant reads if needed.
#       pass

import logging
from celery import Task
from celery.exceptions import MaxRetriesExceededError

from .tenant_context import set_current_tenant_id, clear_current_tenant_id

logger = logging.getLogger('sdta.tasks')


class TenantAwareTask(Task):
    """
    Base Celery task class with tenant context management.

    All SDTA background tasks should use this as their base class. It ensures
    the tenant_id is set in the thread-local context before the task body runs,
    and cleared afterwards — even if the task fails.

    Convention: the first positional argument to every task using this base
    must be `tenant_id` (str UUID). The task can accept it either as:
      - The first arg after `self` (when bind=True)
      - A kwarg named `tenant_id`

    Retry policy (defaults, overridable per-task):
      - max_retries: 3
      - default_retry_delay: 60 seconds
      - Exponential backoff with jitter via retry(countdown=...)

    Attributes:
        autoretry_for: Tuple of exception types to auto-retry on.
        max_retries: Maximum retry attempts.
        default_retry_delay: Base delay in seconds between retries.
    """

    # ── Default retry policy ──────────────────────────────────────────────────
    max_retries = 3
    default_retry_delay = 60  # seconds
    autoretry_for = (Exception,)
    retry_backoff = True       # exponential backoff
    retry_backoff_max = 600    # cap at 10 minutes
    retry_jitter = True        # add randomness to prevent thundering herd

    # ── Task execution hooks ──────────────────────────────────────────────────

    def before_start(self, task_id, args, kwargs):
        """
        Called just before the task starts executing.

        Extracts tenant_id from args/kwargs and sets the thread-local context.
        """
        tenant_id = self._extract_tenant_id(args, kwargs)
        if tenant_id:
            set_current_tenant_id(str(tenant_id))
            logger.info(
                'Task %s[%s] starting for tenant %s',
                self.name, task_id, tenant_id,
            )
        else:
            logger.info(
                'Task %s[%s] starting (no tenant context)',
                self.name, task_id,
            )

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Called after the task returns (success or failure).

        Always clears tenant context to prevent leakage to the next task
        executed by the same worker thread.
        """
        clear_current_tenant_id()
        logger.info(
            'Task %s[%s] finished with status=%s',
            self.name, task_id, status,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Called when the task fails permanently (after all retries exhausted).

        Logs the error with full context for debugging.
        """
        tenant_id = self._extract_tenant_id(args, kwargs)
        logger.error(
            'Task %s[%s] failed permanently for tenant %s: %s',
            self.name, task_id, tenant_id, exc,
            exc_info=True,
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """
        Called when a task is retried.

        Logs the retry with attempt count for monitoring.
        """
        tenant_id = self._extract_tenant_id(args, kwargs)
        logger.warning(
            'Task %s[%s] retrying for tenant %s (attempt %d/%d): %s',
            self.name, task_id, tenant_id,
            self.request.retries + 1, self.max_retries, exc,
        )

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_tenant_id(self, args, kwargs):
        """
        Extract tenant_id from task args or kwargs.

        Convention: tenant_id is the first positional arg or a kwarg.
        """
        if kwargs and 'tenant_id' in kwargs:
            return kwargs['tenant_id']
        if args:
            return args[0]
        return None


class SystemTask(Task):
    """
    Base class for system-level tasks that are NOT tenant-scoped.

    Examples: retention purges, aggregate metrics, health checks.
    These tasks use `all_objects` manager and the `worker` DB alias
    for unrestricted cross-tenant access.

    No tenant context is set. The task body is responsible for any
    tenant iteration logic.
    """

    max_retries = 3
    default_retry_delay = 120
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def before_start(self, task_id, args, kwargs):
        """Ensure no tenant context leaks into system tasks."""
        clear_current_tenant_id()
        logger.info('System task %s[%s] starting', self.name, task_id)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        clear_current_tenant_id()
        logger.info(
            'System task %s[%s] finished with status=%s',
            self.name, task_id, status,
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(
            'System task %s[%s] failed permanently: %s',
            self.name, task_id, exc,
            exc_info=True,
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(
            'System task %s[%s] retrying (attempt %d/%d): %s',
            self.name, task_id,
            self.request.retries + 1, self.max_retries, exc,
        )
