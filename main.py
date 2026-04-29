import logging

from fastapi import FastAPI

from constants import COMPLETED_STATUS
from models import BolnaPayload
from slack import send_call_alert

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory idempotency guard — prevents duplicate Slack alerts when Bolna retries a webhook
processed_ids: set[str] = set()


@app.post("/webhook")
async def bolna_webhook(payload: BolnaPayload):
    if payload.status != COMPLETED_STATUS:
        return {"ok": True}

    if payload.id in processed_ids:
        logger.info("Duplicate webhook for call %s — skipped", payload.id)
        return {"ok": True}

    processed_ids.add(payload.id)

    try:
        await send_call_alert(payload)
    except Exception:
        # Log but still return 200 — Bolna must not retry due to our internal errors
        logger.exception("Failed to send Slack alert for call %s", payload.id)

    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
