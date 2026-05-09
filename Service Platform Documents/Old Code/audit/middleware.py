import threading

_thread_locals = threading.local()

def get_current_user():
    """
    Return the current user from thread local storage.
    Returns None if no user is set or available.
    """
    return getattr(_thread_locals, 'user', None)

class AuditMiddleware:
    """
    Middleware to store the current user in thread local storage.
    This allows signals and other decoupled components to access the current user
    without having the request object explicitly passed to them.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Store user in thread local
        if hasattr(request, 'user'):
            _thread_locals.user = request.user
        else:
            _thread_locals.user = None
            
        try:
            response = self.get_response(request)
        finally:
            # Clean up thread local to prevent leakage
            _thread_locals.user = None
            
        return response
