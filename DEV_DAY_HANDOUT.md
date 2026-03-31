# Cloud Config Right Sizing Agent — Dev Day Guide

## What Are We Building?

Cadence engineers manually read customer SOW (Statement of Work) documents and translate infrastructure requirements into cloud configuration files for the CICD pipeline. This process is slow, error-prone, and doesn't scale.

We're building an **AI agent** that automates this:

**SOW PDF in → Cloud Config JSON out**

The agent reads the SOW, extracts infrastructure requirements, and generates a validated configuration JSON — with PII automatically redacted before anything reaches the model.

---

## Architecture: 5 Stations

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Station 1  │     │  Sanitizer  │     │  Station 2  │     │  Station 3  │     │  Station 4  │
│  Extract    │────▶│  Redact PII │────▶│  Build      │────▶│  Call       │────▶│  Validate   │
│  PDF Text   │     │             │     │  Prompt     │     │  Gemini     │     │  JSON       │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                                       │
                                                                                       ▼
                                                                                ┌─────────────┐
                                                                                │  Station 5  │
                                                                                │  Score      │
                                                                                │  Accuracy   │
                                                                                └─────────────┘
```

| Station | File | What It Does |
|---|---|---|
| 1. Extract | `extract_pdf.py` | Pulls text from the SOW PDF |
| Sanitize | `sanitizer.py` | Redacts emails, phones, addresses, pricing before model input |
| 2. Prompt | `build_prompt.py` | Builds few-shot prompt with reference examples + schema |
| 3. Generate | `call_gemini.py` | Sends prompt to Gemini via Vertex AI (or falls back to mock) |
| 4. Validate | `validate_output.py` | Checks output against the CICD JSON schema |
| 5. Score | `score_accuracy.py` | Compares output to known-good config, field by field |

---

## Setup Instructions

### 1. Fork and clone the repo

```
https://github.com/mikaelaconnell-datapiper/cadence-cloud-config
```

Fork it to your GitHub, then:

```bash
git clone <your-fork-url>
cd cadence-cloud-config
```

### 2. Create virtual environment and install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure GCP access (if available)

```bash
cp .env.example .env
# Edit .env with the project ID and region
gcloud auth application-default login
```

If GCP access isn't ready yet, the app runs with a mock generator — no configuration needed.

### 4. Run the app

```bash
python app.py
```

Open **http://localhost:7860** in your browser.

---

## Try It Out

1. Upload a sample SOW PDF (provided at the table)
2. Click **Generate Config**
3. Review the output:
   - **Sanitized SOW Text** — Confirm PII was redacted
   - **Generated Config JSON** — The infrastructure configuration
   - **Validation Status** — Did it pass schema validation?
   - **Confidence** — High / Medium / Low
   - **Accuracy Report** — Field-by-field comparison (if eval config exists)

---

## Key Files to Explore

| If you want to... | Look at... |
|---|---|
| Change what PII gets redacted | `sanitizer.py` |
| Modify the prompt or add examples | `build_prompt.py` + `data/reference_sows/` |
| Change the output schema | `config_schema.json` |
| Adjust accuracy scoring fields | `score_accuracy.py` |
| Switch between mock and real Gemini | `call_gemini.py` |
| Modify the UI layout | `app.py` |

---

## Stretch Goals

If you finish early, try:

- Add a new reference SOW/config pair to `data/reference_sows/` and `data/reference_configs/`
- Add a new field to `config_schema.json` and update the few-shot examples
- Modify `sanitizer.py` to catch additional PII patterns
- Add a diff view comparing generated vs expected config
- Connect to GCS to load SOW files from a bucket instead of uploading manually

---

## GCP Requirements

| Requirement | Details |
|---|---|
| APIs to enable | `aiplatform.googleapis.com`, `storage.googleapis.com` |
| IAM roles | Vertex AI User (`roles/aiplatform.user`), Storage Object Viewer (`roles/storage.objectViewer`) |
| Auth | `gcloud auth application-default login` or service account |
