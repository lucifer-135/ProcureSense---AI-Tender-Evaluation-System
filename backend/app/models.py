import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from .database import Base
import enum


class TenderStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTING = "extracting_criteria"
    CRITERIA_EXTRACTED = "criteria_extracted"
    APPROVED = "approved"
    EVALUATING = "evaluating"
    COMPLETED = "completed"


class BidderStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    EXTRACTING_NAME = "extracting_name"
    EXTRACTING = "extracting_evidence"
    EVIDENCE_EXTRACTED = "evidence_extracted"
    COMPUTING = "computing_verdicts"
    VERDICTS_COMPUTED = "verdicts_computed"


class VerdictValue(str, enum.Enum):
    ELIGIBLE = "Eligible"
    NOT_ELIGIBLE = "Not Eligible"
    NEEDS_REVIEW = "Needs Manual Review"


class CriterionType(str, enum.Enum):
    TECHNICAL = "Technical"
    FINANCIAL = "Financial"
    COMPLIANCE = "Compliance"


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    extracted_text = Column(Text, default="")
    status = Column(String(50), default=TenderStatus.UPLOADED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    criteria = relationship("Criterion", back_populates="tender", cascade="all, delete-orphan")
    bidders = relationship("Bidder", back_populates="tender", cascade="all, delete-orphan")


class Criterion(Base):
    __tablename__ = "criteria"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    text = Column(Text, nullable=False)
    type = Column(String(50), default=CriterionType.TECHNICAL)
    is_mandatory = Column(Boolean, default=True)
    expected_value_type = Column(String(50), default="text")
    threshold = Column(String(500), default="")
    confidence = Column(Float, default=1.0)
    approved = Column(Boolean, default=False)

    tender = relationship("Tender", back_populates="criteria")
    evidence = relationship("BidderEvidence", back_populates="criterion")
    verdicts = relationship("Verdict", back_populates="criterion")


class Bidder(Base):
    __tablename__ = "bidders"

    id = Column(Integer, primary_key=True, index=True)
    tender_id = Column(Integer, ForeignKey("tenders.id"), nullable=False)
    name = Column(String(500), nullable=False, default="Extracting Name...")
    overall_verdict = Column(String(50), default="")
    status = Column(String(50), default=BidderStatus.UPLOADED)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tender = relationship("Tender", back_populates="bidders")
    documents = relationship("BidderDocument", back_populates="bidder", cascade="all, delete-orphan")
    evidence = relationship("BidderEvidence", back_populates="bidder", cascade="all, delete-orphan")
    verdicts = relationship("Verdict", back_populates="bidder", cascade="all, delete-orphan")


class BidderDocument(Base):
    __tablename__ = "bidder_documents"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    extracted_text = Column(Text, default="")

    bidder = relationship("Bidder", back_populates="documents")


class BidderEvidence(Base):
    __tablename__ = "bidder_evidence"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    criterion_id = Column(Integer, ForeignKey("criteria.id"), nullable=False)
    extracted_value = Column(Text, default="")
    source_doc = Column(String(500), default="")
    source_page = Column(String(100), default="")
    verbatim_quote = Column(Text, default="")
    confidence = Column(Float, default=0.0)

    bidder = relationship("Bidder", back_populates="evidence")
    criterion = relationship("Criterion", back_populates="evidence")


class Verdict(Base):
    __tablename__ = "verdicts"

    id = Column(Integer, primary_key=True, index=True)
    bidder_id = Column(Integer, ForeignKey("bidders.id"), nullable=False)
    criterion_id = Column(Integer, ForeignKey("criteria.id"), nullable=False)
    verdict = Column(String(50), default="")
    explanation = Column(Text, default="")
    extraction_confidence = Column(Float, default=0.0)
    match_confidence = Column(Float, default=0.0)
    human_decision = Column(String(50), default="")
    human_reason = Column(Text, default="")

    bidder = relationship("Bidder", back_populates="verdicts")
    criterion = relationship("Criterion", back_populates="verdicts")
    reviews = relationship("HumanReview", back_populates="verdict", cascade="all, delete-orphan")


class HumanReview(Base):
    __tablename__ = "human_reviews"

    id = Column(Integer, primary_key=True, index=True)
    verdict_id = Column(Integer, ForeignKey("verdicts.id"), nullable=False)
    decision = Column(String(50), nullable=False)
    reason = Column(Text, default="")
    reviewer = Column(String(200), default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    verdict = relationship("Verdict", back_populates="reviews")
