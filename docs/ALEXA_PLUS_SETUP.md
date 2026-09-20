# Exposing DID IT to Alexa+

Alexa+ integrates with **self-hosted MCP servers over Streamable HTTP**
(track requirement: MCP spec **2025-11-25 or later**). DID IT speaks it —
verified live: the smoke run prints `PROTOCOL_VERSION_NEGOTIATED: 2025-11-25`.

## 1. Run the server, reachable from the internet

```bash
DID_IT_HOST=0.0.0.0 DID_IT_PORT=8765 python -m server.app
```

Alexa+ needs a public HTTPS URL. Quickest tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8765   # or ngrok http 8765
# -> https://<something>.trycloudflare.com/mcp
```

Production-ish alternative: any HTTPS reverse proxy (Caddy/nginx) in front of
the port, or a small cloud instance.

## 2. Register the MCP server with Alexa+

Follow the current Alexa+ Preview developer flow (Amazon Developer Console →
Alexa+ → developer tools) and add the server URL:

```
https://<your-public-host>/mcp
```

Alexa+ will discover the three tools via `tools/list`:

| Tool | Alexa+ usage |
|---|---|
| `run_task(task, steps?)` | "Alexa, back up my photos" → task text; free-text goes through the planner |
| `get_receipt(receipt_id)` | "read me the last receipt" — re-read the proof |
| `list_receipts(limit)` | "what did you get done today?" |

## 3. Verify locally before registering

```bash
# one-shot MCP handshake over Streamable HTTP:
python scripts/smoke_e2e.py          # boots the server, full tool round-trip
npx @modelcontextprotocol/inspector # interactive: connect to http://127.0.0.1:8765/mcp
```

## Security notes (self-hosting)

- The server is stateless (no session data kept); receipts persist on disk.
- Bind to `127.0.0.1` by default; expose publicly **only** behind your tunnel
  of choice with the auth layer that tunnel provides.
- Executors touch the local filesystem deliberately (that's the product);
  sandbox by running under a dedicated user/container when exposing publicly.