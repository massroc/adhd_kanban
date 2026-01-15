"""
Custom exception handler for consistent error response format.

Converts DRF's default error format to a consistent format
using 'error' key instead of 'detail'.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that standardizes error responses.
    
    Converts DRF's default {'detail': 'message'} format to {'error': 'message'}
    for consistency across all error responses.
    
    Validation errors (serializer.errors) are preserved as-is since they
    contain field-specific error information.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Only convert 'detail' to 'error' if it's a simple detail error
        # Preserve validation errors (which are dicts with field names as keys)
        if 'detail' in response.data and not isinstance(response.data['detail'], dict):
            # Convert 'detail' to 'error' for consistency
            response.data['error'] = response.data.pop('detail')
            
            # Ensure error is a string (not a list)
            if isinstance(response.data.get('error'), list) and len(response.data['error']) > 0:
                response.data['error'] = response.data['error'][0]
    
    return response
