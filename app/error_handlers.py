from flask import jsonify

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(error):
        response = jsonify({"error": "Invalid JSON payload"})
        response.status_code = 400
        return response

    @app.errorhandler(403)
    def forbidden(error):
        response = jsonify({"error": "Invalid API key"})
        response.status_code = 403
        return response

    @app.errorhandler(404)
    def not_found(error):
        response = jsonify({"error": "Not found"})
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def internal_error(error):
        response = jsonify({"error": "Internal server error"})
        response.status_code = 500
        return response
