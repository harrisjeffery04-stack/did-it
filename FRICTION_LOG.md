# FRICTION LOG — DID IT (Amazon Developer Hackathon 2026)

Format per the hackathon's official friction-log spec:
**task attempted → steps taken → expected vs. actual → severity → workaround → actionable suggestion.**
Friction entries are logged *while building*, not retrofitted. Submissions with
friction logs can earn up to a 10% judging bonus.

---

## FE-001 — Reading the track requirements from the Devpost page
- **Task attempted:** Read the full "Requirements — What to Build" section (all four track definitions) to confirm the Alexa+ MCP-server requirements before committing to a track.
- **Steps taken:** (1) fetched `amazonappdev2026.devpost.com` with an automated reader; (2) re-fetched targeting the Requirements section; (3) fetched `/rules` and `/resources` sub-pages for full coverage.
- **Expected vs. actual:** Expected one clean page read. The main page reader returned content truncated in the middle of the track list — the Alexa+ paragraph (exactly the section we needed most) was cut out. `/rules` (135 KB) and `/resources` (86 KB) were also mid-page truncated at the same reader limit.
- **Severity:** minor.
- **Workaround:** `curl` the raw HTML and strip tags locally — full section recovered verbatim ("Build a self-hosted MCP server (spec 2025-11-25 or later, Streamable HTTP) or an Agent Skill").
- **Actionable suggestion:** Publish each track's requirements as its own sub-page (e.g., `/tracks/alexa-plus`), like the Resources page does per track. A single ever-growing Overview page fights deep-linking, diffing across updates, and automated readers.

## FE-002 — Confirming which MCP protocol version the installed SDK negotiates
- **Task attempted:** Confirm the server speaks MCP spec 2025-11-25 or later (the Alexa+ track's hard requirement) before building on top of it.
- **Steps taken:** (1) checked installed SDK (`mcp` 1.28.1); (2) looked for a one-command version check; (3) built `scripts/smoke_e2e.py` so the first real client handshake prints the negotiated version; (4) ran it.
- **Expected vs. actual:** Expected a quick `--version`-style check. Actual: the SDK does not advertise its supported protocol version anywhere convenient — it only surfaces in a live client handshake. Result: `PROTOCOL_VERSION_NEGOTIATED: 2025-11-25` — exactly the track's required spec, on the first handshake, on Python 3.14.
- **Severity:** minor — resolved in favor of the requirement; no workaround needed beyond the smoke script.
- **Workaround:** `scripts/smoke_e2e.py` now prints the negotiated protocol version on every run, doubling as a permanent compliance check for the repo.
- **Actionable suggestion:** Publish the expected MCP protocol-version handshake (or a conformance-check command) in the Alexa+ track docs so builders can verify compliance in one command instead of reading SDK source or hand-rolling a handshake.
