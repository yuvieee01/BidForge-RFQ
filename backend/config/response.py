"""
Standard API response envelope.
All APIs return: { "success": bool, "data": any, "error": str|null }
"""


def success_response(data=None, message=None):
    payload = {"success": True, "data": data, "error": None}
    if message:
        payload["message"] = message
    return payload


def error_response(error_message, data=None):
    return {"success": False, "data": data, "error": error_message}
