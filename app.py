"""
The Gradio App — The Demo UI
==============================
Three tabs for different workflows:

Tab 1: SANITIZE — Upload a SOW PDF, get sanitized text to copy into Agent Designer
Tab 2: VALIDATE & SCORE — Paste JSON from Agent Designer, validate + score it
Tab 3: FULL PIPELINE — Upload PDF, run everything end to end with Gemini API

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
from score_accuracy import score_config, format_report, format_report_html


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

# Check API status
API_KEY = os.getenv("GEMINI_API_KEY", "")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
if API_KEY:
    print(f"\nUsing Gemini API key: {API_KEY[:10]}...")
elif PROJECT_ID and PROJECT_ID != "your-gcp-project-id":
    print(f"\nUsing GCP project: {PROJECT_ID}")
else:
    print("\nNo API key or GCP project set. Full Pipeline tab will use mock generator.")

print("\nApp ready!\n")


# =============================================
# TAB 1: SANITIZE
# =============================================
def sanitize_sow(file_path):
    """
    Takes a SOW PDF/TXT, extracts text, redacts PII.
    Returns the sanitized text ready to copy into Agent Designer.
    """
    if file_path is None:
        return "Please upload a SOW document.", ""

    try:
        raw_text = extract_text(file_path)
    except (ValueError, Exception):
        try:
            with open(file_path, "r") as f:
                raw_text = f.read()
        except Exception as e:
            return f"Error reading file: {e}", ""

    if not raw_text.strip():
        return "No text could be extracted from this file.", ""

    sanitized = sanitize_text(raw_text)
    return raw_text, sanitized


# =============================================
# TAB 2: VALIDATE & SCORE
# =============================================
def validate_and_score(json_text):
    """
    Takes raw JSON text (pasted from Agent Designer), validates it
    against the schema, and scores accuracy if an eval config exists.
    """
    if not json_text or not json_text.strip():
        return "Please paste a JSON config.", ""

    # Try to parse the JSON
    is_valid, parsed_or_error = validate_config(json_text, SCHEMA)

    if not is_valid:
        return f"VALIDATION FAILED: {parsed_or_error}", ""

    validation_status = "PASSED — all required fields present, types correct"
    pretty_json = json.dumps(parsed_or_error, indent=2)

    # Score accuracy if we have a known-good config
    customer_name = parsed_or_error.get("customer_name", "")
    if customer_name in EVAL_CONFIGS:
        score_result = score_config(parsed_or_error, EVAL_CONFIGS[customer_name])
        accuracy_report = format_report_html(score_result)
    else:
        accuracy_report = (
            "<div style='font-family: Google Sans, Helvetica Neue, Helvetica, Arial, sans-serif; "
            "color: #6b7280; font-size: 14px;'>"
            f"No eval config found for '{customer_name}' — scoring skipped.<br>"
            "<span style='font-size: 12px;'>(Upload a known-good config JSON to enable scoring.)</span>"
            "</div>"
        )

    return validation_status, accuracy_report


def validate_with_eval(json_text, eval_file):
    """
    Same as validate_and_score but also accepts a known-good config
    file for accuracy scoring (for SOWs not in our eval set).
    """
    if not json_text or not json_text.strip():
        return "Please paste a JSON config.", ""

    is_valid, parsed_or_error = validate_config(json_text, SCHEMA)

    if not is_valid:
        return f"VALIDATION FAILED: {parsed_or_error}", ""

    validation_status = "PASSED — all required fields present, types correct"

    # Try scoring with uploaded eval file first, then fall back to built-in
    if eval_file is not None:
        try:
            with open(eval_file.name, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
            expected = eval_data.get("expected_config", eval_data)
            score_result = score_config(parsed_or_error, expected)
            accuracy_report = format_report_html(score_result)
            return validation_status, accuracy_report
        except Exception as exc:
            return validation_status, f"<div style='color: #dc2626;'>Error reading eval file: {exc}</div>"

    # Fall back to built-in eval configs
    customer_name = parsed_or_error.get("customer_name", "")
    if customer_name in EVAL_CONFIGS:
        score_result = score_config(parsed_or_error, EVAL_CONFIGS[customer_name])
        accuracy_report = format_report_html(score_result)
    else:
        accuracy_report = (
            "<div style='font-family: Google Sans, Helvetica Neue, Helvetica, Arial, sans-serif; "
            "color: #6b7280; font-size: 14px;'>"
            f"No eval config found for '{customer_name}' — scoring skipped.<br>"
            "<span style='font-size: 12px;'>(Upload a known-good config JSON above to enable scoring.)</span>"
            "</div>"
        )

    return validation_status, accuracy_report


# =============================================
# TAB 3: FULL PIPELINE
# =============================================
def estimate_confidence(raw_text, sanitized_text, repair_was_attempted):
    """
    Estimates how confident we should be in the generated config.
    """
    issues = []
    if len(raw_text.strip()) < 200:
        issues.append("weak_pdf_extraction")
    if sanitized_text.count("[REDACTED") > 10:
        issues.append("heavily_redacted_input")
    if repair_was_attempted:
        issues.append("required_schema_repair")

    if not issues:
        return "High"
    if len(issues) == 1:
        return f"Medium ({issues[0]})"
    return f"Low ({', '.join(issues)})"


def process_sow(file_path):
    """
    Full pipeline — extract, sanitize, generate, validate, score.
    """
    if file_path is None:
        return "No file uploaded", "", "", "", ""

    # Station 1: Extract text
    try:
        raw_text = extract_text(file_path)
    except (ValueError, Exception):
        try:
            with open(file_path, "r") as f:
                raw_text = f.read()
        except Exception as e:
            return f"Error reading file: {e}", "", "", "", ""

    # Sanitize PII
    sanitized_text = sanitize_text(raw_text)

    # Station 2: Build prompt
    user_prompt = build_user_prompt(sanitized_text)

    # Station 3: Call Gemini
    raw_response = call_gemini(SYSTEM_PROMPT, user_prompt)

    # Station 4: Validate
    is_valid, parsed_or_error = validate_config(raw_response, SCHEMA)

    # Try repair if validation failed
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
        raw_response = repaired_response

    pretty_json = json.dumps(parsed_or_error, indent=2)
    confidence = estimate_confidence(raw_text, sanitized_text, repair_attempted)

    # Station 5: Score accuracy
    customer_name = parsed_or_error.get("customer_name", "")
    if customer_name in EVAL_CONFIGS:
        score_result = score_config(parsed_or_error, EVAL_CONFIGS[customer_name])
        accuracy_report = format_report_html(score_result)
    else:
        accuracy_report = (
            "<div style='font-family: Google Sans, Helvetica Neue, Helvetica, Arial, sans-serif; "
            "color: #6b7280; font-size: 14px;'>"
            f"No eval config found for '{customer_name}' — scoring skipped.<br>"
            "<span style='font-size: 12px;'>(Normal for reference SOWs. Scoring works for eval SOWs.)</span>"
            "</div>"
        )

    validation_status = "PASSED — all required fields present, types correct"
    if repair_attempted:
        validation_status += " (after schema repair)"

    return sanitized_text, pretty_json, validation_status, confidence, accuracy_report


# =============================================
# BUILD THE GRADIO UI
# =============================================
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700&display=swap');

* {
    font-family: 'Google Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
}

textarea, input, .code-wrap, .cm-editor * {
    font-family: 'Google Sans', 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
}
"""

with gr.Blocks(title="Cloud Config Agent — Cadence Dev Day", theme=gr.themes.Soft(), css=CUSTOM_CSS) as app:

    gr.Markdown("# Cloud Config Right Sizing Agent")

    with gr.Tabs():

        # ---- TAB 1: SANITIZE ----
        with gr.TabItem("Sanitize SOW"):
            gr.Markdown(
                "Upload a SOW document to extract text and redact PII. "
                "Copy the sanitized output into Gemini Enterprise Agent Designer."
            )
            with gr.Row():
                with gr.Column():
                    sanitize_file = gr.File(label="Upload SOW (PDF or TXT)", file_types=[".pdf", ".txt"])
                    sanitize_btn = gr.Button("Extract & Sanitize", variant="primary")

                with gr.Column():
                    raw_output = gr.Textbox(label="Raw Extracted Text", lines=12, interactive=False)

                with gr.Column():
                    sanitized_output = gr.Textbox(
                        label="Sanitized Text (copy this into Agent Designer)",
                        lines=12,
                        interactive=False,
                    )

            sanitize_btn.click(
                fn=sanitize_sow,
                inputs=sanitize_file,
                outputs=[raw_output, sanitized_output],
            )

        # ---- TAB 2: VALIDATE & SCORE ----
        with gr.TabItem("Validate & Score"):
            gr.Markdown(
                "Paste the JSON config from Agent Designer to validate it against the CICD schema "
                "and score accuracy against a known-good config."
            )
            with gr.Row():
                with gr.Column():
                    json_input = gr.Textbox(
                        label="Paste JSON config from Agent Designer",
                        lines=16,
                        placeholder='{\n  "customer_name": "...",\n  "environment_tier": "...",\n  ...\n}',
                    )
                    eval_file_input = gr.File(
                        label="Optional: upload known-good config for scoring",
                        file_types=[".json"],
                    )
                    validate_btn = gr.Button("Validate & Score", variant="primary")

                with gr.Column():
                    val_status = gr.Textbox(label="Validation Status", lines=2, interactive=False)
                    val_accuracy = gr.HTML(label="Accuracy Report")

            validate_btn.click(
                fn=validate_with_eval,
                inputs=[json_input, eval_file_input],
                outputs=[val_status, val_accuracy],
            )

        # ---- TAB 3: FULL PIPELINE ----
        with gr.TabItem("Full Pipeline"):
            gr.Markdown(
                "End-to-end: upload a SOW → extract → sanitize → generate config via Gemini → "
                "validate → score. Runs everything automatically."
            )
            with gr.Row():
                with gr.Column():
                    full_file = gr.File(label="Upload SOW (PDF or TXT)", file_types=[".pdf", ".txt"])
                    full_btn = gr.Button("Generate Config", variant="primary")
                    full_sow = gr.Textbox(label="Sanitized SOW Text", lines=14, interactive=False)

                with gr.Column():
                    full_validation = gr.Textbox(label="Validation Status", lines=2, interactive=False)
                    full_confidence = gr.Textbox(label="Confidence / Review Flag", interactive=False)
                    full_accuracy = gr.HTML(label="Accuracy Report")

                with gr.Column():
                    full_config = gr.Code(label="Generated Config JSON", language="json", interactive=False)

            full_btn.click(
                fn=process_sow,
                inputs=full_file,
                outputs=[full_sow, full_config, full_validation, full_confidence, full_accuracy],
            )

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=False)
