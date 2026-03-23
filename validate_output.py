"""
Station 4: JSON Validation
============================
This file checks if the AI's output is valid JSON that matches the schema.

Think of it like a bouncer at a door — if the JSON is missing required fields
or has the wrong data types, it gets rejected before it can reach the CICD pipeline.
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

    # Step 1: Can we even parse it as JSON?
    # Sometimes the AI adds extra text like "Here's the config:" before the JSON.
    # We need to handle that.
    try:
        config = json.loads(config_json_string)
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"

    # Step 2: Does it match the schema?
    # This checks things like: are all required fields present?
    # Are the data types correct? Are enum values valid?
    try:
        jsonschema.validate(instance=config, schema=schema)
    except jsonschema.ValidationError as e:
        return False, f"Schema validation failed: {e.message}"

    # If we got here, everything is good
    return True, config


# ---- TESTING ----
if __name__ == "__main__":
    # Load the schema
    with open("config_schema.json", "r") as f:
        schema = json.load(f)

    # Test with a GOOD config
    print("=== Test 1: Valid config ===")
    with open("data/reference_configs/config_acme_corp.json", "r") as f:
        good_config = f.read()
    is_valid, result = validate_config(good_config, schema)
    print(f"Valid: {is_valid}\n")

    # Test with a BAD config (missing required field)
    print("=== Test 2: Missing required field ===")
    bad_config = '{"customer_name": "Test"}'
    is_valid, result = validate_config(bad_config, schema)
    print(f"Valid: {is_valid}")
    print(f"Error: {result}\n")

    # Test with BROKEN JSON
    print("=== Test 3: Broken JSON ===")
    broken = 'this is not json at all'
    is_valid, result = validate_config(broken, schema)
    print(f"Valid: {is_valid}")
    print(f"Error: {result}")
