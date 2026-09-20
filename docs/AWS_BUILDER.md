# AWS Builder mini-challenge — Amazon Bedrock integration

**The design principle: the LLM may propose; only the machine verifies.**

Bedrock (Anthropic Claude) is used for exactly one job: planning free-text
tasks into `[{action, args}]` steps. Every planned step then runs through the
same verified executors and produces the same receipts — the LLM can never
mark anything "done".

## Where it lives

- `server/planner.py` → `BedrockPlanner`: builds a JSON-schema-constrained
  prompt, calls `bedrock-runtime` `invoke_model`, validates the returned
  plan against the allowed action list, and **asserts** before executing.
- `server/planner.py` → `get_planner()`: auto-detects AWS credentials
  (botocore session) and picks BedrockPlanner when present; LocalPlanner
  otherwise. Zero-config upgrade path — the receipts pipeline is identical
  either way, so nothing else changes when credentials arrive.

## Enable it

```bash
pip install boto3                      # or: pip install -e ".[bedrock]"
aws configure                          # or env credentials
export PROVENDONE_BEDROCK_MODEL="us.anthropic.claude-3-5-haiku-20241022-v1:0"
python scripts/smoke_e2e.py            # same tests, now Bedrock-planned free text
```

Without credentials everything still works: LocalPlanner handles the common
task phrasings, and unparseable tasks return an **honest failure receipt**
pointing to this file.

## Documented integration summary (for judges)

| Item | Value |
|---|---|
| AWS service | Amazon Bedrock (Bedrock runtime `invoke_model`) |
| Model | `us.anthropic.claude-3-5-haiko-*` (env-tunable via `PROVENDONE_BEDROCK_MODEL`) |
| Role in project | Task planner (free text → structured steps) |
| Guardrails | Plan schema validation + allowed-action whitelist + assertion; verification stays mechanical |
| Status | Implemented and credential-guarded; live run pending AWS credentials (the hackathon offers a $150 credit request form) |

## Why Bedrock belongs here (and only here)

Planners are probabilistic; receipts must be deterministic. Putting the LLM
in the planning seat (never the verification seat) is the whole thesis of the
product — and Bedrock is the natural, documented AWS home for that seat.