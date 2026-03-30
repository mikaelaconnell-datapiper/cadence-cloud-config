# Cloud Config Right Sizing Agent

A low-code agent that parses customer SOW (Statement of Work) PDFs and generates chamber configuration JSON for CICD deployment pipelines.

## How It Works

The agent runs through 5 stations:

1. **Extract** — Pull text from SOW PDFs (PyMuPDF primary, pypdf fallback)
2. **Sanitize** — Redact PII (emails, phone numbers, addresses, pricing) before sending to the model
3. **Generate** — Send sanitized text + few-shot examples to Gemini via Vertex AI to produce a config JSON
4. **Validate** — Check the generated JSON against the CICD schema using jsonschema
5. **Score** — Compare output against a known-good config and report field-level accuracy

Additional features:
- **Schema repair** — If the initial output fails validation, the agent sends the error back to Gemini for a self-correction attempt
- **Confidence scoring** — Flags configs as High / Medium / Low confidence based on extraction quality, redaction density, and whether repair was needed
- **Fallback mock generator** — If Vertex AI is unavailable, a heuristic mock keeps the pipeline functional for testing

## Project Structure

```
├── app.py                  # Gradio web UI — the main entry point
├── extract_pdf.py          # Station 1: PDF/TXT text extraction
├── sanitizer.py            # PII redaction before model input
├── build_prompt.py         # Station 2: Few-shot prompt construction
├── call_gemini.py          # Station 3: Vertex AI / Gemini integration + fallback
├── validate_output.py      # Station 4: JSON schema validation
├── score_accuracy.py       # Station 5: Field-level accuracy scoring
├── config_schema.json      # Target JSON schema for chamber configs
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
└── data/
    ├── reference_sows/     # Training examples (SOW text files)
    ├── reference_configs/  # Matching known-good config JSONs
    ├── eval_sows/          # Evaluation SOWs for accuracy testing
    └── eval_configs/       # Ground truth configs for scoring
```

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <your-fork-url>
cd cadence-cloud-config
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your GCP project details:

```
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

### 4. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project your-project-id
```

If you don't have GCP access yet, the app will automatically use the fallback mock generator — no configuration needed.

### 5. Run the app

```bash
python app.py
```

Open http://localhost:7860 in your browser.

## Usage

1. Upload a SOW document (PDF or TXT)
2. Click **Generate Config**
3. Review the outputs:
   - **Sanitized SOW Text** — Confirms PII was redacted before model input
   - **Generated Config JSON** — The chamber configuration
   - **Validation Status** — Whether the JSON conforms to the schema
   - **Confidence** — High / Medium / Low with reasons
   - **Accuracy Report** — Field-level comparison against known-good config (if an eval config exists for that customer)

## GCP Requirements

| Requirement | Details |
|---|---|
| **APIs to enable** | `aiplatform.googleapis.com`, `storage.googleapis.com` |
| **IAM roles** | Vertex AI User (`roles/aiplatform.user`), Storage Object Viewer (`roles/storage.objectViewer`) |
| **Authentication** | `gcloud auth application-default login` or a service account with the above roles |

## Dependencies

- Python 3.10+
- `gradio` — Web UI
- `PyMuPDF` / `pypdf` — PDF text extraction
- `jsonschema` — Schema validation
- `google-cloud-aiplatform` — Vertex AI SDK
- `python-dotenv` — Environment variable loading
