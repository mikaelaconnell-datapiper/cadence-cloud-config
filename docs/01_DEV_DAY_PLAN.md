# Cloud Config Right Sizing Agent
## Dev Day Plan — April 2, 2026

---

### The Problem

Cadence engineers currently read customer Statement of Work (SOW) documents manually and translate the infrastructure requirements into cloud configuration files for the CICD deployment pipeline. This process is slow, inconsistent, and doesn't scale. Missed fields or incorrect sizing can lead to deployment issues downstream.

### The Solution

A low-code AI agent built in Gemini Enterprise Agent Designer that:

1. Accepts an approved SOW document
2. Extracts infrastructure requirements (compute, storage, networking, services)
3. Generates a chamber configuration JSON aligned to the CICD schema
4. Outputs validated, structured JSON ready for pipeline consumption

### Priorities for the Day

- **Privacy** — Customer data is handled according to approved guidelines
- **Output quality** — JSON must align to the target schema with accurate values
- **Clear demo** — At least 3 working end-to-end runs with a compelling narrative

---

## Target Deliverables

- Working Gemini Enterprise Agent Designer agent
- At least 3 end-to-end test runs with approved SOWs
- JSON output aligned to the target schema
- Basic validation and accuracy review against known-good outputs
- Clear explanation of privacy handling and production next steps

---

## Working Approach

| Path | Tool | Purpose |
|---|---|---|
| **Primary** | Gemini Enterprise Agent Designer | Build the agent, generate config JSON |
| **Supporting** | Python/Gradio tooling | Validation, scoring, optional privacy preprocessing |

Focus on one working path first, then refine quality and demo flow.

---

## Schedule

### 9:30 - 10:00 — Setup and Alignment

- Confirm inputs, success criteria, and owners
- Verify available artifacts: approved SOWs, known-good outputs, target JSON schema, critical fields for evaluation
- Confirm how SOWs will be provided in Gemini Enterprise
- Align on the MVP output format

### 10:00 - 10:45 — Build the Agent

- Build the first version of the agent in Agent Designer
- Load instructions, schema guidance, and reference examples
- Test the initial workflow on the first SOW
- Check whether output is returning usable JSON

### 10:45 - 11:15 — Refine the Agent

- Improve instructions and examples based on first test output
- Tighten JSON output expectations
- Identify any missing fields or repeated failure patterns

### 11:15 - 12:00 — Test with Additional SOWs

- Run additional SOWs through the agent
- Compare outputs to expected configs
- Capture where the agent performs well vs where it drifts
- Decide what to refine after lunch

### 12:00 - 1:00 — Lunch / Regroup

- Consolidate notes on prompt changes, privacy discussion points, output issues, and open blockers

### 1:00 - 2:00 — Validation and Scoring

- Review generated JSON against schema
- Compare outputs to known-good configs on critical fields
- Record field-level accuracy observations

### 2:00 - 2:45 — Final Refinement

- Improve agent instructions and examples one last time
- Select 3 demo-ready SOWs
- Prepare a backup example in case one run is weak

### 2:45 - 3:00 — Demo Prep

- Lock the final workflow
- Assign speakers and flow for showcase
- Prepare the privacy and roadmap explanation

---

## Team Roles

| Role | Responsibility |
|---|---|
| Agent workflow owner | Builds and updates the Agent Designer agent |
| Data / examples owner | Manages SOWs, known-good outputs, schema, and reference examples |
| Validation / scoring owner | Checks generated JSON against schema and expected outputs |
| Privacy / narrative owner | Documents how data is handled and how to explain limitations |
| Demo owner | Prepares the final 3 runs and showcase flow |

If the team is small, combine roles. If the team is larger, assign 1-2 people per workstream.

---

## Risks and Fallbacks

| Risk | Fallback |
|---|---|
| Agent output is inconsistent | Refine instructions and add better examples |
| Schema alignment is weak | Tighten expected output structure and validate manually |
| Privacy concerns block direct document input | Narrow the demo to approved sample content and explain preprocessing as a future step |
| One SOW performs poorly | Use backup examples for the final showcase |

---

## Core Messages

- Privacy and accuracy are the priorities
- Low-code first, but output still needs review and validation
- One working path first, polish second
- The goal is a convincing MVP, not a production platform in one day

---

## Showcase Story

1. **Problem:** Manual SOW parsing is slow and error-prone
2. **Solution:** Low-code Gemini Enterprise agent generates chamber config JSON
3. **Controls:** Privacy-aware handling, structured output, validation against expected schema
4. **Outcome:** Faster path from approved SOW to deployment-ready config
5. **Next step:** Productionization with preprocessing, validation, and pipeline integration
