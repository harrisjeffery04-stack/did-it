# Demo video storyboard (< 3:00)

Rules: public YouTube/Vimeo, English, lead with the best material — judges
are not required to watch past 3:00. Lead with a receipt being earned.

| Time | Beat | On screen | Say |
|---|---|---|---|
| 0:00–0:15 | The hook | Receipt card filling in, `done-and-proven` badge flashing green | "Every assistant says 'OK, done.' Ours proves it." |
| 0:15–0:50 | Voice task, real proof | Demo UI: mic click → "back up my photos" → receipt: 3 files, each with **sha256_source == sha256_copy** | "DID IT copies the files, then re-reads every copy and compares cryptographic hashes. Same bytes, proven — not promised." |
| 0:50–1:20 | The trust trap | Second terminal: `echo x >> demo/fixtures/photos/IMG_0001.jpg` → re-run → NEW receipt shows a different sha256 for IMG_0001; old receipt keeps the old hash (show both) | "If anything changed, the receipt shows it. Evidence is gathered per run — old promises can't be recycled." |
| 1:20–1:45 | Not just files | "check example.com" → HTTP status, latency, body sha256, text-found index | "Web checks, disk checks, folder tidying — every executor returns evidence, not vibes." |
| 1:45–2:10 | The open standard, proven | Terminal: `python scripts/smoke_e2e.py` → `PROTOCOL_VERSION_NEGOTIATED: 2025-11-25` and PASS | "This is a real MCP server — Streamable HTTP, spec 2025-11-25 — the same open standard Alexa+ integrates." |
| 2:10–2:30 | Alexa+ path | ALEXA_PLUS_SETUP.md: tunnel + URL in the Alexa+ console; `tools/list` shows run_task | "Alexa+ points at this URL and gets the same tools the browser just used." |
| 2:30–2:50 | The thesis | Code: planner (Bedrock plans) vs executors (machine verifies) | "The LLM may propose. Only the machine verifies. That's DID IT." |
| 2:50–3:00 | Close | GitHub URL, MIT, friction log mention | "Open source under MIT, at github.com/harrisjeffery04-stack/did-it. Friction logs from the build are in the repo." |

Shot list (practical):
1. Browser demo at http://127.0.0.1:8770 (run_local.sh) — 1600×900, dark mode.
2. Terminal split: smoke_e2e.py + `cat receipts/rcpt_*.json | jq`.
3. Optional: MCP Inspector showing the three tools + a live call.

Honesty guardrails for the video:
- Show the real receipts; no mockups.
- If Bedrock credentials aren't live by filming day, say "optional Bedrock
  planner" and show the LocalPlanner path — the receipts are identical.

## Run sheet (record day — ~10 min; all machine-prep done)

Demo state is deterministic: `./scripts/run_local.sh` seeds the photos, resets
the messy folder, and clears the vault on every start — every take starts
identical.

1. `./scripts/run_local.sh` → UI at http://127.0.0.1:8770 (server at :8765/mcp).
2. Warm-up off camera: click **Back up my photos** once (allow mic; the UI
   speaks the verdict — mute the tab if it competes with narration).
3. Record: Win+G → Capture → ● Record (or OBS) · 1600×900 · dark mode · quiet mic.
4. Follow the beats; for the trust-trap beat run the echo command above between
   takes, then show both receipts (new hash vs old hash for the same file).
5. Upload public: title "DID IT — done AND proven done | Amazon Developer
   Hackathon 2026" · description: one-liner + repo URL
   https://github.com/harrisjeffery04-stack/did-it