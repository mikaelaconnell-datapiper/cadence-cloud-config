"""
The Gradio App — The Demo UI
==============================
This is what you run on dev day. It creates a web page with:
- An upload button for the SOW file
- A button to generate the config
- The generated JSON output
- Validation status (pass/fail)
- Accuracy report (if we have the correct answer to compare against)

TO RUN:
  source venv/bin/activate
  python app.py
Then open http://localhost:7860 in your browser
"""

import json
import os
import gradio as gr
from extract_pdf import extract_text
from build_prompt import load_reference_examples, load_schema, build_system_prompt, build_user_prompt
from call_gemini import call_gemini
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

print("\nApp ready!\n")


def process_sow(file_path):
    """
    Main function — takes the uploaded file through all 5 stations.
    Gradio passes the file path as a string.
    """
    if file_path is None:
        return "No file uploaded", "", "", ""

    # Station 1: Extract text
    try:
        sow_text = extract_text(file_path)
    except (ValueError, Exception):
        try:
            with open(file_path, "r") as f:
                sow_text = f.read()
        except Exception as e:
            return f"Error reading file: {e}", "", "", ""

    # Station 2: Build the prompt
    user_prompt = build_user_prompt(sow_text)

    # Station 3: Call Gemini (mock for now)
    raw_response = call_gemini(SYSTEM_PROMPT, user_prompt)

    # Station 4: Validate
    is_valid, parsed_or_error = validate_config(raw_response, SCHEMA)

    if not is_valid:
        return (
            sow_text,
            raw_response,
            f"VALIDATION FAILED: {parsed_or_error}",
            "Cannot score — validation failed",
        )

    pretty_json = json.dumps(parsed_or_error, indent=2)

    # Station 5: Score accuracy
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

    return sow_text, pretty_json, validation_status, accuracy_report


# --- Build the Gradio UI ---
with gr.Blocks(title="Cloud Config Agent — Cadence Dev Day") as app:

    gr.Markdown("# Cloud Config Right Sizing Agent")
    gr.Markdown("Upload a SOW document to generate a chamber configuration for the CICD pipeline.")

    with gr.Row():
        with gr.Column():
            file_input = gr.File(label="Upload SOW (PDF or TXT)", file_types=[".pdf", ".txt"])
            run_button = gr.Button("Generate Config", variant="primary")

        with gr.Column():
            validation_output = gr.Textbox(label="Validation Status", lines=2)
            accuracy_output = gr.Textbox(label="Accuracy Report", lines=12)

    with gr.Row():
        sow_output = gr.Textbox(label="Extracted SOW Text", lines=15)
        config_output = gr.Textbox(label="Generated Config JSON", lines=15)

    run_button.click(
        fn=process_sow,
        inputs=file_input,
        outputs=[sow_output, config_output, validation_output, accuracy_output],
    )

if __name__ == "__main__":
    app.launch(server_name="127.0.0.1", server_port=7860, share=True)
