import os
import ast
import pytest
import secrets
import shutil
from app.main import create_app
from app.celery_app import celery, init_celery
from app.utils import load_schema, create_valid_payload, validate_response

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
    file_path = os.path.join(base_dir, '..', 'json_schemas', f'{endpoint.lstrip("/")}_{config_type}.json')
    return os.path.isfile(file_path)

def get_endpoints_from_main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    main_file_path = os.path.join(base_dir, '..', 'main.py')
    with open(main_file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=main_file_path)

    endpoints = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == 'route':
                    route_path = decorator.args[0].s
                    endpoints.append(route_path)
    return endpoints

endpoints = get_endpoints_from_main()

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_with_invalid_api_key(client, endpoint):
    if endpoint == '/authenticate':
        pytest.skip("Skipping authenticate endpoint")

    response = client.post(endpoint, json={"some": "data"}, headers={"x-api-key": "invalid_key"})
    assert response.status_code == 403
    assert response.get_json() == {"error": "Invalid API key"}

def test_authenticate_missing_api_key(client):
    response = client.get("/authenticate")
    assert response.status_code == 400
    assert response.get_json() == {"error": "API key is missing"}

def test_authenticate_invalid_api_key(client):
    response = client.get("/authenticate", headers={"x-api-key": "invalid_key"})
    assert response.status_code == 403
    assert response.get_json() == {"error": "Invalid API key"}

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_missing_field(client, endpoint):
    if not schema_exists(endpoint, "request"):
        pytest.skip(f"No request schema for {endpoint}")

    output_dir = os.getenv('OUTPUT_DIR', './output')
    api_key_path = os.path.join(output_dir, 'test_key')
    os.makedirs(api_key_path, exist_ok=True)
    try:
        schema = load_schema(endpoint, "request")
        required_fields = [field for field in schema.get("required", [])]

        # Create a payload with all required fields except the last one
        missing_field_payload = create_valid_payload(schema)
        missing_field_payload.pop(required_fields[-1])

        rv = client.post(endpoint, json=missing_field_payload, headers={"x-api-key": "test_key"})

        assert rv.status_code == 400
        missing_field = required_fields[-1]
        assert f"'{missing_field}' is a required property" in rv.get_json()["error"]
    finally:
        shutil.rmtree(api_key_path)

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_invalid_json(client, endpoint):
    if not schema_exists(endpoint, "request"):
        pytest.skip(f"No request schema for {endpoint}")

    output_dir = os.getenv('OUTPUT_DIR', './output')
    api_key_path = os.path.join(output_dir, 'test_key')
    os.makedirs(api_key_path, exist_ok=True)
    try:
        schema = load_schema(endpoint, "request")
        valid_payload = create_valid_payload(schema)
        valid_payload["input_url"] = "invalid_json"  # Add invalid field

        rv = client.post(endpoint, json=valid_payload, headers={"x-api-key": "test_key"})

        assert rv.status_code == 202
        response_data = rv.get_json()
        # Assuming your response includes the filtered payload for testing purposes
        assert "input_url" not in response_data.get("processed_payload", {})
    finally:
        shutil.rmtree(api_key_path)

@pytest.mark.parametrize("endpoint", endpoints)
def test_process_request_valid_response(client, endpoint):
    if not schema_exists(endpoint, "request"):
        pytest.skip(f"No request schema for {endpoint}")
    if not schema_exists(endpoint, "response"):
        pytest.skip(f"No response schema for {endpoint}")

    output_dir = os.getenv('OUTPUT_DIR', './output')
    api_key_path = os.path.join(output_dir, 'test_key')
    os.makedirs(api_key_path, exist_ok=True)
    try:
        schema = load_schema(endpoint, "request")
        valid_payload = create_valid_payload(schema)

        rv = client.post(endpoint, json=valid_payload, headers={"x-api-key": "test_key"})

        assert rv.status_code == 202
        response_schema = load_schema(endpoint, "response")
        response_data = rv.get_json()
        errors = validate_response(response_schema, response_data)
        assert not errors, f"Response validation errors: {errors}"
    finally:
        shutil.rmtree(api_key_path)
