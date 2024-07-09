import json
import os
import logging
from jsonschema import validate, ValidationError, SchemaError
import ast

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_schema(endpoint, config_type):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    endpoint = endpoint.lstrip('/')
    file_path = os.path.join(base_dir, 'json_schemas', f'{endpoint}_{config_type}.json')
    logger.debug(f"Loading schema from: {file_path}")
    with open(file_path, 'r') as file:
        schema = json.load(file)
    logger.debug(f"Loaded schema: {schema}")
    return schema

def validate_data(schema, data):
    errors = []
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        errors.append(e.message)
        logger.debug(f"'{e.message}' is a required property")
    except SchemaError as e:
        errors.append(f"Schema error: {e.message}")
        logger.debug(f"Schema error: {e.message}")
    
    return errors, data if not errors else {}

def create_valid_payload(schema):
    payload = {}
    for field, details in schema.get("properties", {}).items():
        if "default" in details:
            payload[field] = details["default"]
        elif details["type"] == "string":
            payload[field] = "test_string"
        elif details["type"] == "number":
            payload[field] = 24
        elif details["type"] == "boolean":
            payload[field] = True
        elif details["type"] == "uri":
            payload[field] = "http://example.com"
    logger.debug(f"Created valid payload: {payload}")
    return payload

def validate_response(schema, response_data):
    errors = []
    try:
        validate(instance=response_data, schema=schema)
    except ValidationError as e:
        errors.append(e.message)
        logger.debug(f"Validation error: {e.message}")
    except SchemaError as e:
        errors.append(f"Schema error: {e.message}")
        logger.debug(f"Schema error: {e.message}")
    
    return errors

def schema_exists(endpoint, config_type):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, '..', 'json_schemas', f'{endpoint}_{config_type}.json')
    logger.debug(f"Checking if schema exists at {file_path}: {os.path.isfile(file_path)}")
    return os.path.isfile(file_path)

def get_endpoints_from_main(main_file_path='app/main.py'):
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
