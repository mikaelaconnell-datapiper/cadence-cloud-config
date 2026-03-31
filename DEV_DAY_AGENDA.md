# Cloud Config Right Sizing Agent — Dev Day Agenda

**Date:** April 2, 2026
**Location:** Google SF Office
**Use Case 4:** Cloud Config Right Sizing Agent (Low Code)

---

## 9:00 AM — Kickoff (30 min)

- Welcome and introductions
- **The problem:** Engineers manually read SOW documents and hand-build cloud configs for the CICD pipeline. This is slow, inconsistent, and doesn't scale.
- **The solution:** An AI agent that reads a SOW and generates a validated config JSON automatically.
- **Architecture overview:** 5-station pipeline
  - Extract text from SOW → Sanitize PII → Generate config via Gemini → Validate against schema → Score accuracy
- **Data privacy approach:** Customer PII is redacted before any content reaches the model
- **Goals for today:**
  1. Build a working agent in Gemini Enterprise Agent Designer
  2. Test with real SOW documents
  3. Validate and score the output
  4. Discuss the production path

---

## 9:30 AM — Build Session 1: Agent Designer (1.5 hours)

### Create the Agent (30 min)
- Open Gemini Enterprise → Agent Designer
- Create a new agent with instructions for SOW parsing and config generation
- Define the target JSON schema (fields, types, required vs optional)
- Set the model and configure output format

### Add Reference Examples (20 min)
- Upload sample SOW/config pairs as reference materials
- Update agent instructions to use few-shot examples
- Show how examples improve output quality

### Test with SOW Documents (30 min)
- Upload SOW documents to the agent
- Review the generated config JSON
- Identify what the agent gets right and what needs tuning
- Iterate on the agent instructions based on results

---

## 11:00 AM — Break (15 min)

---

## 11:15 AM — Build Session 2: Privacy and Validation (1.5 hours)

### Data Privacy: PII Sanitization (30 min)
- Demo the sanitization layer — show a raw SOW vs the sanitized version
- Walk through what gets redacted (emails, phones, names, account IDs, pricing)
- Walk through what stays (service counts, storage sizes, compute specs, environment type)
- Discuss: should sanitization happen before or inside the agent?

### Output Validation (30 min)
- Take the config JSON from Agent Designer
- Validate it against the CICD JSON schema
- Review any validation errors and what they mean
- Show the schema repair approach — send errors back to the model for self-correction

### Accuracy Scoring (30 min)
- Compare generated configs against known-good configs
- Review field-level accuracy report
- Identify which fields the agent gets right consistently vs where it struggles
- Discuss what accuracy threshold is acceptable for production

---

## 12:45 PM — Lunch (1 hour)

---

## 1:45 PM — Build Session 3: Refinement and Integration (1.5 hours)

### Improve Accuracy (45 min)
- Refine agent instructions based on morning results
- Add more reference examples for edge cases
- Test with additional SOW documents
- Track accuracy improvements across iterations

### Production Path Discussion (45 min)
- Agent Designer for prototyping vs coded pipeline for CICD integration
- Where does the config JSON go after generation? (GCS bucket → CICD pipeline)
- How to handle low-confidence configs (human review workflow)
- Security considerations for production deployment
- Next steps and timeline

---

## 3:15 PM — Wrap-Up (30 min)

- End-to-end demo of the final solution
- Review accuracy results across all test SOWs
- Summary of what was built and key decisions made
- Action items and next steps
- Q&A

---

## Quick Reference

| Resource | Location |
|---|---|
| Starter code (optional) | `github.com/mikaelaconnell-datapiper/cadence-cloud-config` |
| Agent Designer | Gemini Enterprise → Agents → + New agent |
| JSON schema | `config_schema.json` in the repo |
| Sample SOW/config pairs | `data/` directory in the repo |

---

## Target JSON Schema Fields

| Field | Type | Required |
|---|---|---|
| customer_name | string | yes |
| environment_tier | small / medium / large / enterprise | yes |
| compute.instance_type | string (e.g., n2-standard-4) | yes |
| compute.instance_count | integer | yes |
| compute.vcpus_per_instance | integer | yes |
| compute.memory_gb_per_instance | integer | yes |
| storage.storage_type | pd-standard / pd-ssd / pd-balanced | yes |
| storage.total_storage_gb | integer | yes |
| storage.iops_required | integer | yes |
| networking.vpc_cidr | string (e.g., 10.0.0.0/16) | yes |
| networking.subnet_count | integer | yes |
| networking.load_balancer | boolean | yes |
| services | array of {service_name, enabled, configuration} | yes |
| high_availability | boolean | no |
| backup_enabled | boolean | no |
| estimated_users | integer | no |
