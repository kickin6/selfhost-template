import os
from functools import wraps
from flask import request, jsonify

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("x-api-key")
        if not api_key or not os.path.isdir(f"./api_keys/{api_key}"):
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated_function
