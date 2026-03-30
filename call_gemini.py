"""
Station 3: Call Gemini
=======================
This file is where we send our prompt to Gemini and get a response.

HOW IT WORKS:
1. If you have a GCP project configured, it calls the REAL Gemini API via Vertex AI
2. If Gemini isn't available (no project, no auth, API error), it falls back to the
   mock version so the demo still works
3. After getting a response, it validates against the schema
4. If validation fails, it tries a REPAIR step — sends the error back to Gemini
   and asks it to fix the JSON

WHY THE FALLBACK?
On dev day, if GCP access isn't ready or the API is slow, you don't want the demo
to just crash. The fallback gives you a working pipeline to show while you troubleshoot.
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)


def _clean_response_text(response_text):
    """
    Sometimes the AI wraps its JSON in markdown code fences like ```json ... ```.
    This strips those off so we can parse the raw JSON.
    """
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def call_gemini_real(system_prompt, user_prompt):
    """
    REAL VERSION — calls Gemini via Vertex AI.

    Uses the project ID and location from environment variables.
    The response_mime_type="application/json" tells Gemini to ONLY return JSON,
    which reduces the chance of getting markdown or explanations mixed in.
    """
    import vertexai
    from vertexai.generative_models import GenerativeModel

    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

    vertexai.init(project=project, location=location)
    model = GenerativeModel("gemini-3.1-pro", system_instruction=[system_prompt])
    chat = model.start_chat()
    response = chat.send_message(
        user_prompt,
        generation_config={
            "temperature": 0.2,  # Low temperature = more consistent output
            "response_mime_type": "application/json",  # Forces JSON-only response
        },
    )
    return _clean_response_text(response.text)


def call_gemini_mock(system_prompt, user_prompt):
    """
    MOCK VERSION — returns a fake response for testing.

    This pretends to be Gemini. It reads keywords from the SOW text
    and returns a reasonable-looking config. This lets us test the
    entire app flow (UI -> extraction -> prompt -> response -> validation)
    without needing GCP access.
    """
    sow_text = user_prompt.lower()

    # Try to figure out the customer name from the SOW
    customer_name = "Unknown Customer"
    if "client:" in sow_text:
        for line in user_prompt.split("\n"):
            if "Client:" in line:
                customer_name = line.split("Client:")[1].strip()
                break

    # Guess the tier based on user count mentioned in the SOW
    tier = "medium"
    estimated_users = 100
    if "1000" in sow_text or "1,000" in sow_text:
        tier = "enterprise"
        estimated_users = 1000
    elif "500" in sow_text:
        tier = "medium"
        estimated_users = 500
    elif "200" in sow_text:
        tier = "medium"
        estimated_users = 200
    elif "50" in sow_text:
        tier = "small"
        estimated_users = 50

    # Check for high availability keywords
    ha = "high availability" in sow_text and "not required" not in sow_text

    # Check for load balancer
    lb = "load balancer" in sow_text

    # Guess storage type
    storage_type = "pd-ssd" if "ssd" in sow_text else "pd-standard"

    # Build a mock config response
    mock_config = {
        "customer_name": customer_name,
        "environment_tier": tier,
        "compute": {
            "instance_type": "n2-standard-4" if tier in ("small", "medium") else "n2-standard-8",
            "instance_count": 2 if tier == "small" else 3 if tier == "medium" else 4,
            "vcpus_per_instance": 4 if tier in ("small", "medium") else 8,
            "memory_gb_per_instance": 16 if tier in ("small", "medium") else 32,
        },
        "storage": {
            "storage_type": storage_type,
            "total_storage_gb": 500 if tier == "small" else 750 if tier == "medium" else 2000,
            "iops_required": 1500 if tier == "small" else 3000 if tier == "medium" else 5000,
        },
        "networking": {
            "vpc_cidr": "10.0.0.0/16",
            "subnet_count": 2 if tier == "small" else 3,
            "load_balancer": lb,
        },
        "services": [
            {"service_name": "Cloud SQL", "enabled": True, "configuration": {}},
            {"service_name": "Cloud Monitoring", "enabled": True, "configuration": {}},
        ],
        "high_availability": ha,
        "backup_enabled": True,
        "estimated_users": estimated_users,
    }

    return json.dumps(mock_config, indent=2)


def repair_config(invalid_json_str, validation_error, schema):
    """
    SCHEMA REPAIR — if the AI's output fails validation, send the error
    back to Gemini and ask it to fix just the broken parts.

    This only works with a real GCP connection. If we're using the mock,
    we just return the original (broken) config as-is.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    if not project or project == "your-gcp-project-id":
        return invalid_json_str

    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        vertexai.init(project=project, location=location)
        model = GenerativeModel("gemini-3.1-pro")

        prompt = (
            "Fix the following JSON so it conforms to the provided schema. "
            "Change structure only as needed and return valid JSON only.\n\n"
            f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
            f"Validation error:\n{validation_error}\n\n"
            f"Invalid JSON:\n{invalid_json_str}"
        )
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json",
            },
        )
        return _clean_response_text(response.text)
    except Exception as exc:
        logger.error("Repair attempt failed: %s", exc)
        return invalid_json_str


def call_gemini(system_prompt, user_prompt):
    """
    Main function the rest of the app calls.

    Tries the real Gemini API first. If anything goes wrong (no project,
    no auth, API error), falls back to the mock so the demo keeps working.
    """
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # If no project is configured, go straight to mock
    if not project or project == "your-gcp-project-id":
        logger.warning("No GCP project configured. Using mock generator.")
        return call_gemini_mock(system_prompt, user_prompt)

    # Try the real API
    try:
        return call_gemini_real(system_prompt, user_prompt)
    except Exception as exc:
        logger.error("Vertex AI call failed, falling back to mock: %s", exc)
        return call_gemini_mock(system_prompt, user_prompt)
