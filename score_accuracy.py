"""
Station 5: Accuracy Scoring
==============================
This file compares the AI's generated config to the known-good config
and tells you how accurate it was, field by field.

Think of it like grading a test — for each field, did the AI get the
right answer? What's the overall score?
"""

import json


def score_config(generated, expected):
    """
    Compares two configs field by field and returns an accuracy report.

    Parameters:
        generated (dict): The config the AI produced
        expected (dict): The known-good config (the correct answer)

    Returns:
        dict with:
            - total_fields: how many fields we checked
            - matched_fields: how many the AI got right
            - accuracy: percentage (0-100)
            - details: list of per-field results
    """

    details = []

    # These are the critical fields we care most about
    # (from the use case requirements)
    critical_fields = [
        ("environment_tier", None),
        ("instance_type", "compute"),
        ("instance_count", "compute"),
        ("vcpus_per_instance", "compute"),
        ("memory_gb_per_instance", "compute"),
        ("storage_type", "storage"),
        ("total_storage_gb", "storage"),
        ("iops_required", "storage"),
        ("vpc_cidr", "networking"),
        ("subnet_count", "networking"),
        ("load_balancer", "networking"),
        ("high_availability", None),
        ("backup_enabled", None),
        ("estimated_users", None),
    ]

    matched = 0
    total = 0

    for field_name, parent_key in critical_fields:
        # Get the value from both configs
        if parent_key:
            gen_value = generated.get(parent_key, {}).get(field_name)
            exp_value = expected.get(parent_key, {}).get(field_name)
        else:
            gen_value = generated.get(field_name)
            exp_value = expected.get(field_name)

        # Compare them
        is_match = gen_value == exp_value
        if is_match:
            matched += 1
        total += 1

        details.append({
            "field": f"{parent_key}.{field_name}" if parent_key else field_name,
            "expected": exp_value,
            "generated": gen_value,
            "match": is_match,
        })

    # Also check services (just count and names)
    gen_services = sorted([s["service_name"] for s in generated.get("services", [])])
    exp_services = sorted([s["service_name"] for s in expected.get("services", [])])

    services_match = gen_services == exp_services
    if services_match:
        matched += 1
    total += 1

    details.append({
        "field": "services (names)",
        "expected": exp_services,
        "generated": gen_services,
        "match": services_match,
    })

    accuracy = (matched / total * 100) if total > 0 else 0

    return {
        "total_fields": total,
        "matched_fields": matched,
        "accuracy": round(accuracy, 1),
        "details": details,
    }


def format_report(score_result):
    """
    Takes the score result and returns a nicely formatted string report.
    This is what we'll display in the Gradio UI.
    """
    lines = []
    lines.append(f"ACCURACY: {score_result['accuracy']}% ({score_result['matched_fields']}/{score_result['total_fields']} fields)")
    lines.append("")
    lines.append(f"{'Field':<35} {'Expected':<20} {'Generated':<20} {'Match'}")
    lines.append("-" * 85)

    for d in score_result["details"]:
        exp = str(d["expected"])[:18]
        gen = str(d["generated"])[:18]
        match_icon = "YES" if d["match"] else "** NO **"
        lines.append(f"{d['field']:<35} {exp:<20} {gen:<20} {match_icon}")

    return "\n".join(lines)


# ---- TESTING ----
if __name__ == "__main__":
    # Compare the Nimbus eval config against itself (should be 100%)
    with open("data/eval_configs/config_nimbus_retail.json", "r") as f:
        expected = json.load(f)

    print("=== Test: Perfect match (config vs itself) ===\n")
    result = score_config(expected, expected)
    print(format_report(result))
