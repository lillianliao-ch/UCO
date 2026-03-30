from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class RawContentEvent(BaseModel):
    """
    全域统一的标准信息载荷协议 (Unified Content Event Schema).
    
    This acts as the strict contract bounding every single module regardless of their origin.
    Any new GitHub scraper or OpenCLI hook MUST parse its output into this exact Pydantic model
    before handing it over to the processing graph.
    """
    id: str = Field(..., description="Unique identifier or hash of the content fetched")
    source_channel: str = Field(..., description="Origin tracking identifier (e.g., 'opencli_hackernews', 'rss_36kr')")
    title: str = Field(..., description="Main headline of the article or post")
    content: str = Field(..., description="Raw text payload body (markdown, HTML, or plain text)")
    url: str = Field(..., description="Original absolute tracking URL of the post")
    media_urls: Optional[List[str]] = Field(default_factory=list, description="Array of images/videos associated with the event")
    timestamp: datetime = Field(default_factory=datetime.now, description="Data ingestion timestamp")
    score: Optional[float] = Field(default=None, description="Native score/likes/reposts if available natively on the platform")
    
    class Config:
        frozen = True # Make events immutable to ensure strict data tracing downstream
