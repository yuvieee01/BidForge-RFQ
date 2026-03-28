from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    """Wrap all DRF exceptions in standard {success, data, error} envelope."""
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = response.data
        if isinstance(error_detail, dict):
            # Flatten validation errors into a readable string
            messages = []
            for field, errors in error_detail.items():
                if isinstance(errors, list):
                    messages.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    messages.append(str(errors))
            error_message = "; ".join(messages)
        elif isinstance(error_detail, list):
            error_message = ", ".join(str(e) for e in error_detail)
        else:
            error_message = str(error_detail)

        response.data = {
            "success": False,
            "data": None,
            "error": error_message,
        }

    return response
