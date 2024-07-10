# restx_utils.py

import os
import json
from flask_restx import fields
from werkzeug.exceptions import BadRequest

# Simple in-memory cache
schema_cache = {}

def load_schema_from_file(schema_file):
    if schema_file in schema_cache:
        return schema_cache[schema_file]
    
    if not os.path.exists(schema_file):
        raise FileNotFoundError(f"JSON schema file not found: {schema_file}")
    
    with open(schema_file) as f:
        schema = json.load(f)
        schema_cache[schema_file] = schema
        return schema

def get_field_type(property_details):
    field_type = property_details.get('type')
    if isinstance(field_type, list):
        # If 'null' is one of the types, use the other type
        field_type = [t for t in field_type if t != 'null']
        if len(field_type) == 1:
            field_type = field_type[0]
        else:
            raise ValueError(f"Unsupported combination of field types: {field_type}")
    return field_type

def convert_json_schema_to_restx_model(api, name, schema):
    model_fields = {}
    for property_name, property_details in schema['properties'].items():
        required = property_name in schema.get('required', [])
        field_type = get_field_type(property_details)

        if field_type == 'string':
            if 'enum' in property_details:
                field = fields.String(required=required, description=property_details.get('description', ''), enum=property_details['enum'])
            else:
                field = fields.String(required=required, description=property_details.get('description', ''), default=property_details.get('default', ''))
        elif field_type == 'number':
            field = fields.Float(required=required, description=property_details.get('description', ''), default=property_details.get('default', 0))
        elif field_type == 'boolean':
            field = fields.Boolean(required=required, description=property_details.get('description', ''), default=property_details.get('default', False))
        elif field_type == 'array':
            items = property_details.get('items', {})
            if items.get('type') == 'object':
                nested_model = convert_json_schema_to_restx_model(api, f"{name}_{property_name}", items)
                field = fields.List(fields.Nested(nested_model), required=required, description=property_details.get('description', ''))
            else:
                field = fields.List(fields.String, required=required, description=property_details.get('description', ''))
        elif field_type == 'object':
            nested_model = convert_json_schema_to_restx_model(api, f"{name}_{property_name}", property_details)
            field = fields.Nested(nested_model, required=required, description=property_details.get('description', ''))
        else:
            raise ValueError(f"Unsupported field type: {field_type}")

        model_fields[property_name] = field

    return api.model(name, model_fields)

def load_and_convert_schema(api, endpoint_name):
    schema_file = f'json_schemas/{endpoint_name}_request.json'
    try:
        schema = load_schema_from_file(schema_file)
        return convert_json_schema_to_restx_model(api, endpoint_name, schema)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise BadRequest(str(e))

