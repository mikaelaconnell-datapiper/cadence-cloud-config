# Slide Deck Content — Cloud Config Right Sizing Agent
Use this to build your Google Slides presentation for the dev day morning kickoff.

---

## Slide 1: Title

**Cloud Config Right Sizing Agent**

Automating SOW-to-Config with AI

Cadence Dev Day | April 2, 2026

---

## Slide 2: The Problem

**Today's workflow is manual and error-prone**

- Engineers read multi-page SOW documents
- Manually translate requirements into cloud config files
- Each config is hand-built for the CICD pipeline
- Risk: missed fields, inconsistent sizing, slow turnaround
- No standardized way to validate configs before deployment

---

## Slide 3: The Solution

**An AI agent that reads the SOW and generates the config**

SOW PDF → Agent → Validated Config JSON

- Upload a customer SOW
- Agent extracts requirements, generates infrastructure config
- Output is validated against the CICD schema
- Accuracy scored against known-good configs
- All sensitive data redacted before reaching the model

---

## Slide 4: Architecture

**5-Station Pipeline**

```
Extract PDF → Sanitize PII → Build Prompt → Call Gemini → Validate → Score
```

| Station | Purpose |
|---|---|
| Extract | Pull text from SOW PDF |
| Sanitize | Redact emails, phones, addresses, pricing |
| Prompt | Few-shot prompt with reference examples |
| Generate | Gemini via Vertex AI (with mock fallback) |
| Validate | JSON schema validation (with auto-repair) |
| Score | Field-level accuracy vs known-good config |

---

## Slide 5: Data Privacy

**Customer PII never reaches the model**

Before:
```
Client: Nimbus Retail Solutions
Contact: sarah.chen@nimbusretail.com
Phone: (415) 555-0192
Contract Number: NRS-2026-0042
Storage: 750 GB of SSD persistent storage
```

After sanitization:
```
Client: Nimbus Retail Solutions        →  Client: [REDACTED]
Contact: sarah.chen@nimbusretail.com   →  Contact: [REDACTED_EMAIL]
Phone: (415) 555-0192                  →  Phone: [REDACTED_PHONE]
Contract Number: NRS-2026-0042         →  [REDACTED_ACCOUNT_ID]
Storage: 750 GB of SSD persistent...   →  (kept — sizing-relevant)
```

Only the sanitized version is sent to Gemini.

---

## Slide 6: Live Demo

**[Run the app live — upload a SOW, show the output]**

Talking points:
- Show the sanitized text (PII redacted, sizing info preserved)
- Show the generated JSON (all fields populated)
- Show validation status (PASSED)
- Show confidence score (High)
- Show accuracy report (field-by-field comparison with color coding)

---

## Slide 7: What We're Building Today

**Goals for this session:**

1. Fork the starter repo and get the app running locally
2. Run at least 3 end-to-end demo runs with sample SOWs
3. Explore the codebase — understand each station
4. Connect to Vertex AI (if GCP access is ready)
5. Stretch: add new SOW examples, modify the schema, improve the sanitizer

---

## Slide 8: Getting Started

**Setup (5 minutes):**

1. Fork: `github.com/mikaelaconnell-datapiper/cadence-cloud-config`
2. Clone, create venv, install requirements
3. Run `python app.py`
4. Open `http://localhost:7860`

**Handout at your table has full instructions and file map.**

Sample SOW PDFs are provided — start by uploading one and reviewing the output.

---

## Slide 9 (Optional): What's Next

**Beyond the MVP:**

- Deploy as a Cloud Run service
- Connect to GCS for SOW ingestion
- Add more reference examples to improve accuracy
- Integrate with the CICD pipeline for automated provisioning
- Add human-in-the-loop review for low-confidence configs
