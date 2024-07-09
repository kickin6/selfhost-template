import logging
from celery import Celery

celery = Celery(__name__)

@celery.task(name='app.tasks.process_task')
def process_task(data):
    # Placeholder for processing logic
    # A webhook call is common
    logger = logging.getLogger(__name__)
    logger.debug(f"Processing task with data: {data}")
    pass
