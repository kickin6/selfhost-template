import pytest
from app.main import create_app
from app.celery_app import celery, init_celery

@pytest.fixture
def app():
    app = create_app('config.TestingConfig')
    init_celery(app)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def celery_app(app):
    celery.conf.update(task_always_eager=True)
    yield celery
    celery.conf.update(task_always_eager=False)
