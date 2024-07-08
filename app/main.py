from flask import Flask, request, jsonify
from celery import Celery
import os
from auth import api_key_required

app = Flask(__name__)
app.config.from_object("config.Config")

celery = Celery(app.name, broker=app.config["CELERY_BROKER_URL"])
celery.conf.update(app.config)

@app.route("/authenticate", methods=["GET"])
def authenticate():
    api_key = request.headers.get("x-api-key")
    if not api_key:
        return jsonify({"error": "API key is missing"}), 400

    if os.path.isdir(f"./api_keys/{api_key}"):
        return jsonify({"message": "API key is valid"}), 200
    else:
        return jsonify({"error": "Invalid API key"}), 403

@app.route("/process_request", methods=["POST"])
@api_key_required
def process_request():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    task = process_task.apply_async(args=[data])
    return jsonify({"task_id": task.id, "status": "Processing started"}), 202

@celery.task
def process_task(data):
    # Placeholder for processing logic using ffmpeg container
    # Make webhook call to webhook_url in the payload
    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
