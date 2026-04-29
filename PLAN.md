# Bolna → Slack Integration Plan

## Task
Send a Slack alert whenever a Bolna call ends, containing: `id`, `agent_id`, `duration`, `transcript`.

## Architecture
```
Bolna (webhook POST on status change)
        ↓
FastAPI server (filter → extract → format)
        ↓
Slack Incoming Webhook (Block Kit message)
```

## Tech Stack
- **Python 3.11**
- **FastAPI** — webhook receiver
- **slack_sdk** — `WebhookClient` for Slack (one-liner)
- **pydantic** — payload validation (built into FastAPI)
- **python-dotenv** — env var management
- **uvicorn** — ASGI server
- **ngrok** — expose local server for testing

## Project Structure
```
bolna-slack-integration/
├── main.py
├── requirements.txt
├── .env              # real secrets, gitignored
├── .env.sample       # template, committed
├── .gitignore
└── README.md
```

## Bolna Payload (key fields)
```json
{
  "id": "...",
  "agent_id": "...",
  "status": "completed",
  "transcript": "...",
  "telephony_data": {
    "duration": 45
  }
}
```
> `duration` lives at `telephony_data.duration`. Bolna fires the webhook on every status change — filter for `status == "completed"` only.

## 10-Step Execution Plan

### Step 1 — Bolna Setup
- Sign up at platform.bolna.ai
- Clone template agent `d311e737-70e6-4075-bef6-c0ef3a7026b4`
- Copy API key from settings

### Step 2 — Slack Setup
- Go to api.slack.com/apps → Create New App
- Enable Incoming Webhooks → Install to channel
- Copy `https://hooks.slack.com/services/...` URL

### Step 3 — Scaffold Project
- Create `bolna-slack-integration/` directory
- `requirements.txt`: `fastapi`, `uvicorn`, `slack_sdk`, `python-dotenv`
- `.env.sample` with placeholder keys
- `.gitignore` ignoring `.env`

### Step 4 — Write Webhook Endpoint
`POST /webhook` with Pydantic model covering:
- `id`, `agent_id`, `status`, `transcript`, `telephony_data`

### Step 5 — Filter for Completed Calls Only
Guard clause at the top:
```python
if payload.status != "completed":
    return {"ok": True}  # return 200 immediately, do nothing
```
> Critical: return 200 fast — Bolna will retry if your server is slow or errors.

### Step 6 — Idempotency Check
Maintain an in-memory `set` of processed call IDs:
```python
if payload.id in processed_ids:
    return {"ok": True}
processed_ids.add(payload.id)
```
> Prevents duplicate Slack alerts if Bolna retries the webhook.

### Step 7 — Extract the Four Required Fields
```python
call_id    = payload.id
agent_id   = payload.agent_id
duration   = payload.telephony_data.duration
transcript = payload.transcript
```

### Step 8 — Format + Send Slack Alert
Use `slack_sdk.WebhookClient` with Block Kit:
```python
client = WebhookClient(SLACK_WEBHOOK_URL)
client.send(
    text=f"Call {call_id} completed",
    blocks=[...]  # Block Kit with all 4 fields
)
```

### Step 9 — Expose + Connect to Bolna
```bash
uvicorn main:app --port 8000
ngrok http 8000
```
- Copy ngrok HTTPS URL
- Paste into Bolna agent → Analytics tab → "Push all execution data to webhook" → Save
- Whitelist Bolna's static IP `13.203.39.153` (optional but shows doc awareness)

### Step 10 — Test + Package + Submit
- Trigger a test call in Bolna
- Verify Slack message arrives with all 4 fields
- Check logs for errors
- Clean up: ensure no real secrets in code
- Write concise `README.md` (setup + run instructions)
- Zip the directory
- Submit to `ie+submissions@bolna.ai`

## Key Differentiators
| Feature | Why it matters |
|---|---|
| Return 200 immediately | Prevents Bolna webhook retries on slow processing |
| Idempotency set | No duplicate Slack alerts on retry |
| Pydantic model | Type-safe payload parsing, clean error handling |
| Block Kit formatting | Readable, professional Slack message |
| IP whitelisting note | Shows thorough doc reading |
| `.env.sample` in zip | Clean submission with no exposed secrets |
