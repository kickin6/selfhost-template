from celery import Celery
import requests

app = Celery("tasks", broker="redis://redis:6379/0")

@app.task
def process_task(data):
    # Placeholder for external call to ffmpeg container
    webhook_url = data.get("webhook_url")
    if webhook_url:
        requests.post(webhook_url, json={"status": "Processing completed"})
