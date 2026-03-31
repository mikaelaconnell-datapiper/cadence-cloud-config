# Agent Designer Guide — Cloud Config Right Sizing Agent

A step-by-step guide for building and refining the SOW-to-Config agent in Gemini Enterprise Agent Designer.

---

## Getting Started

### Opening Agent Designer

1. Go to Gemini Enterprise (the URL depends on the organization's setup)
2. In the left sidebar, click **Agents**
3. Click **+ New agent**
4. The Agent Designer page appears with a chat box at the bottom

### Two Ways to Build

- **Chat pane** (left side) — Describe the agent in plain language and let Agent Designer generate the initial version. Best for getting started quickly.
- **Designer pane** (right side) — Edit the agent's instructions, model settings, and data sources with direct control. Best for fine-tuning after the initial version is created.

---

## Step 1: Create the Agent

Paste the following into the chat box to create the initial agent:

```
Create an agent that accepts a customer Statement of Work (SOW) document
and generates a cloud infrastructure configuration JSON for a CICD
deployment pipeline.

The agent should:
1. Read the uploaded SOW document
2. Extract infrastructure requirements (compute, storage, networking,
   services, availability)
3. Generate a JSON configuration with these fields: customer_name,
   environment_tier (small/medium/large/enterprise), compute
   (instance_type, instance_count, vcpus_per_instance,
   memory_gb_per_instance), storage (storage_type, total_storage_gb,
   iops_required), networking (vpc_cidr, subnet_count, load_balancer),
   services array, high_availability, backup_enabled, estimated_users
4. Output only valid JSON — no markdown, no explanations
```

Click **Submit**. Agent Designer will generate the agent and show a preview.

---

## Step 2: Test the Agent

1. In the agent preview, type: **"Here is a SOW document"** and attach a sample SOW PDF
2. Review the JSON output:
   - Is it valid JSON?
   - Are all the required fields present?
   - Do the values make sense for what the SOW describes?
3. Note what the agent gets right and what it misses

---

## Step 3: Refine with Prompt Engineering

Click **Open in Agent Designer** to access the full configuration. The **Instructions** field is where prompt engineering happens — this is the most important part.

### Prompt Engineering Principles

**Be specific, not vague**

Bad:
```
Generate a cloud config from the SOW.
```

Good:
```
Read the SOW document and generate a JSON configuration with the following
structure. Extract the values directly from the document. If a value is
not explicitly stated, infer it conservatively based on the context.
```

**Include the schema in the instructions**

The agent needs to know exactly what the output should look like. Include the full JSON schema or a clear example of the expected output structure in the instructions.

**Tell the agent what NOT to do**

```
- Do not include markdown code fences around the JSON
- Do not add explanations or commentary before or after the JSON
- Do not hallucinate services that are not mentioned in the SOW
- Do not guess pricing or budget information
```

**Set clear rules for ambiguous cases**

```
- If the SOW does not specify an instance type, choose based on the
  vCPU and memory requirements
- Set environment_tier based on user count: small (<100), medium (100-499),
  large (500-999), enterprise (1000+)
- If high availability is not mentioned, default to false
- Only include services that are explicitly named in the SOW
```

---

## Step 4: Add Reference Examples (Few-Shot Prompting)

Few-shot prompting means showing the agent examples of correct input→output pairs before asking it to process a new SOW. This dramatically improves accuracy.

### How to add examples

In the agent instructions, add a section like:

```
REFERENCE EXAMPLES:

Example 1 — Small development environment:
Input SOW excerpt: "The team needs a lightweight dev environment for
50 developers. 2 services, 100 GB standard storage, no HA required."

Expected output:
{
  "customer_name": "...",
  "environment_tier": "small",
  "compute": {
    "instance_type": "e2-standard-2",
    "instance_count": 1,
    "vcpus_per_instance": 2,
    "memory_gb_per_instance": 8
  },
  "storage": {
    "storage_type": "pd-standard",
    "total_storage_gb": 100,
    "iops_required": 1500
  },
  ...
}

Example 2 — Enterprise production environment:
[another example with different scale]
```

### Tips for examples

- Include at least 2-3 examples covering different scales (small, medium, enterprise)
- Make sure the examples match the exact JSON schema being used
- The more realistic the examples, the better the agent performs
- If possible, use real SOW/config pairs (with PII removed)

---

## Step 5: Upload Reference Files

Instead of putting everything in the instructions, reference materials can be uploaded as files:

1. In Agent Designer, look for **Add files** or **Data sources**
2. Upload SOW/config pairs as reference documents
3. Update the instructions to reference them: "Use the uploaded reference examples to understand the expected mapping pattern"

This keeps the instructions cleaner and allows easy swapping of examples.

---

## Step 6: Iterate and Improve

After each test run, check the output and refine:

| Problem | Solution |
|---|---|
| Missing fields in the JSON | Add the missing fields to the schema in the instructions and specify they are required |
| Wrong values (e.g., wrong instance type) | Add a rule explaining how to choose that value, or add a reference example that covers that case |
| Extra text around the JSON | Add "Output ONLY valid JSON. No markdown, no explanations, no code fences" to the instructions |
| Inconsistent output format | Add a complete example of the exact expected JSON structure |
| Agent ignores part of the SOW | Add "Extract ALL relevant information from the SOW" and specify which sections to look for |
| Agent hallucinates services not in the SOW | Add "Only include services explicitly mentioned in the SOW" |

### The refinement loop

1. Run a SOW through the agent
2. Compare the output to what was expected
3. Identify the gap (missing field? wrong value? bad format?)
4. Update the instructions to address that specific gap
5. Run the same SOW again to verify the fix
6. Run a different SOW to make sure the fix didn't break something else

---

## Step 7: Prepare for the Demo

Once the agent is producing good output consistently:

1. **Select 3 strong SOWs** — Pick runs where the output is clean and accurate
2. **Have a backup** — Keep a 4th SOW ready in case one run is weak during the demo
3. **Know the story** — Be ready to explain:
   - What the agent does (SOW in → config JSON out)
   - How it handles privacy (what data reaches the model)
   - How accurate it is (field-level comparison to expected output)
   - What the production path looks like (validation, preprocessing, pipeline integration)

---

## Quick Reference: Agent Designer Settings

| Setting | Recommended Value |
|---|---|
| **Model** | Gemini 3.1 Pro (or whatever is available) |
| **Temperature** | Low (0.1-0.3) for consistent JSON output |
| **Output format** | Specify JSON-only in instructions |
| **Instructions length** | As detailed as needed — longer instructions with examples produce better results |

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Agent returns markdown instead of raw JSON | Add "Do not wrap output in code fences or markdown" to instructions |
| Agent returns different fields each time | Include the exact schema in instructions with all field names |
| Agent misreads the PDF | Try copying the text manually and pasting it instead of uploading the PDF |
| Output has the right structure but wrong values | Add more reference examples that cover similar scenarios |
| Agent is slow to respond | Long SOWs with detailed instructions may take 10-15 seconds — this is normal |
