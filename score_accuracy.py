"""
Station 5: Accuracy Scoring
==============================
This file compares the AI's generated config to a known-good config
and reports accuracy field by field.

PURPOSE:
Knowing that the JSON is valid (passes schema) is not enough — the values
also need to be correct. This module checks each critical field against the
expected answer and produces a percentage score and detailed report.
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
            - total_fields: how many fields were checked
            - matched_fields: how many matched the expected value
            - accuracy: percentage (0-100)
            - details: list of per-field results
    """

    details = []

    # Critical fields to evaluate
    # Each tuple is (field_name, parent_key) — parent_key is None for top-level fields
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
        # If the field is nested (e.g., compute.instance_type), look inside the parent first
        if parent_key:
            gen_value = generated.get(parent_key, {}).get(field_name)
            exp_value = expected.get(parent_key, {}).get(field_name)
        else:
            gen_value = generated.get(field_name)
            exp_value = expected.get(field_name)

        # Compare the values
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

    # Also check services (compare sorted service name lists)
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
    Returns the accuracy report as plain text (fallback format).
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


def format_report_html(score_result):
    """
    Returns the accuracy report as a styled HTML table for the Gradio UI.
    Color-coded rows: green for matches, red for mismatches.
    """
    accuracy = score_result["accuracy"]
    matched = score_result["matched_fields"]
    total = score_result["total_fields"]

    # Color the accuracy badge based on score
    if accuracy >= 80:
        badge_color = "#16a34a"  # green
    elif accuracy >= 60:
        badge_color = "#ca8a04"  # yellow
    else:
        badge_color = "#dc2626"  # red

    html = f"""
    <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
    <div style="font-family: 'Google Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 14px; letter-spacing: 0.01em;">
      <div style="margin-bottom: 16px;">
        <span style="background: {badge_color}; color: white; padding: 6px 14px;
               border-radius: 6px; font-weight: 600; font-size: 15px;">
          {accuracy}% Accuracy
        </span>
        <span style="color: #6b7280; margin-left: 10px; font-size: 13px;">
          {matched} / {total} fields matched
        </span>
      </div>
      <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
        <thead>
          <tr style="border-bottom: 2px solid #e5e7eb;">
            <th style="text-align: left; padding: 8px 10px; color: #374151; font-weight: 600;">Field</th>
            <th style="text-align: left; padding: 8px 10px; color: #374151; font-weight: 600;">Expected</th>
            <th style="text-align: left; padding: 8px 10px; color: #374151; font-weight: 600;">Generated</th>
            <th style="text-align: center; padding: 8px 10px; color: #374151; font-weight: 600;">Match</th>
          </tr>
        </thead>
        <tbody>
    """

    for d in score_result["details"]:
        exp = str(d["expected"])
        gen = str(d["generated"])
        if d["match"]:
            icon = "&#10003;"  # checkmark
            icon_color = "#16a34a"
            row_bg = "#f0fdf4"
        else:
            icon = "&#10007;"  # X mark
            icon_color = "#dc2626"
            row_bg = "#fef2f2"

        html += f"""
          <tr style="background: {row_bg}; border-bottom: 1px solid #f3f4f6;">
            <td style="padding: 7px 10px; font-weight: 500; color: #1f2937;">{d['field']}</td>
            <td style="padding: 7px 10px; color: #4b5563;">{exp}</td>
            <td style="padding: 7px 10px; color: #4b5563;">{gen}</td>
            <td style="padding: 7px 10px; text-align: center; color: {icon_color}; font-size: 16px; font-weight: 700;">{icon}</td>
          </tr>
        """

    html += """
        </tbody>
      </table>
    </div>
    """
    return html


# ---- TESTING ----
if __name__ == "__main__":
    # Compare the Nimbus eval config against itself (should be 100%)
    with open("data/eval_configs/config_nimbus_retail.json", "r") as f:
        expected = json.load(f)

    print("=== Test: Perfect match (config vs itself) ===\n")
    result = score_config(expected, expected)
    print(format_report(result))
