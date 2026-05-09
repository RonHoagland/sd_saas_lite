# config/tenant_context.py
# Async-safe, thread-safe storage for the current request's tenant_id.
# Uses asgiref.local.Local so the value is isolated per async task / thread.
# Source: Technical Architecture V2, Section 4.2.

from asgiref.local import Local

_state = Local()


def set_current_tenant_id(tenant_id: str | None) -> None:
    _state.tenant_id = tenant_id


def get_current_tenant_id() -> str | None:
    return getattr(_state, 'tenant_id', None)


def clear_current_tenant_id() -> None:
    try:
        del _state.tenant_id
    except AttributeError:
        pass
