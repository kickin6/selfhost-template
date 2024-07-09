from app.celery_app import celery
import logging

logger = logging.getLogger(__name__)

@celery.task(name='app.main.process_task')
def process_task(data):
    # Placeholder for processing logic
    logger.debug(f"Processing task with data: {data}")
    pass
