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

    # Critical fields to evaluate for Cadence chamber configs
    # Each tuple is (field_name, parent_key) — parent_key is None for top-level fields
    # For nested lists (like hardware.interactive_servers), comparison is done separately below
    critical_fields = [
        ("platform_provider", None),
        ("chamber_location", None),
        ("third_party_licence_chamber_required", None),
        ("total_users", None),
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

    # Check hardware — compare first interactive server details
    gen_servers = generated.get("hardware", {}).get("interactive_servers", [])
    exp_servers = expected.get("hardware", {}).get("interactive_servers", [])

    if exp_servers:
        exp_server = exp_servers[0]
        gen_server = gen_servers[0] if gen_servers else {}

        for field in ["count", "instance_type", "vcpus", "memory_gb"]:
            gen_val = gen_server.get(field)
            exp_val = exp_server.get(field)
            is_match = gen_val == exp_val
            if is_match:
                matched += 1
            total += 1
            details.append({
                "field": f"hardware.interactive_servers[0].{field}",
                "expected": exp_val,
                "generated": gen_val,
                "match": is_match,
            })

    # Check storage
    gen_storage = generated.get("hardware", {}).get("storage", {})
    exp_storage = expected.get("hardware", {}).get("storage", {})

    for field in ["backup_storage_gb", "scratch_storage_gb"]:
        gen_val = gen_storage.get(field)
        exp_val = exp_storage.get(field)
        if exp_val is not None:
            is_match = gen_val == exp_val
            if is_match:
                matched += 1
            total += 1
            details.append({
                "field": f"hardware.storage.{field}",
                "expected": exp_val,
                "generated": gen_val,
                "match": is_match,
            })

    # Check software licenses — compare product names and quantities
    gen_licenses = {item["product_name"]: item["quantity"]
                    for item in generated.get("software_licenses", [])}
    exp_licenses = {item["product_name"]: item["quantity"]
                    for item in expected.get("software_licenses", [])}

    # Check each expected license
    all_products = sorted(set(list(exp_licenses.keys()) + list(gen_licenses.keys())))
    license_matched = 0
    license_total = 0

    for product in all_products:
        exp_qty = exp_licenses.get(product)
        gen_qty = gen_licenses.get(product)
        is_match = exp_qty == gen_qty
        if is_match:
            license_matched += 1
        license_total += 1
        details.append({
            "field": f"license: {product}",
            "expected": exp_qty,
            "generated": gen_qty,
            "match": is_match,
        })

    matched += license_matched
    total += license_total

    # Check user accounts
    gen_accounts = sorted(
        [(a.get("count"), a.get("location")) for a in generated.get("user_accounts", [])],
        key=lambda x: str(x[1])
    )
    exp_accounts = sorted(
        [(a.get("count"), a.get("location")) for a in expected.get("user_accounts", [])],
        key=lambda x: str(x[1])
    )
    accounts_match = gen_accounts == exp_accounts
    if accounts_match:
        matched += 1
    total += 1
    details.append({
        "field": "user_accounts",
        "expected": exp_accounts,
        "generated": gen_accounts,
        "match": accounts_match,
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
    lines.append(f"{'Field':<45} {'Expected':<20} {'Generated':<20} {'Match'}")
    lines.append("-" * 95)

    for d in score_result["details"]:
        exp = str(d["expected"])[:18]
        gen = str(d["generated"])[:18]
        match_icon = "YES" if d["match"] else "** NO **"
        lines.append(f"{d['field']:<45} {exp:<20} {gen:<20} {match_icon}")

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
    # Test with a sample config against itself (should be 100%)
    sample = {
        "platform_provider": "AWS",
        "chamber_location": "AWS Frankfurt",
        "third_party_licence_chamber_required": True,
        "total_users": 10,
        "user_accounts": [
            {"count": 5, "location": "Berlin Germany"},
            {"count": 5, "location": "Istanbul Turkiye"}
        ],
        "hardware": {
            "interactive_servers": [
                {"count": 1, "instance_type": "M6i.4xlarge", "vcpus": 16, "memory_gb": 64}
            ],
            "storage": {"backup_storage_gb": 1000, "scratch_storage_gb": 1000}
        },
        "software_licenses": [
            {"product_name": "Virtuoso Schematic Editor L", "quantity": 3},
            {"product_name": "Spectre MMSIM with Spectre X Simulator", "quantity": 9}
        ]
    }
    result = score_config(sample, sample)
    print(f"Self-comparison: {result['accuracy']}% ({result['matched_fields']}/{result['total_fields']})")
    print(format_report(result))
