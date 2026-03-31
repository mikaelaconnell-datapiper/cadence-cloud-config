# Cloud Config Right Sizing Agent — Dev Day Reference

## What We're Building

An AI agent that reads customer SOW (Statement of Work) documents and generates cloud infrastructure configuration JSON for the CICD deployment pipeline.

**SOW Document → Agent → Validated Config JSON**

---

## Priorities

1. **Privacy** — Customer PII must be handled carefully
2. **Output quality** — JSON must align to the target schema
3. **Clear demo** — 3 working end-to-end runs with a compelling story

---

## Working Approach

| Path | Tool | Purpose |
|---|---|---|
| **Primary** | Gemini Enterprise Agent Designer | Build the agent, generate config JSON |
| **Supporting** | Python/Gradio app (optional) | Validation, scoring, privacy/preprocessing discussion |

Focus on one working path first, then refine quality and demo flow.

---

## Agent Designer Workflow

### Creating the Agent
1. Open Gemini Enterprise → Agents → + New agent
2. Describe the agent's purpose: parse SOW documents and generate config JSON
3. Include the target JSON schema in the instructions
4. Upload reference SOW/config examples to improve accuracy
5. Test with an approved SOW document

### Iterating
- Review the JSON output — does it match the expected schema?
- Refine instructions based on what the agent gets wrong
- Add more examples to cover edge cases
- Re-test and compare accuracy

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

*This schema may be updated on dev day based on the actual CICD pipeline requirements.*

---

## Validation Checklist

When reviewing agent output, check:

- [ ] Valid JSON (no syntax errors)
- [ ] All required fields present
- [ ] Data types correct (strings, numbers, booleans)
- [ ] Enum values valid (environment_tier, storage_type)
- [ ] Values make sense for the SOW (right instance size, storage amount, etc.)

---

## Privacy Handling

**The concern:** Customer SOWs contain sensitive information — names, emails, phone numbers, account IDs, pricing.

**For today:** We're using approved SOW content provided by the Cadence team. The team has confirmed what content is safe to process through Gemini Enterprise.

**For production:** A preprocessing step would redact PII before any content reaches the model. This ensures the model only sees infrastructure requirements, never customer-identifying information.

---

## Showcase Story (for the afternoon demo)

1. **Problem:** Manual SOW parsing is slow and error-prone
2. **Solution:** Low-code Gemini Enterprise agent generates chamber config JSON
3. **Controls:** Privacy-aware handling, structured output, validation against expected schema
4. **Outcome:** Faster path from approved SOW to deployment-ready config
5. **Next step:** Productionization with preprocessing, validation, and pipeline integration

---

## Team Roles

| Role | Responsibility |
|---|---|
| Agent workflow owner | Builds and updates the Agent Designer agent |
| Data / examples owner | Manages SOWs, known-good outputs, schema, and reference examples |
| Validation / scoring owner | Checks generated JSON against schema and expected outputs |
| Privacy / narrative owner | Documents how data is handled and how to explain limitations |
| Demo owner | Prepares the final 3 runs and showcase flow |

If the team is small, combine roles.

---

## Starter Code (Optional)

If you want to run validation and scoring locally:

```
https://github.com/mikaelaconnell-datapiper/cadence-cloud-config
```

```bash
git clone <your-fork-url>
cd cadence-cloud-config
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# Open http://localhost:7860
```
