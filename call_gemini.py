"""
Station 3: Call Gemini (MOCK VERSION)
======================================
This file is where we send our prompt to Gemini and get a response.

RIGHT NOW: It returns a fake (mock) response so we can test everything
without needing GCP access.

ON DEV DAY: You'll replace the mock function with the real Gemini API call.
It's literally swapping one function — everything else stays the same.
"""

import json


def call_gemini_mock(system_prompt, user_prompt):
    """
    MOCK VERSION — returns a fake response for testing.

    This pretends to be Gemini. It reads keywords from the SOW text
    and returns a reasonable-looking config. This lets us test the
    entire app flow (UI → extraction → prompt → response → validation)
    without needing GCP access.
    """

    # Look for clues in the user prompt to generate a semi-realistic response
    sow_text = user_prompt.lower()

    # Try to figure out the customer name from the SOW
    customer_name = "Unknown Customer"
    if "client:" in sow_text:
        # Find the line that starts with "client:"
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


def call_gemini_real(system_prompt, user_prompt):
    """
    REAL VERSION — uncomment and use this on dev day when you have GCP access.

    You'll need to:
    1. pip install google-cloud-aiplatform
    2. Be authenticated to your GCP project
    3. Replace MODEL_NAME with whatever the team tells you to use
    """
    # from google.cloud import aiplatform
    # import vertexai
    # from vertexai.generative_models import GenerativeModel
    #
    # vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")
    # model = GenerativeModel("MODEL_NAME")  # Ask your team which model
    #
    # response = model.generate_content(
    #     [system_prompt, user_prompt],
    #     generation_config={"temperature": 0}  # 0 = most consistent output
    # )
    #
    # return response.text
    pass


# This is the function the rest of the app calls.
# Switch this to call_gemini_real when you have GCP access.
def call_gemini(system_prompt, user_prompt):
    return call_gemini_mock(system_prompt, user_prompt)
