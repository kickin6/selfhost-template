#!/usr/bin/env python3

import json
import sys
import os
from jsonschema import validate, ValidationError, SchemaError

def validate_json_payload(schema_filename, payload_filename):
    schema_directory = os.path.join(os.path.dirname(__file__), '../app/json_schemas')
    schema_filepath = os.path.join(schema_directory, schema_filename)

    if not os.path.exists(schema_filepath):
        print(f"Error: Schema file {schema_filepath} does not exist.")
        sys.exit(1)

    if not os.path.exists(payload_filename):
        print(f"Error: Payload file {payload_filename} does not exist.")
        sys.exit(1)

    with open(schema_filepath, 'r') as schema_file:
        schema = json.load(schema_file)

    with open(payload_filename, 'r') as payload_file:
        payload = json.load(payload_file)

    # Validate the payload against the schema
    try:
        validate(instance=payload, schema=schema)
        print(f"Payload {payload_filename} is valid against the schema {schema_filename}.")
    except ValidationError as e:
        print(f"Payload {payload_filename} is invalid against the schema {schema_filename}.")
        print(f"Validation error: {e.message}")
        sys.exit(1)
    except SchemaError as e:
        print(f"Schema {schema_filename} is invalid.")
        print(f"Schema error: {e.message}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./validate_json_payload.py <schema_filename> <payload_filename>")
        sys.exit(1)

    schema_filename = sys.argv[1]
    payload_filename = sys.argv[2]

    validate_json_payload(schema_filename, payload_filename)

