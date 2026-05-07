from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Tender ──────────────────────────────────────────────────────────────
class TenderResponse(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Criterion ───────────────────────────────────────────────────────────
class CriterionCreate(BaseModel):
    text: str
    type: str = "Technical"
    is_mandatory: bool = True
    expected_value_type: str = "text"
    threshold: str = ""


class CriterionUpdate(BaseModel):
    text: Optional[str] = None
    type: Optional[str] = None
    is_mandatory: Optional[bool] = None
    expected_value_type: Optional[str] = None
    threshold: Optional[str] = None


class CriterionResponse(BaseModel):
    id: int
    tender_id: int
    text: str
    type: str
    is_mandatory: bool
    expected_value_type: str
    threshold: str
    confidence: float
    approved: bool

    class Config:
        from_attributes = True


# ── Bidder ──────────────────────────────────────────────────────────────
class BidderResponse(BaseModel):
    id: int
    tender_id: int
    name: str
    overall_verdict: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── BidderDocument ──────────────────────────────────────────────────────
class BidderDocumentResponse(BaseModel):
    id: int
    bidder_id: int
    filename: str

    class Config:
        from_attributes = True


# ── BidderEvidence ──────────────────────────────────────────────────────
class EvidenceResponse(BaseModel):
    id: int
    bidder_id: int
    criterion_id: int
    extracted_value: str
    source_doc: str
    source_page: str
    verbatim_quote: str
    confidence: float

    class Config:
        from_attributes = True


class EvidenceWithCriterion(EvidenceResponse):
    criterion_text: str = ""
    criterion_type: str = ""


# ── Verdict ─────────────────────────────────────────────────────────────
class VerdictResponse(BaseModel):
    id: int
    bidder_id: int
    criterion_id: int
    verdict: str
    explanation: str
    extraction_confidence: float
    match_confidence: float
    human_decision: str
    human_reason: str
    criterion_text: str = ""
    criterion_type: str = ""
    is_mandatory: bool = True
    extracted_value: str = ""
    source_doc: str = ""
    verbatim_quote: str = ""

    class Config:
        from_attributes = True


class VerdictListResponse(BaseModel):
    overall_verdict: str
    bidder_name: str
    verdicts: List[VerdictResponse]


# ── Human Review ────────────────────────────────────────────────────────
class HumanReviewCreate(BaseModel):
    decision: str
    reason: str = ""
    reviewer: str = ""


class HumanReviewResponse(BaseModel):
    id: int
    verdict_id: int
    decision: str
    reason: str
    reviewer: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Review Queue ────────────────────────────────────────────────────────
class ReviewQueueItem(BaseModel):
    verdict_id: int
    bidder_id: int
    bidder_name: str
    criterion_id: int
    criterion_text: str
    criterion_type: str
    extracted_value: str
    source_doc: str
    source_page: str
    verbatim_quote: str
    explanation: str
    extraction_confidence: float
    match_confidence: float
