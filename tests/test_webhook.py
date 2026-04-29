import os

import pytest

# Must be set before any app module is imported so pydantic-settings picks it up
os.environ.setdefault("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/TEST/FAKE/URL")

from unittest.mock import AsyncMock, patch  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402

import main  # noqa: E402
from main import app  # noqa: E402
from slack import _build_blocks, _resolve_duration  # noqa: E402
from models import BolnaPayload, TelephonyData  # noqa: E402

client = TestClient(app)

COMPLETED_PAYLOAD = {
    "id": "call-001",
    "agent_id": "agent-001",
    "status": "completed",
    "transcript": "Agent: Hello. User: Hi there.",
    "telephony_data": {"duration": "42"},
    "conversation_time": 42.0,
}


@pytest.fixture(autouse=True)
def reset_state():
    main.processed_ids.clear()
    yield
    main.processed_ids.clear()


# --- /health ---

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- /webhook status filtering ---

def test_non_completed_status_ignored():
    for status in ("in-progress", "ringing", "queued", "failed"):
        with patch("main.send_call_alert", new_callable=AsyncMock) as mock_send:
            resp = client.post("/webhook", json={**COMPLETED_PAYLOAD, "status": status})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        mock_send.assert_not_called()


def test_completed_call_triggers_slack_alert():
    with patch("main.send_call_alert", new_callable=AsyncMock) as mock_send:
        resp = client.post("/webhook", json=COMPLETED_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    mock_send.assert_called_once()


# --- idempotency ---

def test_duplicate_call_id_sends_alert_only_once():
    with patch("main.send_call_alert", new_callable=AsyncMock) as mock_send:
        client.post("/webhook", json=COMPLETED_PAYLOAD)
        client.post("/webhook", json=COMPLETED_PAYLOAD)
    assert mock_send.call_count == 1


# --- resilience ---

def test_slack_failure_still_returns_200():
    with patch("main.send_call_alert", new_callable=AsyncMock, side_effect=Exception("Slack down")):
        resp = client.post("/webhook", json=COMPLETED_PAYLOAD)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_null_telephony_data_is_accepted():
    payload = {**COMPLETED_PAYLOAD, "id": "call-002", "telephony_data": None}
    with patch("main.send_call_alert", new_callable=AsyncMock) as mock_send:
        resp = client.post("/webhook", json=payload)
    assert resp.status_code == 200
    mock_send.assert_called_once()


# --- _resolve_duration unit tests ---

def test_duration_from_telephony_data():
    payload = BolnaPayload(
        id="x", agent_id="y", status="completed",
        telephony_data=TelephonyData(duration="55"),
    )
    assert _resolve_duration(payload) == "55s"


def test_duration_falls_back_to_conversation_time():
    payload = BolnaPayload(
        id="x", agent_id="y", status="completed",
        telephony_data=None,
        conversation_time=73.9,
    )
    assert _resolve_duration(payload) == "73s"


def test_duration_returns_na_when_both_missing():
    payload = BolnaPayload(id="x", agent_id="y", status="completed")
    assert _resolve_duration(payload) == "N/A"


# --- _build_blocks unit tests ---

def test_build_blocks_contains_all_four_fields():
    payload = BolnaPayload(
        id="call-abc",
        agent_id="agent-xyz",
        status="completed",
        transcript="Hello world",
        telephony_data=TelephonyData(duration="10"),
    )
    blocks = _build_blocks(payload)
    flat = str(blocks)
    assert "call-abc" in flat
    assert "agent-xyz" in flat
    assert "10s" in flat
    assert "Hello world" in flat


def test_build_blocks_truncates_long_transcript():
    payload = BolnaPayload(
        id="x", agent_id="y", status="completed",
        transcript="A" * 3000,
    )
    blocks = _build_blocks(payload)
    transcript_block = blocks[-1]["text"]["text"]
    assert "(truncated)" in transcript_block
    assert len(transcript_block) < 3100
