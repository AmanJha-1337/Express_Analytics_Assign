from typing import Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000)


class SourceItem(BaseModel):
    source: str
    page: int | None = None
    chunk_id: str | None = None
    excerpt: str | None = None


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceItem] = []
    retries: int = 0


class FeedbackRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    rating: str = Field(..., pattern="^(up|down)$")
    comment: str | None = None


class DocumentItem(BaseModel):
    filename: str
    chunks: int
    type: str
    added_at: str


class IngestResponse(BaseModel):
    message: str
    ingested: list[dict[str, Any]]
