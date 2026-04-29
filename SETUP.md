# Setup & Usage Guide

Complete walkthrough from zero to a working Slack alert on every Bolna call.

---

## Prerequisites

- Python 3.11+
- A Bolna account — [platform.bolna.ai](https://platform.bolna.ai)
- A Slack workspace where you can create apps
- [ngrok](https://ngrok.com/download) installed and authenticated

---

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 2. Create a Slack Incoming Webhook

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g. `Bolna Alerts`) and pick your workspace → **Create App**
3. In the left sidebar click **Incoming Webhooks** → toggle it **ON**
4. Scroll down → **Add New Webhook to Workspace** → pick a channel → **Allow**
5. Copy the webhook URL — it looks like:
   ```
   https://hooks.slack.com/services/T.../B.../XXXXXXXXXXXX
   ```

---

## 3. Configure environment

```bash
cp .env.sample .env
```

Open `.env` and paste your Slack webhook URL:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../XXXXXXXXXXXX
```

---

## 4. Import the Bolna template agent

The assignment provides a pre-built template agent so you don't have to configure voice/LLM settings from scratch.

1. Make sure you're logged into [platform.bolna.ai](https://platform.bolna.ai)
2. Open the template import link:
   ```
   https://platform.bolna.ai/a/d311e737-70e6-4075-bef6-c0ef3a7026b4
   ```
3. Click **Import this agent** — it copies the agent into your account
4. Your agents list at [platform.bolna.ai/agents](https://platform.bolna.ai/agents) will show it

---

## 5. Start the server

```bash
uvicorn main:app --port 8000
```

Expected output:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Verify it's up:
```bash
curl http://localhost:8000/health
# {"status":"ok"}
```

---

## 6. Expose the server publicly with ngrok

If you haven't set up ngrok yet:

1. Download from [ngrok.com/download](https://ngrok.com/download)
2. Sign up for a free account and grab your authtoken from [dashboard.ngrok.com/get-started/your-authtoken](https://dashboard.ngrok.com/get-started/your-authtoken)
3. Authenticate once:
   ```bash
   ngrok config add-authtoken <YOUR_AUTHTOKEN>
   ```

Then start the tunnel:

```bash
ngrok http 8000
```

ngrok will print a forwarding URL, e.g.:
```
Forwarding  https://abc123.ngrok-free.app -> http://localhost:8000
```

Your webhook URL is:
```
https://abc123.ngrok-free.app/webhook
```

Quick sanity check:
```bash
curl https://abc123.ngrok-free.app/health
# {"status":"ok"}
```

> The free ngrok tier generates a new random URL every time you restart it. If you restart ngrok, update the webhook URL in your Bolna agent (step 7).

---

## 7. Connect the webhook to your Bolna agent

1. Open your imported agent in [platform.bolna.ai/agents](https://platform.bolna.ai/agents)
2. Go to the **Analytics** tab
3. Paste your full webhook URL into **"Push all execution data to webhook"**:
   ```
   https://abc123.ngrok-free.app/webhook
   ```
4. **Save** the agent

> Bolna webhooks originate from the static IP `13.203.39.153`. Whitelist it on any firewall sitting in front of your server.

---

## 8. Trigger a test call

Use the **Playground** tab inside your agent to initiate a call and let it run to completion.

**What to expect:**

Server logs:
```
INFO  Slack alert sent for call 4c06b4d1-4096-4561-919a-4f94539c8d4a
```

Slack message in your channel:
```
Call Completed
─────────────────────────────
Call ID    4c06b4d1-...
Agent ID   d311e737-...
Duration   42s
─────────────────────────────
Transcript
  Agent: Hello, how can I help you today?
  User: ...
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `SLACK_WEBHOOK_URL is not set` on startup | Check `.env` exists and the key is spelled correctly |
| No Slack message, but server logs show the call | Slack webhook URL is wrong — re-copy it from api.slack.com/apps |
| Bolna never hits `/webhook` | ngrok URL changed on restart — update it in the Analytics tab and save |
| Duplicate Slack messages | Expected on Bolna retries; the idempotency check drops duplicates after the first |
| `422 Unprocessable Entity` in logs | Bolna sent an unexpected payload shape — check logs for the validation error field |

---

## Packaging for submission

Once the end-to-end test passes, zip the project (exclude `.env` and `__pycache__`):

```bash
cd ..
zip -r bolna-slack-integration.zip task/ --exclude "task/.env" --exclude "task/__pycache__/*"
```

Submit the zip to `ie+submissions@bolna.ai`.
