from functools import wraps
from flask import request, make_response, jsonify

def cors_preflight(f):
    """Decorator to handle CORS preflight requests and add proper headers"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            # Create an empty response with 200 status code for preflight
            response = make_response()
            # We don't set CORS headers here anymore, relying on Flask-CORS
            # to do this correctly for us in all cases.
            return response
        return f(*args, **kwargs)
    return decorated_function
