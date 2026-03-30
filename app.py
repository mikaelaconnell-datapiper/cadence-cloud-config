"""
The Gradio App — The Demo UI
==============================
This is what you run on dev day. It creates a web page with:
- An upload button for the SOW file
- A button to generate the config
- Sanitized text preview (shows PII was redacted)
- The generated JSON output
- Validation status (pass/fail)
- Confidence score (High/Medium/Low)
- Accuracy report (if we have the correct answer to compare against)

TO RUN:
  source venv/bin/activate
  python app.py
Then open http://localhost:7860 in your browser
"""

import json
import os
import gradio as gr

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from extract_pdf import extract_text
from sanitizer import sanitize_text
from build_prompt import load_reference_examples, load_schema, build_system_prompt, build_user_prompt
from call_gemini import call_gemini, repair_config
from validate_output import validate_config
from score_accuracy import score_config, format_report


# --- Load everything when the app starts ---
print("Loading reference examples...")
EXAMPLES = load_reference_examples("data/reference_sows", "data/reference_configs")
print(f"Loaded {len(EXAMPLES)} reference examples\n")

print("Loading schema...")
SCHEMA = load_schema("config_schema.json")
print("Schema loaded\n")

print("Building system prompt...")
SYSTEM_PROMPT = build_system_prompt(EXAMPLES, SCHEMA)
print(f"System prompt ready ({len(SYSTEM_PROMPT)} characters)\n")

# Load eval configs for accuracy scoring
EVAL_CONFIGS = {}
eval_config_dir = "data/eval_configs"
for f in os.listdir(eval_config_dir):
    if f.endswith(".json"):
        with open(os.path.join(eval_config_dir, f), "r") as file:
            config = json.load(file)
            EVAL_CONFIGS[config["customer_name"]] = config
            print(f"Loaded eval config for: {config['customer_name']}")

# Check GCP status
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
if not PROJECT_ID or PROJECT_ID == "your-gcp-project-id":
    print("\nWarning: GOOGLE_CLOUD_PROJECT is not set. Using mock generator.")
else:
    print(f"\nUsing GCP project: {PROJECT_ID}")

print("\nApp ready!\n")


def estimate_confidence(raw_text, sanitized_text, repair_was_attempted):
    """
    Estimates how confident we should be in the generated config.

    High = clean extraction, minimal redaction, no repair needed
    Medium = one minor issue
    Low = multiple issues — flag for human review

    This is a nice-to-have deliverable for the demo.
    """
    issues = []

    # If the PDF extraction got very little text, the config might be unreliable
    if len(raw_text.strip()) < 200:
        issues.append("weak_pdf_extraction")

    # If a lot of content was redacted, the AI had less info to work with
    if sanitized_text.count("[REDACTED") > 10:
        issues.append("heavily_redacted_input")

    # If the AI's first output failed schema validation and needed repair
    if repair_was_attempted:
        issues.append("required_schema_repair")

    if not issues:
        return "High"
    if len(issues) == 1:
        return f"Medium ({issues[0]})"
    return f"Low ({', '.join(issues)})"


def process_sow(file_path):
    """
    Main function — takes the uploaded file through all 5 stations plus
    sanitization, repair, and confidence scoring.

    Gradio passes the file path as a string.
    """
    if file_path is None:
        return "No file uploaded", "", "", "", ""

    # Station 1: Extract text from the PDF/TXT
    try:
        raw_text = extract_text(file_path)
    except (ValueError, Exception):
        try:
            with open(file_path, "r") as f:
                raw_text = f.read()
        except Exception as e:
            return f"Error reading file: {e}", "", "", "", ""

    # Sanitize: Redact PII before sending to the AI
    sanitized_text = sanitize_text(raw_text)

    # Station 2: Build the prompt (using sanitized text, not raw)
    user_prompt = build_user_prompt(sanitized_text)

    # Station 3: Call Gemini (real or mock depending on config)
    raw_response = call_gemini(SYSTEM_PROMPT, user_prompt)

    # Station 4: Validate against the schema
    is_valid, parsed_or_error = validate_config(raw_response, SCHEMA)

    # If validation failed, try the repair step
    repair_attempted = False
    if not is_valid:
        repair_attempted = True
        repaired_response = repair_config(raw_response, str(parsed_or_error), SCHEMA)
        is_valid, parsed_or_error = validate_config(repaired_response, SCHEMA)

        if not is_valid:
            confidence = estimate_confidence(raw_text, sanitized_text, repair_attempted)
            return (
                sanitized_text,
                raw_response,
                f"VALIDATION FAILED: {parsed_or_error}",
                confidence,
                "Cannot score — validation failed",
            )
        # Repair succeeded — use the repaired version
        raw_response = repaired_response

    pretty_json = json.dumps(parsed_or_error, indent=2)

    # Confidence scoring
    confidence = estimate_confidence(raw_text, sanitized_text, repair_attempted)

    # Station 5: Score accuracy (if we have the correct answer)
    customer_name = parsed_or_error.get("customer_name", "")
    if customer_name in EVAL_CONFIGS:
        score_result = score_config(parsed_or_error, EVAL_CONFIGS[customer_name])
        accuracy_report = format_report(score_result)
    else:
        accuracy_report = (
            f"No eval config found for '{customer_name}' — scoring skipped.\n"
            "(Normal for reference SOWs. Scoring works for eval SOWs.)"
        )

    validation_status = "PASSED — all required fields present, types correct"
    if repair_attempted:
        validation_status += " (after schema repair)"

    return sanitized_text, pretty_json, validation_status, confidence, accuracy_report


# --- Build the Gradio UI ---
with gr.Blocks(title="Cloud Config Agent — Cadence Dev Day", theme=gr.themes.Soft()) as app:

    gr.Markdown("# Cloud Config Right Sizing Agent")
    gr.Markdown(
        "Upload a SOW document to generate a chamber configuration for the CICD pipeline. "
        "Sensitive data is automatically redacted before processing."
    )

    with gr.Row():
        with gr.Column():
            file_input = gr.File(label="Upload SOW (PDF or TXT)", file_types=[".pdf", ".txt"])
            run_button = gr.Button("Generate Config", variant="primary")
            sow_output = gr.Textbox(label="Sanitized SOW Text", lines=14, interactive=False)

        with gr.Column():
            validation_output = gr.Textbox(label="Validation Status", lines=2, interactive=False)
            confidence_output = gr.Textbox(label="Confidence / Review Flag", interactive=False)
            accuracy_output = gr.Textbox(label="Accuracy Report", lines=14, interactive=False)

        with gr.Column():
            config_output = gr.Code(label="Generated Config JSON", language="json", interactive=False)

    run_button.click(
        fn=process_sow,
        inputs=file_input,
        outputs=[sow_output, config_output, validation_output, confidence_output, accuracy_output],
    )

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
