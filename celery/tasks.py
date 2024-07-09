from celery_app import celery
import logging

logger = logging.getLogger(__name__)

@celery.task(name='app.main.process_task')
def process_task(data):
    # Placeholder for processing logic
    # A webhook call to webhook_url is common
    logger.debug(f"Processing task with data: {data}")
    pass
