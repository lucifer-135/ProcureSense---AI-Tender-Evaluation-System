from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Verdict, Bidder, Criterion, BidderEvidence, HumanReview, VerdictValue
from ..schemas import (
    VerdictResponse, VerdictListResponse,
    HumanReviewCreate, HumanReviewResponse, ReviewQueueItem,
)
from ..services.verdict_engine import recompute_overall_verdict

router = APIRouter(prefix="/api", tags=["verdicts"])


@router.get("/bidders/{bidder_id}/verdicts", response_model=VerdictListResponse)
def get_verdicts(bidder_id: int, db: Session = Depends(get_db)):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(404, "Bidder not found")

    verdicts = db.query(Verdict).filter(Verdict.bidder_id == bidder_id).all()
    verdict_list = []
    for v in verdicts:
        crit = db.query(Criterion).filter(Criterion.id == v.criterion_id).first()
        ev = (
            db.query(BidderEvidence)
            .filter(BidderEvidence.bidder_id == bidder_id, BidderEvidence.criterion_id == v.criterion_id)
            .first()
        )
        verdict_list.append(VerdictResponse(
            id=v.id,
            bidder_id=v.bidder_id,
            criterion_id=v.criterion_id,
            verdict=v.verdict,
            explanation=v.explanation,
            extraction_confidence=v.extraction_confidence,
            match_confidence=v.match_confidence,
            human_decision=v.human_decision or "",
            human_reason=v.human_reason or "",
            criterion_text=crit.text if crit else "",
            criterion_type=crit.type if crit else "",
            is_mandatory=crit.is_mandatory if crit else True,
            extracted_value=ev.extracted_value if ev else "",
            source_doc=ev.source_doc if ev else "",
            verbatim_quote=ev.verbatim_quote if ev else "",
        ))

    return VerdictListResponse(
        overall_verdict=bidder.overall_verdict or "",
        bidder_name=bidder.name,
        verdicts=verdict_list,
    )


@router.get("/tenders/{tender_id}/review-queue", response_model=List[ReviewQueueItem])
def get_review_queue(tender_id: int, db: Session = Depends(get_db)):
    bidders = db.query(Bidder).filter(Bidder.tender_id == tender_id).all()
    queue = []
    for bidder in bidders:
        verdicts = (
            db.query(Verdict)
            .filter(Verdict.bidder_id == bidder.id, Verdict.verdict == VerdictValue.NEEDS_REVIEW)
            .filter((Verdict.human_decision == "") | (Verdict.human_decision.is_(None)))
            .all()
        )
        for v in verdicts:
            crit = db.query(Criterion).filter(Criterion.id == v.criterion_id).first()
            ev = (
                db.query(BidderEvidence)
                .filter(BidderEvidence.bidder_id == bidder.id, BidderEvidence.criterion_id == v.criterion_id)
                .first()
            )
            queue.append(ReviewQueueItem(
                verdict_id=v.id,
                bidder_id=bidder.id,
                bidder_name=bidder.name,
                criterion_id=v.criterion_id,
                criterion_text=crit.text if crit else "",
                criterion_type=crit.type if crit else "",
                extracted_value=ev.extracted_value if ev else "",
                source_doc=ev.source_doc if ev else "",
                source_page=ev.source_page if ev else "",
                verbatim_quote=ev.verbatim_quote if ev else "",
                explanation=v.explanation,
                extraction_confidence=v.extraction_confidence,
                match_confidence=v.match_confidence,
            ))
    return queue


@router.post("/verdicts/{verdict_id}/review", response_model=HumanReviewResponse)
def submit_review(verdict_id: int, data: HumanReviewCreate, db: Session = Depends(get_db)):
    verdict = db.query(Verdict).filter(Verdict.id == verdict_id).first()
    if not verdict:
        raise HTTPException(404, "Verdict not found")

    review = HumanReview(
        verdict_id=verdict_id,
        decision=data.decision,
        reason=data.reason,
        reviewer=data.reviewer,
    )
    db.add(review)

    verdict.human_decision = data.decision
    verdict.human_reason = data.reason
    db.commit()

    recompute_overall_verdict(verdict.bidder_id, db)

    db.refresh(review)
    return review
