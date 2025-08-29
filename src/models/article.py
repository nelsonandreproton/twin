from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Article(BaseModel):
    title: str
    url: str
    platform: str  # 'linkedin', 'medium', 'facebook', 'npblog'
    content: Optional[str] = None
    summary: Optional[str] = None
    published_date: Optional[datetime] = None
    author: str
    tags: List[str] = Field(default_factory=list)
    engagement_metrics: Optional[dict] = None  # likes, comments, shares, etc.
    additional_data: Optional[dict] = None  # Additional metadata for platform-specific data
    scraped_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }