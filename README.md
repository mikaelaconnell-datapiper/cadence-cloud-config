# Cloud Config Right Sizing Agent

Parses Cadence Managed Cloud SOW documents and generates chamber configuration JSON for the CICD deployment pipeline.

## How It Works

**Primary path:** Gemini Enterprise Agent Designer generates the chamber config from an uploaded SOW.

**Supporting tools:** A Gradio web app handles preprocessing (PII redaction) and post-processing (schema validation + accuracy scoring).

### Pipeline

1. **Extract** — Pull text from a SOW PDF
2. **Sanitize** — Redact customer PII (names, emails, addresses, signatures, terms, payment info) while preserving chamber requirements
3. **Generate** — Agent Designer produces the chamber config JSON
4. **Validate** — Check the JSON against the target schema
5. **Score** — Compare output to a known-good config field by field

## Project Structure

```
├── app.py                  # Gradio web UI (3 tabs: Sanitize, Validate & Score, Full Pipeline)
├── extract_pdf.py          # PDF text extraction (PyMuPDF + pypdf fallback)
├── sanitizer.py            # PII redaction based on Cadence's SOW structure
├── build_prompt.py         # Few-shot prompt construction
├── call_gemini.py          # Gemini API integration (optional full pipeline)
├── validate_output.py      # JSON schema validation
├── score_accuracy.py       # Field-level accuracy scoring
├── config_schema.json      # Target chamber config schema
├── Cloud_Config_Agent.ipynb # Colab notebook — step-by-step walkthrough
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── data/
    ├── reference_sows/     # Example SOW text files
    ├── reference_configs/  # Matching known-good config JSONs
    └── eval_configs/       # Ground truth configs for accuracy scoring
```

## Setup

```bash
git clone https://github.com/mikaelaconnell-datapiper/cadence-cloud-config.git
cd cadence-cloud-config
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:7860** in a browser.

## Colab Notebook

The notebook walks through each step independently and can launch the full Gradio app with a shareable link:

**Open in Colab →** `Cloud_Config_Agent.ipynb`

## Chamber Config Schema

The agent extracts these fields from SOW documents:

| Category | Fields |
|---|---|
| Platform | `platform_provider`, `chamber_location` |
| Users | `total_users`, `user_accounts` (count + location) |
| Hardware | `interactive_servers` (instance type, vCPUs, RAM), `storage` (backup GB, scratch GB) |
| Software | `software_licenses` (product name + quantity) |
| Services | `pdks_to_install` (name + source) |

## What Gets Redacted

| Removed | Preserved |
|---|---|
| SOW headings, order numbers | Platform provider, region |
| Customer/billing addresses | Hardware specs |
| Contact info, emails, signatures | Storage requirements |
| Terms and conditions | Software license names and quantities |
| Payment schedules, pricing | User counts and locations |
| Footer text, document IDs | PDK requirements |
