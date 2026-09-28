"""The 'contract': the exact shape an AI answer must have before we trust it."""

from typing import Literal

from pydantic import BaseModel, Field


class TicketClassification(BaseModel):
    category: Literal["billing", "technical", "shipping", "account", "other"]
    priority: Literal["low", "medium", "high", "urgent"]
    summary: str = Field(min_length=1, max_length=200)
    confidence: float = Field(ge=0.0, le=1.0)
