"""
Station 3: Call Gemini
=======================
This file sends the prompt to Gemini and gets a response back.

HOW IT WORKS:
1. First checks for a Gemini API key (free, no GCP needed) — simplest path
2. If no API key, checks for a GCP project and uses Vertex AI
3. If neither is available, falls back to the mock so the demo still works
4. After getting a response, validation happens in validate_output.py
5. If validation fails, a REPAIR step sends the error back to Gemini
   and asks it to fix the JSON

THREE WAYS TO CALL GEMINI (in priority order):
- Gemini Developer API — free API key from aistudio.google.com, no GCP needed
- Vertex AI — requires GCP project + IAM roles + auth
- Mock — heuristic fallback, always works, no external calls

REASON FOR THE FALLBACK:
On dev day, if the API key isn't working or the network is slow, the demo
shouldn't just crash. The fallback provides a working pipeline to demonstrate
while troubleshooting the real connection.
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)


def _clean_response_text(response_text):
    """
    Sometimes the AI wraps its JSON in markdown code fences like ```json ... ```.
    This strips those off so the raw JSON can be parsed.
    """
    cleaned = response_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[len("```json"):].strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:].strip()
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3].strip()
    return cleaned


def call_gemini_api(system_prompt, user_prompt):
    """
    Calls Gemini using the free Developer API (via google-genai SDK).

    This is the simplest way to call Gemini — just an API key, no GCP project,
    no IAM roles, no gcloud auth. Get a key at aistudio.google.com/apikey.

    Uses gemini-2.5-flash which is available on the free tier with generous
    rate limits (15 requests/min, 1500/day).
    """
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY", "")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"{system_prompt}\n\n{user_prompt}",
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    return _clean_response_text(response.text)


def call_gemini_vertex(system_prompt, user_prompt):
    """
    Calls Gemini via Vertex AI (requires GCP project + auth).

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
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )
    return _clean_response_text(response.text)


def call_gemini_mock(system_prompt, user_prompt):
    """
    MOCK VERSION — returns a synthetic response for testing.

    This simulates Gemini by reading keywords from the SOW text and returning
    a reasonable-looking config. It allows the entire app flow to be tested
    (UI → extraction → prompt → response → validation) without any API access.
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
    SCHEMA REPAIR — if the AI's output fails validation, the error is sent
    back to Gemini with a request to fix just the broken parts.

    Tries the API key first, then Vertex AI. If neither is available,
    the original config is returned as-is.
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    repair_prompt = (
        "Fix the following JSON so it conforms to the provided schema. "
        "Change structure only as needed and return valid JSON only.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Validation error:\n{validation_error}\n\n"
        f"Invalid JSON:\n{invalid_json_str}"
    )

    # Try free Gemini API first
    if api_key:
        try:
            from google import genai

            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=repair_prompt,
                config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                },
            )
            return _clean_response_text(response.text)
        except Exception as exc:
            logger.error("Repair via API key failed: %s", exc)

    # Try Vertex AI
    if project and project != "your-gcp-project-id":
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            vertexai.init(project=project, location=location)
            model = GenerativeModel("gemini-3.1-pro")
            response = model.generate_content(
                repair_prompt,
                generation_config={
                    "temperature": 0,
                    "response_mime_type": "application/json",
                },
            )
            return _clean_response_text(response.text)
        except Exception as exc:
            logger.error("Repair via Vertex AI failed: %s", exc)

    return invalid_json_str


def call_gemini(system_prompt, user_prompt):
    """
    Main function the rest of the app calls.

    Priority order:
    1. Gemini Developer API (free, just needs an API key)
    2. Vertex AI (needs GCP project + auth)
    3. Mock fallback (always works, no external calls)
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    project = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    # Option 1: Free Gemini API key
    if api_key:
        try:
            return call_gemini_api(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("Gemini API call failed: %s", exc)

    # Option 2: Vertex AI (GCP project)
    if project and project != "your-gcp-project-id":
        try:
            return call_gemini_vertex(system_prompt, user_prompt)
        except Exception as exc:
            logger.error("Vertex AI call failed: %s", exc)

    # Option 3: Mock fallback
    logger.warning("No API key or GCP project configured. Using mock generator.")
    return call_gemini_mock(system_prompt, user_prompt)
