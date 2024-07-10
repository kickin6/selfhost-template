import json
import os
from flask import Flask, request, jsonify, make_response
from flask_restx import Api, Resource, fields  # Ensure fields is imported
from app.auth import api_key_required
from app.celery_app import celery, init_celery
from app.utils import load_schema, validate_data
from app.tasks import process_task
from .restx_utils import load_and_convert_schema

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    app = Flask(__name__)
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object('app.config.DevelopmentConfig')

    app.config.setdefault('CELERY_BROKER_URL', 'redis://redis:6379/0')
    app.config.setdefault('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

    init_celery(app)

    api = Api(app, doc='/docs', title='My API', description='API documentation')

    auth_ns = api.namespace('auth', description='Authentication operations')
    process_ns = api.namespace('process', description='Process operations')

    auth_model = auth_ns.model('Authenticate', {
        'x-api-key': fields.String(required=True, description='API key', location='headers')
    })

    process_request_model = load_and_convert_schema(process_ns, 'process_request')

    @auth_ns.route("/authenticate")
    class Authenticate(Resource):
        @auth_ns.doc('check_auth')
        def get(self):
            api_key = request.headers.get("x-api-key")
            if not api_key:
                return make_response(jsonify({"error": "API key is missing"}), 400)

            output_dir = os.getenv('OUTPUT_DIR', './output')
            api_key_path = os.path.join(output_dir, 'api_keys', api_key)
            
            if os.path.isdir(api_key_path):
                return make_response(jsonify({"message": "API key is valid"}), 200)
            else:
                return make_response(jsonify({"error": "Invalid API key"}), 403)

    @process_ns.route("/process_request")
    class ProcessRequest(Resource):
        @process_ns.doc('process_request')
        @process_ns.expect(process_request_model, validate=True)
        @api_key_required
        def post(self):
            if not request.is_json:
                logger.debug("Invalid JSON payload")
                return make_response(jsonify({"error": "Invalid JSON payload"}), 400)

            try:
                data = request.get_json()
                if not data:
                    raise ValueError("No JSON data")
            except ValueError:
                logger.debug("Invalid JSON payload")
                return make_response(jsonify({"error": "Invalid JSON payload"}), 400)

            schema = load_schema("process_request", "request")
            errors, validated_data = validate_data(schema, data)

            logger.debug(f"Validation errors: {errors}")
            logger.debug(f"Validated data: {validated_data}")

            if errors:
                return make_response(jsonify({"error": errors}), 400)

            # Filter out any additional fields not in the schema
            filtered_data = {k: v for k, v in validated_data.items() if k in schema["properties"]}

            # Task creation logic
            task = process_task.apply_async(args=[filtered_data])
            response_schema = load_schema("process_request", "response")
            response = {"task_id": task.id, "status": task.status}
            response.update({k: v["default"] for k, v in response_schema["properties"].items() if "default" in v})
            return make_response(jsonify(response), 202)

    return app

if __name__ == "__main__":
    app = create_app('app.config.DevelopmentConfig')
    app.run(host="0.0.0.0", port=5000)
