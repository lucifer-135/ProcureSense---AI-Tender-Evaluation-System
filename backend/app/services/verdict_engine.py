from sqlalchemy.orm import Session
from ..models import (
    Bidder, BidderEvidence, Criterion, Verdict,
    BidderStatus, VerdictValue
)
from . import llm_service

MATCHING_PROMPT = """You are evaluating whether a bidder meets a specific eligibility criterion.

Given:
- The criterion text and its threshold/requirement
- The extracted evidence from the bidder's submission

Determine the verdict and provide reasoning.

Return a JSON object with:
- "verdict": One of "Eligible", "Not Eligible", or "Needs Manual Review"
- "explanation": A clear explanation citing the evidence and criterion
- "match_confidence": A float 0.0-1.0 indicating confidence in this verdict

Rules:
- If the evidence clearly satisfies the criterion → "Eligible"
- If the evidence clearly fails the criterion → "Not Eligible"
- If the evidence is ambiguous, partially available, or uncertain → "Needs Manual Review"
- Always explain your reasoning with specific values"""


EXTRACTION_CONFIDENCE_THRESHOLD = 0.75
MATCH_CONFIDENCE_THRESHOLD = 0.80


def compute_verdicts_for_bidder(bidder_id: int, db: Session):
    """Compute verdicts for all criteria for a given bidder."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        return

    bidder.status = BidderStatus.COMPUTING
    db.commit()

    try:
        evidence_list = (
            db.query(BidderEvidence)
            .filter(BidderEvidence.bidder_id == bidder.id)
            .all()
        )

        for ev in evidence_list:
            criterion = db.query(Criterion).filter(Criterion.id == ev.criterion_id).first()
            if not criterion:
                continue

            # Low extraction confidence → auto-flag
            if ev.confidence < EXTRACTION_CONFIDENCE_THRESHOLD:
                verdict_obj = Verdict(
                    bidder_id=bidder.id,
                    criterion_id=criterion.id,
                    verdict=VerdictValue.NEEDS_REVIEW,
                    explanation=f"Extraction confidence ({ev.confidence:.2f}) is below threshold ({EXTRACTION_CONFIDENCE_THRESHOLD}). Manual review required.",
                    extraction_confidence=ev.confidence,
                    match_confidence=0.0,
                )
                db.add(verdict_obj)
                continue

            # Not Found → flag
            if ev.extracted_value in ("Not Found", "Extraction Failed", ""):
                verdict_obj = Verdict(
                    bidder_id=bidder.id,
                    criterion_id=criterion.id,
                    verdict=VerdictValue.NEEDS_REVIEW,
                    explanation="Evidence not found in bidder's documents. Document may be missing or evidence not clearly stated.",
                    extraction_confidence=ev.confidence,
                    match_confidence=0.0,
                )
                db.add(verdict_obj)
                continue

            # Use LLM for matching
            prompt = (
                f"CRITERION: {criterion.text}\n"
                f"Type: {criterion.type}\n"
                f"Required threshold: {criterion.threshold}\n"
                f"Mandatory: {criterion.is_mandatory}\n\n"
                f"EXTRACTED EVIDENCE:\n"
                f"Value: {ev.extracted_value}\n"
                f"Source: {ev.source_doc}, page {ev.source_page}\n"
                f"Quote: \"{ev.verbatim_quote}\"\n"
            )

            try:
                result = llm_service.generate_json(prompt, MATCHING_PROMPT)
                match_conf = float(result.get("match_confidence", 0.5))

                verdict_val = result.get("verdict", VerdictValue.NEEDS_REVIEW)
                if match_conf < MATCH_CONFIDENCE_THRESHOLD:
                    verdict_val = VerdictValue.NEEDS_REVIEW

                verdict_obj = Verdict(
                    bidder_id=bidder.id,
                    criterion_id=criterion.id,
                    verdict=verdict_val,
                    explanation=result.get("explanation", ""),
                    extraction_confidence=ev.confidence,
                    match_confidence=match_conf,
                )
            except Exception:
                verdict_obj = Verdict(
                    bidder_id=bidder.id,
                    criterion_id=criterion.id,
                    verdict=VerdictValue.NEEDS_REVIEW,
                    explanation="Automated matching failed. Manual review required.",
                    extraction_confidence=ev.confidence,
                    match_confidence=0.0,
                )

            db.add(verdict_obj)

        # Compute overall verdict
        db.flush()
        _compute_overall_verdict(bidder, db)

        bidder.status = BidderStatus.VERDICTS_COMPUTED
        db.commit()

    except Exception as e:
        bidder.status = BidderStatus.EVIDENCE_EXTRACTED
        db.commit()
        raise e


def _compute_overall_verdict(bidder: Bidder, db: Session):
    """
    Overall verdict logic:
    - Any 'Needs Manual Review' → overall 'Needs Manual Review'
    - Any mandatory 'Not Eligible' (and no review needed) → 'Not Eligible'
    - All mandatory 'Eligible' → 'Eligible'
    """
    verdicts = db.query(Verdict).filter(Verdict.bidder_id == bidder.id).all()

    has_needs_review = False
    has_not_eligible_mandatory = False

    for v in verdicts:
        effective = v.human_decision if v.human_decision else v.verdict
        criterion = db.query(Criterion).filter(Criterion.id == v.criterion_id).first()

        if effective == VerdictValue.NEEDS_REVIEW:
            has_needs_review = True
        elif effective == VerdictValue.NOT_ELIGIBLE and criterion and criterion.is_mandatory:
            has_not_eligible_mandatory = True

    if has_needs_review:
        bidder.overall_verdict = VerdictValue.NEEDS_REVIEW
    elif has_not_eligible_mandatory:
        bidder.overall_verdict = VerdictValue.NOT_ELIGIBLE
    else:
        bidder.overall_verdict = VerdictValue.ELIGIBLE


def recompute_overall_verdict(bidder_id: int, db: Session):
    """Recompute after a human review is submitted."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if bidder:
        _compute_overall_verdict(bidder, db)
        db.commit()
