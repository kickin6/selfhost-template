import logging
from celery import Celery

celery = Celery(__name__)

@celery.task(name='app.tasks.process_task')
def process_task(data):
    # Placeholder for processing logic using ffmpeg container
    # Make webhook call to webhook_url in the payload
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing task with data: {data}")
    pass
