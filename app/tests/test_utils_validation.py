import os
import glob
import json
import pytest
from app.utils import validate_response

@pytest.fixture
def test_files_dir():
    return os.path.join(os.path.dirname(__file__), 'test_files')

@pytest.mark.parametrize("schema_path", glob.glob(os.path.join('tests/test_files', 'test_schema_*_request.json')))
def test_jsonschema_validation(test_files_dir, schema_path):
    # Extract the test number from the schema file name
    test_number = os.path.splitext(os.path.basename(schema_path))[0].split('_')[-2]
    payload_file = os.path.join(test_files_dir, f'test_payload_{test_number}_request.json')

    # Load schema
    with open(schema_path, 'r') as file:
        schema = json.load(file)

    # Load payload
    with open(payload_file, 'r') as file:
        payload = json.load(file)

    # Validate
    errors = validate_response(schema, payload)
    assert not errors, f"Validation errors for schema {schema_path} and payload {payload_file}: {errors}"
