# Cloud Config Dev Day Plan

## Objective

Build and demo a low-code Cloud Config agent that takes an approved SOW document and returns chamber configuration JSON aligned to the CICD schema. Priorities for the day are **privacy**, **output quality**, and a **clear demo narrative**.

---

## Target Deliverables

- Working Gemini Enterprise Agent Designer agent
- At least 3 end-to-end test runs with approved SOWs
- JSON output aligned to the target schema
- Basic validation and accuracy review against known-good outputs
- Clear explanation of privacy handling and production next steps

---

## Working Approach

- **Primary build path:** Gemini Enterprise Agent Designer
- **Supporting path:** Lightweight Python/Gradio tooling for validation, scoring, and optional privacy/preprocessing discussion if needed
- Focus on one working path first, then refine quality and demo flow

---

## Schedule

### 9:30 - 10:00 — Setup and Alignment

- Confirm inputs, success criteria, and owners
- Verify what artifacts are available:
  - Approved SOWs
  - Known-good outputs
  - Target JSON schema
  - Critical fields for evaluation
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

- Consolidate notes on:
  - Prompt changes
  - Privacy discussion points
  - Output issues
  - Open blockers

### 1:00 - 2:00 — Validation and Scoring

- Review generated JSON against schema
- Compare outputs to known-good configs on critical fields
- Record field-level accuracy observations

### 2:00 - 2:45 — Final Refinement

- Improve agent instructions/examples one last time
- Select 3 demo-ready SOWs
- Prepare backup example in case one run is weak

### 2:45 - 3:00 — Demo Prep

- Lock the final workflow
- Assign speakers / flow for showcase
- Prepare the privacy and roadmap explanation

---

## Team Roles

| Role | Responsibility |
|---|---|
| **Agent workflow owner** | Builds and updates the Agent Designer agent |
| **Data / examples owner** | Manages SOWs, known-good outputs, schema, and reference examples |
| **Validation / scoring owner** | Checks generated JSON against schema and expected outputs |
| **Privacy / narrative owner** | Documents how data is handled and how to explain limitations |
| **Demo owner** | Prepares the final 3 runs and showcase flow |

If the team is small, combine roles. If the team is larger, assign 1-2 people per workstream.

---

## Core Messages To Keep Repeating

- Privacy and accuracy are the priorities
- Low-code first, but output still needs review and validation
- One working path first, polish second
- The goal is a convincing MVP, not a production platform in one day

---

## Risks / Fallbacks

| Risk | Fallback |
|---|---|
| Agent output is inconsistent | Refine instructions and add better examples |
| Schema alignment is weak | Tighten expected output structure and validate manually |
| Privacy concerns block direct document input | Narrow the demo to approved sample content and explain preprocessing as a future step |
| One SOW performs poorly | Use backup examples for the final showcase |

---

## Showcase Story

1. **Problem:** Manual SOW parsing is slow and error-prone
2. **Solution:** Low-code Gemini Enterprise agent generates chamber config JSON
3. **Controls:** Privacy-aware handling, structured output, validation against expected schema
4. **Outcome:** Faster path from approved SOW to deployment-ready config
5. **Next step:** Stronger productionization with preprocessing, validation, and pipeline integration if needed
