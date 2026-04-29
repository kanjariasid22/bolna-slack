# Bolna → Slack Integration

Sends a Slack alert containing `id`, `agent_id`, `duration`, and `transcript` whenever a Bolna call reaches `completed` status.

## How it works

```
Bolna (webhook POST on every status change)
        ↓
FastAPI /webhook  (filters completed calls, idempotency check)
        ↓
Slack Incoming Webhook (Block Kit message)
```

## Stack

- **FastAPI** + **Uvicorn** — webhook receiver
- **slack_sdk** — `WebhookClient` for Slack
- **Pydantic** — payload validation
- **python-dotenv** — environment config

## Quick start

```bash
pip install -r requirements.txt
cp .env.sample .env        # add your SLACK_WEBHOOK_URL
uvicorn main:app --port 8000
```

For the full walkthrough — Slack app setup, Bolna agent configuration, tunnelling, and testing — see **[SETUP.md](SETUP.md)**.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/webhook` | Receives Bolna call events |
| `GET` | `/health` | Liveness check |
