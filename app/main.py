from flask import Flask, request, jsonify
import os
from app.auth import api_key_required
from app.celery_app import celery, init_celery
from app.utils import load_schema, validate_data
from app.tasks import process_task

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

    @app.route("/authenticate", methods=["GET"])
    def authenticate():
        api_key = request.headers.get("x-api-key")
        if not api_key:
            return jsonify({"error": "API key is missing"}), 400

        output_dir = os.getenv('OUTPUT_DIR', './output')
        api_key_path = os.path.join(output_dir, 'api_keys', api_key)
        
        if os.path.isdir(api_key_path):
            return jsonify({"message": "API key is valid"}), 200
        else:
            return jsonify({"error": "Invalid API key"}), 403

    @app.route("/process_request", methods=["POST"])
    @api_key_required
    def process_request():
        if not request.is_json:
            logger.debug("Invalid JSON payload")
            return jsonify({"error": "Invalid JSON payload"}), 400

        try:
            data = request.get_json()
            if not data:
                raise ValueError("No JSON data")
        except ValueError:
            logger.debug("Invalid JSON payload")
            return jsonify({"error": "Invalid JSON payload"}), 400

        schema = load_schema("process_request", "request")
        errors, validated_data = validate_data(schema, data)

        logger.debug(f"Validation errors: {errors}")
        logger.debug(f"Validated data: {validated_data}")

        if errors:
            return jsonify({"error": errors}), 400

        # Filter out any additional fields not in the schema
        filtered_data = {k: v for k, v in validated_data.items() if k in schema["properties"]}

        # Task creation logic
        task = process_task.apply_async(args=[filtered_data])
        response_schema = load_schema("process_request", "response")
        response = {"task_id": task.id, "status": task.status}
        response.update({k: v["default"] for k, v in response_schema["properties"].items() if "default" in v})
        return jsonify(response), 202

    return app

if __name__ == "__main__":
    app = create_app('app.config.DevelopmentConfig')
    app.run(host="0.0.0.0", port=5000)
