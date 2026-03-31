"""
Station 4: JSON Validation
============================
This file checks if the AI's output is valid JSON that matches the schema.

PURPOSE:
Before any generated config reaches the CICD pipeline, it needs to pass
validation. If the JSON is missing required fields or has wrong data types,
it gets rejected. This acts as a quality gate between the AI and production.
"""

import json
import jsonschema


def validate_config(config_json_string, schema):
    """
    Checks if a JSON string is valid and matches the schema.

    Parameters:
        config_json_string (str): The raw JSON text the AI generated
        schema (dict): The schema rules to check against

    Returns:
        tuple: (is_valid, parsed_config_or_error_message)
            - If valid:   (True, {the parsed config as a dictionary})
            - If invalid: (False, "description of what's wrong")
    """

    # Step 1: Can the string be parsed as JSON?
    # Sometimes the AI adds extra text like "Here's the config:" before the JSON.
    # This catches that.
    try:
        config = json.loads(config_json_string)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

    # Step 2: Does the parsed JSON match the schema?
    # Checks: are all required fields present? Are the data types correct?
    # Are enum values valid?
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"

    # Both checks passed
    return True, config


# ---- TESTING ----
if __name__ == "__main__":
    # Load the schema
    with open("config_schema.json", "r") as f:
        schema = json.load(f)

    # Test with a valid config
    print("=== Test 1: Valid config ===")
    with open("data/reference_configs/config_acme_corp.json", "r") as f:
        good_config = f.read()
    is_valid, result = validate_config(good_config, schema)
    print(f"Valid: {is_valid}\n")

    # Test with a config missing required fields
    print("=== Test 2: Missing required field ===")
    bad_config = '{"customer_name": "Test"}'
    is_valid, result = validate_config(bad_config, schema)
    print(f"Valid: {is_valid}")
    print(f"Error: {result}\n")

    # Test with broken JSON
    print("=== Test 3: Broken JSON ===")
    broken = 'this is not json at all'
    is_valid, result = validate_config(broken, schema)
    print(f"Valid: {is_valid}")
    print(f"Error: {result}")
