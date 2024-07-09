from celery import Celery, Task

celery = Celery(__name__)

class ContextTask(Task):
    def __call__(self, *args, **kwargs):
        with self.app.app_context():
            return self.run(*args, **kwargs)

def init_celery(app):
    celery.conf.update(app.config)
    celery.conf.broker_url = app.config['CELERY_BROKER_URL']
    celery.conf.result_backend = app.config['CELERY_RESULT_BACKEND']
    celery.autodiscover_tasks(['app.main'])
    celery.Task = ContextTask
    celery.Task.app = app  # Bind Flask app to the ContextTask
