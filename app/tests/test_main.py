import os
import ast
import pytest
from app.main import create_app
from app.celery_app import celery, init_celery
from app.utils import load_schema, create_valid_payload, validate_response

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

def schema_exists(endpoint, config_type):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    logger.debug(f"BaseDir at {base_dir}")
    file_path = os.path.join(base_dir, '..', 'json_schemas', f'{endpoint.lstrip("/")}_{config_type}.json')
    exists = os.path.isfile(file_path)
    logger.debug(f"Checking if schema exists at {file_path}: {exists}")
    return exists

def get_endpoints_from_main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    main_file_path = os.path.join(base_dir, '..', 'main.py')
    logger.debug(f"Reading main.py from {main_file_path}")
    with open(main_file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=main_file_path)

    endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
                    route_path = decorator.args[0].s
                    endpoints.append(route_path)
    logger.debug(f"Found endpoints: {endpoints}")
    return endpoints

endpoints = get_endpoints_from_main()

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_missing_field(client, endpoint):
    if not schema_exists(endpoint, "request"):
        logger.debug(f"No request schema for {endpoint}")
        pytest.skip(f"No request schema for {endpoint}")

    os.makedirs("./app/api_keys/test_key", exist_ok=True)
    schema = load_schema(endpoint, "request")
    required_fields = [field for field in schema.get("required", [])]

    # Create a payload with all required fields except the last one
    missing_field_payload = create_valid_payload(schema)
    missing_field_payload.pop(required_fields[-1])

    logger.debug(f"Payload sent: {missing_field_payload}")

    rv = client.post(endpoint, json=missing_field_payload, headers={"x-api-key": "test_key"})
    logger.debug(f"Response status: {rv.status_code}")
    logger.debug(f"Response data: {rv.get_json()}")

    assert rv.status_code == 400
    missing_field = required_fields[-1]
    assert f"'{missing_field}' is a required property" in rv.get_json()["error"]

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_invalid_json(client, endpoint):
    if not schema_exists(endpoint, "request"):
        logger.debug(f"No request schema for {endpoint}")
        pytest.skip(f"No request schema for {endpoint}")

    os.makedirs("./app/api_keys/test_key", exist_ok=True)
    schema = load_schema(endpoint, "request")
    valid_payload = create_valid_payload(schema)
    valid_payload["input_url"] = "invalid_json"  # Add invalid field

    logger.debug(f"Payload sent: {valid_payload}")

    rv = client.post(endpoint, json=valid_payload, headers={"x-api-key": "test_key"})
    logger.debug(f"Response status: {rv.status_code}")
    logger.debug(f"Response data: {rv.get_json()}")

    assert rv.status_code == 202
    response_data = rv.get_json()
    # Assuming your response includes the filtered payload for testing purposes
    assert "input_url" not in response_data.get("processed_payload", {})


@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_valid_response(client, endpoint):
    if not schema_exists(endpoint, "request"):
        logger.debug(f"No request schema for {endpoint}")
        pytest.skip(f"No request schema for {endpoint}")
    if not schema_exists(endpoint, "response"):
        logger.debug(f"No response schema for {endpoint}")
        pytest.skip(f"No response schema for {endpoint}")

    os.makedirs("./app/api_keys/test_key", exist_ok=True)
    schema = load_schema(endpoint, "request")
    valid_payload = create_valid_payload(schema)

    logger.debug(f"Payload sent: {valid_payload}")

    rv = client.post(endpoint, json=valid_payload, headers={"x-api-key": "test_key"})
    logger.debug(f"Response status: {rv.status_code}")
    logger.debug(f"Response data: {rv.get_json()}")

    assert rv.status_code == 202
    response_schema = load_schema(endpoint, "response")
    response_data = rv.get_json()
    errors = validate_response(response_schema, response_data)
    assert not errors, f"Response validation errors: {errors}"
