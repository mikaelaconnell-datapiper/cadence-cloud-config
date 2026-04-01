# Cloud Config Right Sizing Agent
## Technical Reference & Guide

This document explains how each piece of the solution works and how to use the tools after dev day.

---

## Part 1: Sanitize — PII Redaction

### Purpose

Customer SOWs contain sensitive information — names, emails, phone numbers, account IDs, pricing. If the requirement is to redact this information before any content reaches the AI model, the sanitization pipeline handles that.

### How It Works

**Step 1: Extract text from the PDF** (`extract_pdf.py`)

PDFs aren't plain text — the content is encoded in a binary format. This module opens the PDF and pulls out all readable text, page by page.

- Uses **PyMuPDF** as the primary extractor (handles tables and complex layouts well)
- Falls back to **pypdf** if PyMuPDF returns nothing (pure Python, always available)
- Cleans up whitespace artifacts from the extraction process

Input: A PDF file path
Output: A clean text string of the full document

**Step 2: Redact PII** (`sanitizer.py`)

Once the text is extracted, the sanitizer scans it using pattern matching (regex) and replaces sensitive data with `[REDACTED]` tags.

| What gets redacted | Example | Replacement |
|---|---|---|
| Email addresses | `john@acme.com` | `[REDACTED_EMAIL]` |
| Phone numbers | `(555) 123-4567` | `[REDACTED_PHONE]` |
| Street addresses | `123 Main Street` | `[REDACTED_ADDRESS]` |
| Account/contract IDs | `Account ID: ACME-001` | `[REDACTED_ACCOUNT_ID]` |
| Client/customer names | `Client Name: Acme Corp` | `Client Name: [REDACTED]` |
| Pricing/budget lines | `Budget: $45,000/month` | `[REDACTED_PRICING_LINE]` |

What stays intact: service counts, storage sizes, compute specs, environment references, availability requirements — everything the AI needs to generate the config.

Input: Raw text from the PDF
Output: Sanitized text safe for model input

### When to Use

- Before pasting SOW content into Agent Designer (if PII redaction is required)
- As a preprocessing step in the full pipeline
- To demonstrate the privacy approach during the showcase

---

## Part 2: Validate & Score — Output Quality

### Purpose

After the agent generates a config JSON (from Agent Designer or the Gemini API), the output needs to be checked for correctness before it could ever reach a CICD pipeline.

### How It Works

**Step 1: Schema validation** (`validate_output.py`)

Checks the generated JSON against the target schema (`config_schema.json`):

- Is it valid JSON? (Can it be parsed without syntax errors?)
- Are all required fields present? (`customer_name`, `environment_tier`, `compute`, `storage`, `networking`, `services`)
- Are data types correct? (Numbers are numbers, booleans are booleans, strings are strings)
- Are enum values valid? (`environment_tier` must be one of: `small`, `medium`, `large`, `enterprise`)

Input: A JSON string + the schema
Output: Pass/fail + error message if failed

**Step 2: Accuracy scoring** (`score_accuracy.py`)

Compares the generated config to a known-good config (the "correct answer") field by field.

For each critical field, the scorer checks: does the generated value match the expected value?

Critical fields checked:

| Category | Fields |
|---|---|
| Top-level | `environment_tier`, `high_availability`, `backup_enabled`, `estimated_users` |
| Compute | `instance_type`, `instance_count`, `vcpus_per_instance`, `memory_gb_per_instance` |
| Storage | `storage_type`, `total_storage_gb`, `iops_required` |
| Networking | `vpc_cidr`, `subnet_count`, `load_balancer` |
| Services | List of service names (sorted comparison) |

The output is a percentage score (e.g., "80% — 12/15 fields matched") and a field-by-field breakdown showing which fields matched and which didn't.

Input: Generated config + known-good config
Output: Accuracy percentage + detailed field-level report

### When to Use

- After every agent run to check output quality
- To compare different prompt versions (did the new prompt improve accuracy?)
- To identify which fields the agent consistently gets wrong

---

## Part 3: Full Pipeline — End-to-End with Gemini API

### Purpose

This is an optional backup path that runs everything automatically: extract PDF, sanitize, call Gemini directly via API, validate, and score — all in one step. It bypasses Agent Designer entirely.

### How It Works

**Prompt construction** (`build_prompt.py`)

Builds a prompt for Gemini using the few-shot approach:

1. **System prompt** — Defines the AI's role (cloud config expert), the task (parse SOW → generate config), the output format (the JSON schema), and rules to follow
2. **Reference examples** — 2-3 SOW/config pairs loaded from the `data/` directory that show the AI what correct output looks like
3. **User prompt** — The new SOW text to process

**Gemini API call** (`call_gemini.py`)

Sends the prompt to Gemini and gets the config JSON back. Three options in priority order:

1. **Gemini Developer API** — Free API key from aistudio.google.com. No GCP project needed. Uses `gemini-2.5-flash`.
2. **Vertex AI** — Requires a GCP project with `aiplatform.googleapis.com` enabled and IAM roles configured. Uses `gemini-3.1-pro`.
3. **Mock fallback** — A heuristic generator that reads keywords from the SOW and returns a reasonable config. Always works, no external calls. Used for testing when no API access is available.

The call includes `response_mime_type: "application/json"` which forces Gemini to return only JSON — no markdown, no explanations.

If the initial output fails schema validation, a **repair step** sends the validation error back to Gemini and asks it to fix just the broken parts.

### When to Use

- As a backup if Agent Designer is unavailable
- To demonstrate the programmatic approach during the showcase
- For testing and development outside of Agent Designer

---

## The Gradio App (`app.py`)

A web-based UI with three tabs that correspond to the three parts above:

| Tab | What it does | Inputs | Outputs |
|---|---|---|---|
| **Sanitize SOW** | Extract + redact PII | Upload a PDF | Raw text + sanitized text |
| **Validate & Score** | Check schema + compare accuracy | Paste JSON + optional known-good config | Validation status + accuracy report |
| **Full Pipeline** | Everything end-to-end | Upload a PDF | Sanitized text + config JSON + validation + confidence + accuracy |

To run locally:
```bash
python app.py
# Open http://localhost:7860
```

When launched with `share=True`, Gradio generates a public URL (like `https://abc123.gradio.live`) that anyone on the team can access from their browser.

---

## Target JSON Schema

The current schema defines the following fields. This may be updated on dev day based on the actual CICD pipeline requirements.

```json
{
  "customer_name": "string (required)",
  "environment_tier": "small | medium | large | enterprise (required)",
  "compute": {
    "instance_type": "string, e.g. n2-standard-4 (required)",
    "instance_count": "integer (required)",
    "vcpus_per_instance": "integer (required)",
    "memory_gb_per_instance": "integer (required)"
  },
  "storage": {
    "storage_type": "pd-standard | pd-ssd | pd-balanced (required)",
    "total_storage_gb": "integer (required)",
    "iops_required": "integer (required)"
  },
  "networking": {
    "vpc_cidr": "string, e.g. 10.0.0.0/16 (required)",
    "subnet_count": "integer (required)",
    "load_balancer": "boolean (required)"
  },
  "services": [
    {
      "service_name": "string (required)",
      "enabled": "boolean (required)",
      "configuration": "object (optional)"
    }
  ],
  "high_availability": "boolean (optional)",
  "backup_enabled": "boolean (optional)",
  "estimated_users": "integer (optional)"
}
```

---

## Using Agent Designer After Dev Day

### Creating a New Agent

1. Open Gemini Enterprise → Agents → + New agent
2. Describe the agent's purpose in the chat box
3. Include the target JSON schema in the instructions
4. Upload reference SOW/config examples
5. Test with an approved SOW document

### Prompt Engineering Tips

- **Be specific** — Tell the agent exactly what fields to include, what format to use, and what rules to follow
- **Include the schema** — Paste the full JSON schema into the instructions so the agent knows the exact expected structure
- **Add examples** — Upload 2-3 SOW/config pairs as reference. More examples = better accuracy
- **Say what NOT to do** — "Do not include markdown code fences. Do not add explanations. Do not hallucinate services not mentioned in the SOW."
- **Set rules for ambiguity** — "If high availability is not mentioned, default to false. Set environment_tier based on user count."

### Improving Accuracy

The iteration loop:

1. Run a SOW through the agent
2. Compare the output to what was expected
3. Identify the gap (missing field? wrong value? extra text?)
4. Update the instructions to address that specific gap
5. Re-test the same SOW to verify the fix
6. Test a different SOW to make sure the fix didn't break something else

### Recommended Settings

| Setting | Value |
|---|---|
| Model | Gemini 3.1 Pro (or latest available) |
| Temperature | Low (0.1 - 0.3) for consistent output |
| Output format | Specify JSON-only in instructions |

---

## What to Update When the Schema Changes

| What changed | Where to update |
|---|---|
| Target schema (fields, types, required) | `config_schema.json` and the SCHEMA dict in the Colab notebook |
| Critical fields for scoring | `score_accuracy.py` → `critical_fields` list |
| Reference examples | `data/reference_sows/` + `data/reference_configs/` |
| Known-good configs for scoring | `data/eval_configs/` |
| Agent Designer instructions | The Instructions field in Agent Designer |

---

## Resources

| Resource | Location |
|---|---|
| Source code | github.com/mikaelaconnell-datapiper/cadence-cloud-config |
| Colab notebook | `Cloud_Config_Agent.ipynb` in the repo (click "Open in Colab" on GitHub) |
| Agent Designer docs | cloud.google.com/gemini/enterprise/docs/agent-designer |
| Gemini API keys | aistudio.google.com/apikey |
