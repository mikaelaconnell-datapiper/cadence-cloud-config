# Slide Deck — Cloud Config Right Sizing Agent

Use this to build your Google Slides presentation for the dev day morning kickoff.

---

## Slide 1: Title

**Cloud Config Right Sizing Agent**

Low-Code SOW-to-Config with Gemini Enterprise

Cadence Dev Day | April 2, 2026

---

## Slide 2: The Problem

**Today's workflow is manual and error-prone**

- Engineers read multi-page SOW documents
- Manually translate requirements into cloud config files for the CICD pipeline
- Risk: missed fields, inconsistent sizing, slow turnaround
- No standardized way to validate configs before deployment

---

## Slide 3: The Solution

**A low-code agent that reads the SOW and generates the config**

SOW Document → Gemini Enterprise Agent → Validated Config JSON

- Upload an approved SOW to the agent
- Agent extracts infrastructure requirements and generates config JSON
- Output is validated against the CICD schema
- Privacy-aware: customer data is handled according to approved guidelines

---

## Slide 4: How It Works

**Agent Designer Workflow**

1. **Input** — Approved SOW document uploaded to Agent Designer
2. **Generate** — Agent extracts requirements and produces config JSON
3. **Validate** — Output checked against the target schema
4. **Score** — Compare to known-good configs on critical fields
5. **Refine** — Improve agent instructions based on results

---

## Slide 5: Privacy

**Customer data handling is a priority**

- Only approved SOW content is processed through the agent
- Gemini Enterprise provides enterprise-grade security controls
- For production: a preprocessing step would redact PII before model input
- The model only needs infrastructure requirements — not customer identifiers

---

## Slide 6: What We're Building Today

**Goals for the session:**

1. Build a working agent in Gemini Enterprise Agent Designer
2. Run at least 3 end-to-end tests with approved SOWs
3. Validate JSON output against the CICD schema
4. Review accuracy against known-good configs
5. Prepare a demo with a clear narrative

---

## Slide 7: The Plan

| Time | Activity |
|---|---|
| 9:30 - 10:00 | Setup — confirm inputs, schema, success criteria |
| 10:00 - 10:45 | Build the agent in Agent Designer |
| 10:45 - 11:15 | Refine instructions and examples |
| 11:15 - 12:00 | Test with additional SOWs |
| 12:00 - 1:00 | Lunch / regroup |
| 1:00 - 2:00 | Validation and scoring |
| 2:00 - 2:45 | Final refinement and demo prep |
| 2:45 - 3:00 | Lock demo flow |

---

## Slide 8: Team Roles

| Role | Responsibility |
|---|---|
| Agent workflow owner | Builds and updates the agent |
| Data / examples owner | Manages SOWs, configs, and schema |
| Validation / scoring owner | Checks output quality |
| Privacy / narrative owner | Documents data handling approach |
| Demo owner | Prepares the 3 showcase runs |

Combine roles if the team is small.

---

## Slide 9: Showcase Story

1. **Problem:** Manual SOW parsing is slow and error-prone
2. **Solution:** Low-code Gemini Enterprise agent generates config JSON
3. **Controls:** Privacy-aware handling, structured output, schema validation
4. **Outcome:** Faster path from approved SOW to deployment-ready config
5. **Next step:** Productionization with preprocessing, validation, and pipeline integration

---

## Slide 10 (Optional): Risks and Fallbacks

| Risk | Fallback |
|---|---|
| Agent output is inconsistent | Refine instructions, add better examples |
| Schema alignment is weak | Validate manually, tighten structure |
| Privacy blocks direct input | Use approved sample content, explain preprocessing |
| One SOW performs poorly | Use backup examples for showcase |

**Core message:** One working path first, polish second. The goal is a convincing MVP, not a production platform in one day.
