"""
Station 2: Prompt Builder
==========================
This file builds the message (prompt) that gets sent to the AI.

THE BIG IDEA:
Imagine training a new employee to do a task. Instead of saying "figure it out,"
showing them 3 examples of completed work first and then saying "now do this one
the same way" is much more effective. That's exactly what few-shot prompting is.

The prompt has 2 parts:
1. SYSTEM PROMPT — the instructions and examples (stays the same every time)
2. USER PROMPT — the new SOW to process (changes each time)
"""

import json
import os
from extract_pdf import extract_text


def load_reference_examples(sow_dir, config_dir):
    """
    Loads all the reference SOW/config pairs from the data folders.

    These are the "training examples" shown to the AI — each one is a pair
    of (SOW text, config JSON) that demonstrates the expected input→output mapping.

    Parameters:
        sow_dir: folder with reference SOW files
        config_dir: folder with matching config JSON files

    Returns:
        list of tuples: [(sow_text, config_json), (sow_text, config_json), ...]
    """
    examples = []

    # Get all SOW files, sorted so the order is consistent
    sow_files = sorted([f for f in os.listdir(sow_dir) if f.startswith("sow_")])

    for sow_file in sow_files:
        # Figure out the matching config file name
        # "sow_acme_corp.txt" → "config_acme_corp.json"
        #
        # How this works:
        #   1. sow_file = "sow_acme_corp.txt"
        #   2. Remove "sow_" from the front → "acme_corp.txt"
        #   3. Remove the file extension → "acme_corp"
        #   4. Add "config_" to the front and ".json" to the end → "config_acme_corp.json"
        base_name = sow_file.replace("sow_", "").rsplit(".", 1)[0]
        config_file = f"config_{base_name}.json"
        config_path = os.path.join(config_dir, config_file)

        # Make sure the matching config actually exists
        if not os.path.exists(config_path):
            print(f"  Warning: No matching config for {sow_file}, skipping")
            continue

        # Read the SOW text
        sow_path = os.path.join(sow_dir, sow_file)
        sow_text = extract_text(sow_path)

        # Read the config JSON
        with open(config_path, "r") as f:
            config_json = json.load(f)

        examples.append((sow_text, config_json))
        print(f"  Loaded example: {sow_file} → {config_file}")

    return examples


def load_schema(schema_path):
    """
    Loads the JSON schema file that defines what the output must look like.
    """
    with open(schema_path, "r") as f:
        return json.load(f)


def build_system_prompt(examples, schema):
    """
    Builds the system prompt — the instructions for the AI.

    This is the most critical function in the project. The quality of this prompt
    directly determines how good the AI's output will be.

    The system prompt tells the AI:
    1. Its role (a cloud config expert)
    2. Its task (parse SOWs, generate configs)
    3. The output format (the JSON schema)
    4. Reference examples (the few-shot examples)
    5. Rules to follow (validation, no hallucination, etc.)
    """

    # Start with the role and task description
    prompt = """You are a cloud infrastructure configuration expert at Cadence.

YOUR TASK:
You will receive a customer Statement of Work (SOW) document. You must analyze it
and generate a chamber configuration JSON that can be fed directly into the CICD
deployment pipeline.

OUTPUT FORMAT:
Your output must be ONLY valid JSON — no explanations, no markdown, no extra text.
The JSON must conform to this schema:

"""
    # Add the schema so the AI knows the exact structure
    prompt += json.dumps(schema, indent=2)

    prompt += """

RULES:
1. Extract ALL relevant information from the SOW — instance sizes, storage, networking, services.
2. Output ONLY the JSON configuration. No markdown code fences, no explanations.
3. Every required field in the schema MUST be present.
4. Choose instance_type based on the vCPU and memory requirements in the SOW.
5. Set environment_tier based on overall scale: small (<100 users), medium (100-499), large (500-999), enterprise (1000+).
6. Only include services explicitly mentioned in the SOW.
7. If a value is not specified in the SOW, make a reasonable inference based on the examples below.

REFERENCE EXAMPLES:
Below are real examples of SOW documents and their correct configurations.
Study these carefully to understand the mapping pattern.

"""

    # Add each reference example
    for i, (sow_text, config_json) in enumerate(examples, 1):
        prompt += f"--- EXAMPLE {i} ---\n"
        prompt += f"SOW DOCUMENT:\n{sow_text}\n\n"
        prompt += f"CORRECT CONFIGURATION:\n{json.dumps(config_json, indent=2)}\n\n"

    return prompt


def build_user_prompt(new_sow_text):
    """
    Builds the user prompt — the new SOW that needs to be processed.

    This is straightforward — just the SOW text with a clear instruction.
    """
    prompt = f"""Analyze the following SOW document and generate the chamber configuration JSON.
Output ONLY the JSON — no other text.

SOW DOCUMENT:
{new_sow_text}"""

    return prompt


# ---- TESTING ----
if __name__ == "__main__":
    print("Loading reference examples...\n")
    examples = load_reference_examples(
        "data/reference_sows",
        "data/reference_configs"
    )
    print(f"\nLoaded {len(examples)} examples\n")

    schema = load_schema("config_schema.json")
    print(f"Loaded schema with {len(schema['properties'])} fields\n")

    system_prompt = build_system_prompt(examples, schema)
    print(f"System prompt length: {len(system_prompt)} characters")
    print(f"That's roughly {len(system_prompt) // 4} tokens")
    print("\n=== First 500 chars of system prompt ===\n")
    print(system_prompt[:500])
