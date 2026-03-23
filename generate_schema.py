"""
Schema Generator
=================
This script takes one or more example JSON config files and automatically
generates a JSON schema from them.

HOW IT WORKS (step by step):
1. You point it at a folder of real config files from Cadence
2. It reads every config file and looks at every field
3. For each field, it figures out:
   - What type is it? (string, number, boolean, list, object)
   - What values has it seen? (to suggest enums/constraints)
   - Does every config file have this field? (if yes → required)
4. It outputs a JSON schema file you can use for validation

USAGE:
  python generate_schema.py --input-dir data/reference_configs --output config_schema.json
"""

import json
import os
import argparse


def infer_type(value):
    """
    Look at a Python value and figure out what JSON type it is.

    This is like asking "what kind of thing is this?"
      - "hello"      → string
      - 42           → integer
      - 3.14         → number (decimal)
      - true/false   → boolean
      - [1, 2, 3]    → array (a list)
      - {"key": val} → object (a nested structure)
    """
    if isinstance(value, bool):
        # IMPORTANT: check bool BEFORE int, because in Python,
        # True/False are technically also integers (weird, I know)
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif value is None:
        return "null"
    else:
        return "string"  # fallback


def analyze_field(values):
    """
    Given a list of values that a field has across ALL config files,
    figure out the schema rules for that field.

    Example: if "environment_tier" has values ["small", "medium", "large"]
    across 3 configs, we know:
      - type: string
      - enum: ["small", "medium", "large"]  (only these values are valid)
    """
    # Figure out the type from the first non-None value
    field_type = "string"
    for v in values:
        if v is not None:
            field_type = infer_type(v)
            break

    result = {"type": field_type}

    # For strings: collect all unique values we've seen
    # If there are only a few unique values, suggest them as an enum
    if field_type == "string":
        unique_values = list(set(v for v in values if v is not None))
        if 1 < len(unique_values) <= 10:
            # Few enough unique values that it might be an enum
            result["_observed_values"] = sorted(unique_values)

    # For numbers: find the min and max we've seen
    if field_type in ("integer", "number"):
        numeric_values = [v for v in values if isinstance(v, (int, float))]
        if numeric_values:
            result["_observed_min"] = min(numeric_values)
            result["_observed_max"] = max(numeric_values)

    return result


def build_schema_from_configs(config_files):
    """
    The main function. Takes a list of config file paths,
    reads them all, and builds a schema.

    Think of it like this:
    - Read 5 filled-out forms
    - Figure out what the blank form template should look like
    """

    # Step 1: Load all config files into memory
    all_configs = []
    for filepath in config_files:
        with open(filepath, "r") as f:
            config = json.load(f)
            all_configs.append(config)
            print(f"  Loaded: {os.path.basename(filepath)}")

    if not all_configs:
        print("No config files found!")
        return None

    print(f"\n  Analyzing {len(all_configs)} config files...\n")

    # Step 2: Collect all field names and their values across every config
    # This is like looking at all the forms and noting what fields exist
    field_values = {}    # field_name → [list of values from each config]
    field_presence = {}  # field_name → how many configs have this field

    for config in all_configs:
        for key, value in config.items():
            if key not in field_values:
                field_values[key] = []
                field_presence[key] = 0
            field_values[key].append(value)
            field_presence[key] += 1

    # Step 3: Build the schema
    total_configs = len(all_configs)
    properties = {}
    required = []

    for field_name, values in field_values.items():
        # Analyze this field
        field_schema = analyze_field(values)

        # If every single config has this field, it's required
        if field_presence[field_name] == total_configs:
            required.append(field_name)
            print(f"  ✓ {field_name}: {field_schema['type']} (REQUIRED - in all {total_configs} configs)")
        else:
            print(f"  ○ {field_name}: {field_schema['type']} (optional - in {field_presence[field_name]}/{total_configs} configs)")

        # If it's an object (nested structure), note that it needs deeper analysis
        if field_schema["type"] == "object":
            # Recursively analyze nested objects
            nested_values = [v for v in values if isinstance(v, dict)]
            nested_keys = set()
            for nv in nested_values:
                nested_keys.update(nv.keys())
            field_schema["properties"] = {}
            nested_required = []
            for nk in sorted(nested_keys):
                nk_values = [nv.get(nk) for nv in nested_values if nk in nv]
                field_schema["properties"][nk] = analyze_field(nk_values)
                # If this nested key appears in all nested objects, it's required
                nk_count = sum(1 for nv in nested_values if nk in nv)
                if nk_count == len(nested_values):
                    nested_required.append(nk)
            if nested_required:
                field_schema["required"] = nested_required

        # If it's an array (list), analyze what's inside the list
        if field_schema["type"] == "array":
            all_items = []
            for v in values:
                if isinstance(v, list):
                    all_items.extend(v)
            if all_items and isinstance(all_items[0], dict):
                # It's a list of objects — figure out the object structure
                item_keys = set()
                for item in all_items:
                    if isinstance(item, dict):
                        item_keys.update(item.keys())
                item_properties = {}
                item_required = []
                for ik in sorted(item_keys):
                    ik_values = [item.get(ik) for item in all_items if isinstance(item, dict) and ik in item]
                    item_properties[ik] = analyze_field(ik_values)
                    ik_count = sum(1 for item in all_items if isinstance(item, dict) and ik in item)
                    if ik_count == len(all_items):
                        item_required.append(ik)
                field_schema["items"] = {
                    "type": "object",
                    "properties": item_properties,
                }
                if item_required:
                    field_schema["items"]["required"] = item_required

        # Clean up internal-only fields (the ones starting with _)
        clean_schema = {k: v for k, v in field_schema.items() if not k.startswith("_")}

        # Add helpful comments based on what we observed
        if "_observed_values" in field_schema:
            clean_schema["description"] = f"Observed values: {field_schema['_observed_values']}"
        if "_observed_min" in field_schema:
            clean_schema["minimum"] = field_schema["_observed_min"]

        properties[field_name] = clean_schema

    # Step 4: Assemble the final schema
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Auto-Generated Chamber Configuration Schema",
        "description": f"Generated from {total_configs} example config files",
        "type": "object",
        "required": sorted(required),
        "properties": properties,
    }

    return schema


def main():
    # argparse lets us accept command-line arguments
    # so you can run: python generate_schema.py --input-dir some/folder
    parser = argparse.ArgumentParser(
        description="Generate a JSON schema from example config files"
    )
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Folder containing example JSON config files",
    )
    parser.add_argument(
        "--output",
        default="generated_schema.json",
        help="Where to save the generated schema (default: generated_schema.json)",
    )

    args = parser.parse_args()

    # Find all .json files in the input directory
    config_files = []
    for filename in sorted(os.listdir(args.input_dir)):
        if filename.endswith(".json"):
            config_files.append(os.path.join(args.input_dir, filename))

    print(f"\nFound {len(config_files)} config files in {args.input_dir}\n")

    # Build the schema
    schema = build_schema_from_configs(config_files)

    if schema:
        # Save it
        with open(args.output, "w") as f:
            json.dump(schema, f, indent=2)
        print(f"\n  Schema saved to: {args.output}")
        print(f"  Required fields: {schema['required']}")
        print(f"  Total fields: {len(schema['properties'])}")


if __name__ == "__main__":
    main()
