from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class Webhook(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    webhook_url: str
    event_type: str  # document.uploaded, document.enriched
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)