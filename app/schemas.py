from __future__ import annotations

from typing import Literal, List
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_id: str = Field(..., description="Unique source chunk identifier")
    source_title: str = Field(..., description="Human-readable document title")
    excerpt: str = Field(..., description="Short excerpt supporting the reasoning")
    relevance: str = Field(..., description="Why this source is relevant to the decision")


class DecisionOutput(BaseModel):
    decision: Literal["Option A", "Option B", "Option C", "Needs Review", "Not Recommended"]
    confidence: float = Field(..., ge=0, le=1)
    executive_summary: str
    reasoning: List[str] = Field(..., min_length=3, max_length=7)
    risks: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_next_steps: List[str] = Field(default_factory=list)
    evidence: List[EvidenceItem] = Field(..., min_length=2)
    memo_markdown: str
