import logging

from slack_sdk.webhook.async_client import AsyncWebhookClient

from config import settings
from constants import MAX_TRANSCRIPT_CHARS, TRANSCRIPT_TRUNCATION_SUFFIX
from models import BolnaPayload

logger = logging.getLogger(__name__)

_client = AsyncWebhookClient(settings.slack_webhook_url)


def _resolve_duration(payload: BolnaPayload) -> str:
    if payload.telephony_data and payload.telephony_data.duration:
        return f"{payload.telephony_data.duration}s"
    if payload.conversation_time is not None:
        return f"{int(payload.conversation_time)}s"
    return "N/A"


def _build_blocks(payload: BolnaPayload) -> list[dict]:
    transcript = payload.transcript or "No transcript available"
    if len(transcript) > MAX_TRANSCRIPT_CHARS:
        transcript = transcript[:MAX_TRANSCRIPT_CHARS] + TRANSCRIPT_TRUNCATION_SUFFIX

    duration = _resolve_duration(payload)

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "Call Completed"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Call ID:*\n`{payload.id}`"},
                {"type": "mrkdwn", "text": f"*Agent ID:*\n`{payload.agent_id}`"},
                {"type": "mrkdwn", "text": f"*Duration:*\n{duration}"},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Transcript:*\n```{transcript}```",
            },
        },
    ]


async def send_call_alert(payload: BolnaPayload) -> None:
    response = await _client.send(
        text=f"Call {payload.id} completed",
        blocks=_build_blocks(payload),
    )
    if response.status_code != 200:
        logger.error("Slack webhook returned %s: %s", response.status_code, response.body)
    else:
        logger.info("Slack alert sent for call %s", payload.id)
