# Cadence Dev Day — Study Guide
## Cloud Config Right Sizing Pricing Agent

Use this to review before dev day. Covers every component, what it does, and where to go when the client asks questions.

---

## What Does This Agent Do?

Cadence's cloud team currently reads customer contracts (SOW PDFs) by hand and manually types up a config file that tells their system what infrastructure to deploy. This agent automates that:

**PDF in → AI reads it → JSON config out**

---

## Project File Map

```
cadence/
├── data/
│   ├── reference_sows/        ← SOW files the AI learns from (the "study materials")
│   ├── reference_configs/     ← The correct configs for each reference SOW (the "answer key")
│   ├── eval_sows/             ← SOW files we test the AI on (the "exam")
│   └── eval_configs/          ← The correct configs for eval SOWs (to check the AI's answers)
├── extract_pdf.py             ← Station 1: Reads a PDF/text file and returns plain text
├── build_prompt.py            ← Station 2: Builds the message we send to the AI
├── call_gemini.py             ← Station 3: Sends the prompt to Gemini and gets a response
├── validate_output.py         ← Station 4: Checks if the AI's JSON output is valid
├── score_accuracy.py          ← Station 5: Compares the AI's output to the correct answer
├── app.py                     ← The Flask web UI (upload button, results display)
├── config_schema.json         ← The rules for what the output JSON must look like
├── generate_schema.py         ← Tool to auto-generate a schema from example configs
├── requirements.txt           ← List of Python packages to install
└── STUDY_GUIDE.md             ← This file
```

---

## How the Agent Works (Step by Step)

### Station 1: extract_pdf.py — "Read the Document"
- **What it does:** Opens a PDF and pulls out all the text as a string
- **Why we need it:** The AI can't read PDFs directly, it needs plain text
- **Library used:** PyMuPDF (imported as `fitz`)
- **Key function:** `extract_text(file_path)` — give it a file path, get back text
- **If client asks "what about complex tables in PDFs?"** → PyMuPDF handles tables, but for very complex layouts we could add a table-specific extraction step

**How the code works (line by line):**
```
1. import fitz                         — loads the PDF-reading library
2. doc = fitz.open(pdf_path)           — opens the PDF file
3. all_text = []                       — creates an empty list (like an empty bag)
4. for page_number in range(len(doc)): — loop through every page
5.     page = doc[page_number]         — grab one page
6.     page_text = page.get_text()     — pull out that page's text
7.     all_text.append(page_text)      — add it to the bag
8. full_text = "\n".join(all_text)     — combine all pages into one string
9. return full_text                    — send it back to whoever called this function
```

**The router pattern (extract_text function):**
This function checks the file extension and picks the right method:
- `.pdf` → use PyMuPDF to extract text
- `.txt` → just read it as plain text
- anything else → throw an error
This is a common pattern — one "smart" function that routes to the right helper.

**Testing trick:** The `if __name__ == "__main__":` block at the bottom only runs when you execute the file directly (`python3 extract_pdf.py`). When `app.py` imports it, that block gets skipped. This is how you add quick tests to any Python file.

### Station 2: build_prompt.py — "Build the Instructions"
- **What it does:** Assembles the message (prompt) we send to the AI
- **Two parts of the prompt:**
  - SYSTEM PROMPT = the instructions + reference examples (stays the same every time)
  - USER PROMPT = the new SOW to process (changes each time)
- **This is few-shot prompting:** We show the AI 3-5 examples of SOW→config, then ask it to do a new one
- **Key function:** `build_system_prompt(examples, schema)` — creates the instructions
- **Key function:** `build_user_prompt(new_sow_text)` — wraps the new SOW
- **If client asks "why few-shot?"** → It's more accurate than zero-shot because the AI can see the exact pattern and output format we want

**How the prompt is structured:**
```
SYSTEM PROMPT (the instructions — stays the same):
├── "You are a cloud infrastructure configuration expert..."  ← tells the AI who it is
├── The JSON schema                                           ← tells the AI what format to use
├── Rules (output only JSON, use all required fields, etc.)   ← guardrails
├── EXAMPLE 1: Acme SOW text → Acme config JSON              ← reference pair
├── EXAMPLE 2: BrightStar SOW text → BrightStar config JSON  ← reference pair
└── EXAMPLE 3: GreenLeaf SOW text → GreenLeaf config JSON    ← reference pair

USER PROMPT (the new request — changes each time):
└── "Analyze this SOW and generate the config: [new SOW text]"
```

**How load_reference_examples works:**
1. Looks in the `data/reference_sows/` folder, finds all files starting with `sow_`
2. For each one, figures out the matching config file name (e.g., `sow_acme_corp.txt` → `config_acme_corp.json`)
3. Reads both files and pairs them together
4. Returns a list of (SOW text, config JSON) pairs

**The name-matching trick:**
`sow_acme_corp.txt` → strip `sow_` → strip `.txt` → get `acme_corp` → add `config_` + `.json` → `config_acme_corp.json`
This is why the file naming matters — SOW and config files must follow this pattern to match up.

### Station 3: call_gemini.py — "Ask the AI"
- **What it does:** Sends the prompt to Gemini and gets back a JSON response
- **Right now:** Uses a mock (fake) function that guesses based on keywords
- **On dev day:** Swap to the real Gemini API call (the code is already there, just commented out)
- **Key concept:** We send two things — the system prompt (instructions + examples) and the user prompt (new SOW)

**How the mock works:**
The mock is intentionally dumb — it just searches for keywords:
- Finds "Client: Acme Corporation" in the text → sets customer_name
- Finds "500" in the text → guesses medium tier, 500 users
- Finds "ssd" in the text → sets storage type to pd-ssd
- Finds "high availability" → sets HA to true
This is why the mock only gets 80% accuracy — it's guessing, not understanding.

**How real Gemini will work:**
Real Gemini actually reads and understands the SOW. It will:
- See "IOPS requirement is 5000" and output 5000 (not guess 3000)
- See "VPC CIDR: 10.5.0.0/16" and output exactly that (not default to 10.0.0.0/16)
- See all 5 services listed and include all of them (not just 2)

**The swap pattern:**
The `call_gemini()` function at the bottom of the file currently calls `call_gemini_mock()`. To switch to real Gemini, you just change one line to call `call_gemini_real()` instead.

### Station 4: validate_output.py — "Check the Answer"
- **What it does:** Takes the JSON the AI generated and checks it against the schema rules
- **What it catches:** Missing required fields, wrong data types (string where number should be), invalid values
- **Library used:** jsonschema
- **Why this matters:** A bad config going into the CICD pipeline could deploy the wrong infrastructure. Validation is the safety net.
- **If client asks "what happens if validation fails?"** → The agent rejects the output and can retry with a clarified prompt, or flag it for human review

**Two checks happen in order:**
1. `json.loads()` — Can we even parse this as JSON? (catches if the AI returned plain text or broken syntax)
2. `jsonschema.validate()` — Does the JSON match our schema? (catches missing fields, wrong types)

**What the function returns:**
- If valid: `(True, {the config as a dictionary})`
- If invalid: `(False, "description of what went wrong")`
This tuple pattern (returning two values) lets the caller easily check success/failure.

### Station 5: score_accuracy.py — "Grade the Answer"
- **What it does:** Compares the AI's generated config to the known-good config field by field
- **How scoring works:** For each field, does the AI's value match the correct value? Count matches / total fields = accuracy %
- **Critical fields:** instance_type, instance_count, total_storage_gb, storage_type, environment_tier, services
- **The 80% target:** The use case requires at least 80% field-level accuracy
- **If client asks "how do you measure accuracy?"** → "We compare each field in the generated config against the known-good config and calculate a match rate"

**How scoring works in detail:**
The function has a list of 14 critical fields. For each one:
1. Get the value from the AI's config
2. Get the value from the known-good config
3. Are they equal? → YES or NO
4. Count up all the YESes, divide by total fields → accuracy %

**Nested fields:** Some fields are inside other fields (e.g., `instance_type` is inside `compute`). The `parent_key` variable handles this — if parent_key is "compute", it looks inside `config["compute"]["instance_type"]` instead of just `config["instance_type"]`.

**Services scoring:** Services are compared by name only — does the generated config list the same service names as the correct config? The order doesn't matter (both lists get sorted first).

### The UI: app.py — "The Demo Interface"
- **What it does:** A web page where you upload a SOW and see the config output
- **Library used:** Flask — a lightweight web framework that handles HTTP requests
- **Demo flow:** Upload PDF → click button → see generated config + validation status + accuracy score

**How Flask works (the basics):**
- `@app.route("/")` means "when someone visits the homepage, run this function"
- `methods=["GET", "POST"]` means it handles both loading the page (GET) and submitting the form (POST)
- GET = user just opened the page → show the empty upload form
- POST = user clicked "Generate Config" → process the file and show results
- `render_template_string(HTML_TEMPLATE, results=results)` fills in the HTML with the results

**How the file upload works:**
1. User clicks "Choose File" and picks a SOW
2. User clicks "Generate Config"
3. Browser sends the file to Flask (POST request)
4. Flask saves it to a temp location (`/tmp/filename`)
5. Our code processes it through all 5 stations
6. Flask puts the results into the HTML template and sends the page back
7. User sees the results

---

## Key Concepts to Know

### JSON Schema
A rulebook that defines what a JSON file must look like. Think of it as a blank form template — it says which fields are required, what type each field is, and what values are allowed.

### Few-Shot Prompting
Giving the AI examples before asking it to do something. Like training a new employee by showing them completed work before asking them to do their own. More examples = more accurate, but also slower.

### Vertex AI
Google Cloud's AI platform. It's where Gemini (the AI model) lives. You send it a prompt through their API, it sends back a response.

### Flask
A lightweight Python web framework. You define "routes" (URLs) and what happens when someone visits them. It's reliable and works on any Python version. We use it for the demo UI.

### CICD Pipeline
The automated system that takes a config file and deploys actual cloud infrastructure. We don't build this — Cadence already has it. Our agent just produces the JSON that feeds into it.

---

## Common Client Questions & Answers

**"How does it handle SOWs with missing information?"**
→ The AI makes reasonable inferences based on the patterns it learned from the reference examples. If a SOW doesn't mention storage type but the workload is database-heavy, it would infer SSD based on similar examples.

**"Can we add more fields to the config?"**
→ Yes. Add the field to config_schema.json, update the reference configs to include it, and the AI will pick it up from the examples.

**"What if the SOW format changes?"**
→ The agent reads natural language, not a rigid format. It extracts requirements regardless of how the SOW is structured. Different headers, different ordering — it handles that.

**"How do we handle sensitive data?"**
→ SOW content is processed in-memory only, nothing persisted. For production, a preprocessing step strips PII before it reaches the model.

**"How long does it take to generate a config?"**
→ Usually 5-15 seconds depending on the SOW length and model response time.

**"What happens if the AI gets something wrong?"**
→ JSON schema validation catches structural errors automatically. For value errors (e.g., wrong instance type), the accuracy scoring flags mismatches for human review.

**"Can this work with other document types besides PDFs?"**
→ Yes. The extraction layer is modular — we could add support for Word docs, spreadsheets, or any text-based format.

---

## Dev Day Setup Commands

```bash
# If using your laptop
cd ~/Desktop/cadence
pip install -r requirements.txt
python3 app.py

# If using Cloud Shell or a new machine
git clone https://github.com/YOUR_REPO/cadence.git
cd cadence
pip install -r requirements.txt
python3 app.py
```

---

## Day-Before Checklist

- [ ] Run the full app end-to-end at least 3 times
- [ ] Practice explaining each component out loud (pretend someone asked "how does this work?")
- [ ] Make sure the GitHub repo is up to date
- [ ] Test that `pip install -r requirements.txt` works cleanly
- [ ] Charge your laptop
- [ ] Have this study guide open on your phone as a backup
