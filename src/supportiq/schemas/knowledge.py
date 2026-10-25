
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeArticleCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10, max_length=20000)
    category: str = Field(default="general", min_length=2, max_length=100)


class KnowledgeArticleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    is_active: bool
    created_at: datetime
    
