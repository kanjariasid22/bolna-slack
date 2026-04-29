from typing import Optional

from pydantic import BaseModel, ConfigDict


class TelephonyData(BaseModel):
    model_config = ConfigDict(extra="ignore")

    duration: Optional[str] = None


class BolnaPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    agent_id: str
    status: str
    transcript: Optional[str] = None
    telephony_data: Optional[TelephonyData] = None
    conversation_time: Optional[float] = None
