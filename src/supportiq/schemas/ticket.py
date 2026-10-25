
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TicketCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=100)
    message: str = Field(min_length=1, max_length=5000)


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    message: str
    status: Literal["open", "in_progress", "resolved"]
    created_at: datetime


class TicketStatusUpdate(BaseModel):
    status: Literal["open", "in_progress", "resolved"]


class TicketCountResponse(BaseModel):
    total: int
    open: int
    in_progress: int
    resolved: int


class AIReplyResponse(BaseModel):
    ticket_id: int
    draft_reply: str
    requires_human_review: bool = True
