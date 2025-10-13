from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response:
        return Response(
            {'error': True, 'message': response.data},
            status=response.status_code)

    # fallback
    return Response(
        {'error': True, 'message': str(exc)},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR)
