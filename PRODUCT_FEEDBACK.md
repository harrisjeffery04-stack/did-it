# PRODUCT FEEDBACK — DID IT (per-tool, as required)

The hackathon requires product feedback on EVERY tool/API/SDK used: purpose,
what worked, what needs work, onboarding feel, and would-we-build-again.
This file is updated as each tool is actually used (not written from marketing copy).

| Tool / API / SDK | Purpose in DID IT | Worked | Needs work | Onboarding | Build again? |
|---|---|---|---|---|---|
| MCP Python SDK (`mcp` 1.28.1) | Server core: tools, Streamable HTTP transport | FastMCP gave a working stateless Streamable HTTP server with typed tool schemas, zero protocol code; first handshake negotiated spec 2025-11-25 on Python 3.14; client+server in one package | Supported protocol version isn't advertised by any one-command check — it only surfaces in a live handshake (see FRICTION_LOG FE-002) | Smooth, code-first; the smoke script doubles as the spec check | Yes — already have |
| Devpost (amazonappdev2026) | Hackathon rules, resources, submission | Full pages reachable with workaround (see FRICTION_LOG FE-001); track requirements crisp once read verbatim; friction-log bonus is a genuinely novel incentive | Overview page truncates in automated readers; track details not sub-paginated | Smooth — clear prize/track structure | (pending submission flow) |
| Amazon Devices Builder Tools / docs | Alexa+ MCP reference (planned) | (pending) | (pending) | (pending) | (pending) |
| AWS Bedrock (via boto3, optional planner) | LLM planner for free-text tasks (planned) | (pending) | (pending) | (pending) | (pending) |

<!-- Entries are finalized only after real use; placeholders above are honest stubs. -->