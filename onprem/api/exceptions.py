# api/exceptions.py
# Custom exception handler for SDTA API.
# Wraps DRF's default handler with consistent error response format.

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError


def sdta_exception_handler(exc, context):
    """
    Custom exception handler that provides a consistent error format.

    Response format:
        {
            "error": true,
            "code": "validation_error",
            "message": "Human-readable summary",
            "details": { ... }  // optional field-level errors
        }
    """
    # Handle Django ValidationError (from model clean/save)
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            details = exc.message_dict
            message = 'Validation failed.'
        else:
            details = exc.messages if hasattr(exc, 'messages') else [str(exc)]
            message = '; '.join(str(m) for m in details) if isinstance(details, list) else str(details)

        return Response(
            {
                'error': True,
                'code': 'validation_error',
                'message': message,
                'details': details,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Let DRF handle the rest
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap DRF's response in our standard format
        error_data = {
            'error': True,
            'code': _status_to_code(response.status_code),
            'message': _get_message(response.data),
            'details': response.data,
        }
        response.data = error_data

    return response


def _status_to_code(status_code):
    """Map HTTP status codes to error code strings."""
    mapping = {
        400: 'bad_request',
        401: 'unauthorized',
        403: 'forbidden',
        404: 'not_found',
        405: 'method_not_allowed',
        409: 'conflict',
        429: 'throttled',
        500: 'internal_error',
    }
    return mapping.get(status_code, f'error_{status_code}')


def _get_message(data):
    """Extract a human-readable message from DRF error data."""
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        # Collect field-level error messages
        messages = []
        for key, value in data.items():
            if isinstance(value, list):
                messages.extend(str(v) for v in value)
            else:
                messages.append(str(value))
        return '; '.join(messages) if messages else 'An error occurred.'
    if isinstance(data, list):
        return '; '.join(str(item) for item in data)
    return str(data)
