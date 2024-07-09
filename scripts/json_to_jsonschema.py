#!/usr/bin/env python3

import json
import re
import sys
import os
from jsonschema import Draft7Validator

def infer_type(value):
    """Infers the JSON Schema type for a given value."""
    if value == "text" or value == "url":
        return "string"
    elif value == "number":
        return "number"
    elif value == "integer":
        return "integer"
    elif value == "boolean":
        return "boolean"
    elif value == "array":
        return "array"
    elif value == "object" or value == "collection":
        return "object"
    else:
        return "null"

def generate_property_schema(property, is_required):
    """Generates a JSON Schema for a single property."""
    schema = {
        "type": infer_type(property.get("type", "string"))
    }
    if "default" in property:
        schema["default"] = property["default"]
    if property.get("type") == "url":
        schema["format"] = "uri"
    if property.get("type") == "select" and "options" in property:
        options = [option.get("value", option.get("label")) for option in property["options"]]
        if is_required:
            schema["enum"] = options
        else:
            schema = {
                "anyOf": [
                    {"type": "string", "enum": options},
                    {"type": "string"}
                ]
            }
    if property.get("type") == "collection" and "spec" in property:
        schema = generate_schema(property["spec"], is_required)
    return schema

def generate_schema(json_data, is_parent_required=False):
    """Generates a JSON Schema for the provided JSON data."""
    if isinstance(json_data, list):
        if not json_data:
            return {"type": "array", "items": {}}
        if isinstance(json_data[0], dict):
            schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            for item in json_data:
                if not isinstance(item, dict):
                    raise TypeError(f"Expected each item in json_data to be a dictionary, but got {type(item)}. Content: {item}")
                property_name = item["name"]
                is_required = item.get("required", is_parent_required)
                if "grouped" in item and item["grouped"]:
                    schema["properties"][property_name] = generate_schema(item.get("properties", []), is_required)
                elif item.get("type") == "collection" and "spec" in item:
                    schema["properties"][property_name] = generate_schema(item.get("spec", []), is_required)
                elif item.get("type") == "array" and "items" in item:
                    schema["properties"][property_name] = {
                        "type": "array",
                        "items": generate_schema(item.get("items", []), is_required) if isinstance(item["items"], list) else generate_property_schema(item["items"], is_required)
                    }
                else:
                    schema["properties"][property_name] = generate_property_schema(item, is_required)
                if is_required:
                    schema["required"].append(property_name)
            if not schema["required"]:
                del schema["required"]
            return schema
        else:
            raise TypeError(f"Expected first item in json_data list to be a dictionary, but got {type(json_data[0])}. Content: {json_data[0]}")
    
    if not isinstance(json_data, dict):
        raise TypeError(f"Expected json_data to be a dictionary or list of dictionaries, but got {type(json_data)}. Content: {json_data}")

    schema = {
        "type": "object",
        "properties": {},
        "required": []
    }

    for key, item in json_data.items():
        if not isinstance(item, dict):
            raise TypeError(f"Expected each item in json_data to be a dictionary, but got {type(item)}. Content: {item}")
        property_name = key
        is_required = item.get("required", is_parent_required)
        if "grouped" in item and item["grouped"]:
            schema["properties"][property_name] = generate_schema(item.get("properties", []), is_required)
        elif item.get("type") == "collection" and "spec" in item:
            schema["properties"][property_name] = generate_schema(item.get("spec", []), is_required)
        elif item.get("type") == "array" and "items" in item:
            schema["properties"][property_name] = {
                "type": "array",
                "items": generate_schema(item.get("items", []), is_required) if isinstance(item["items"], list) else generate_property_schema(item["items"], is_required)
            }
        else:
            schema["properties"][property_name] = generate_property_schema(item, is_required)
        if is_required:
            schema["required"].append(property_name)

    if not schema["required"]:
        del schema["required"]

    return schema

def convert_to_jsonschema(json_data):
    """Converts plain JSON data to JSON Schema compliant JSON."""
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
    }
    schema.update(generate_schema(json_data))
    return schema

def validate_filename(name):
    """Validates the filename and type according to the specified rules."""
    if not re.match(r'^\w+$', name):
        raise ValueError("Filename and type can only contain letters, numbers, or underscores.")

def validate_input_filename(input_filename):
    """Validates that the input filename ends with .json and has a valid base name."""
    if not input_filename.endswith('.json'):
        raise ValueError("Input filename must end with .json")
    base_name = input_filename[:-5]  # Remove the .json part
    validate_filename(base_name)
    return base_name

def main(input_filename, file_type):
    base_name = validate_input_filename(input_filename)
    validate_filename(file_type)

    #output_directory = os.path.join(os.path.dirname(__file__), '../app/json_schemas')
    output_directory = os.path.join(os.path.dirname(__file__), '../app/tests/test_files')
    os.makedirs(output_directory, exist_ok=True)
    output_filename = os.path.join(output_directory, f"{base_name}_{file_type}.json")

    if os.path.exists(output_filename):
        overwrite = input(f"File {output_filename} already exists. Do you want to overwrite it? (Y/n): ").strip().lower()
        if overwrite == 'n':
            print("Operation cancelled.")
            sys.exit(0)

    with open(input_filename, 'r') as f:
        json_data = json.load(f)

    print("Loaded JSON data:")
    print(json.dumps(json_data, indent=2))

    try:
        json_schema = convert_to_jsonschema(json_data)
    except TypeError as e:
        print(f"Error generating JSON schema: {e}")
        sys.exit(1)

    # Validate generated schema to ensure it is correct
    try:
        Draft7Validator.check_schema(json_schema)
        print("Generated JSON Schema is valid.")
    except Exception as e:
        print("Generated JSON Schema is invalid.")
        print(f"Validation error: {e}")
        sys.exit(1)

    with open(output_filename, 'w') as f:
        json.dump(json_schema, f, indent=2)

    relative_output_path = os.path.relpath(output_filename)
    print(relative_output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: ./json-to-jsonschema.py <input_filename> <type>")
        sys.exit(1)

    input_filename = sys.argv[1]
    file_type = sys.argv[2]

    if not os.path.exists(input_filename):
        print(f"Error: File {input_filename} does not exist.")
        sys.exit(1)

    main(input_filename, file_type)

