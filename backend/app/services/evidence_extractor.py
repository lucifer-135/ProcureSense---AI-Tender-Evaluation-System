from sqlalchemy.orm import Session
from ..models import (
    Bidder, BidderEvidence, Criterion, Verdict, 
    BidderStatus, VerdictValue
)
from . import llm_service

SYSTEM_PROMPT = """You are an expert document analyst for government procurement evaluation.
Your task is to analyze bidder documents against a set of eligibility criteria.

For EACH criterion provided:
1. Extract the relevant evidence (value, source page, verbatim quote).
2. Determine the verdict (Eligible, Not Eligible, or Needs Manual Review).
3. Provide a clear explanation.

Also, identify the official "bidder_name" (company name).

Return a JSON object with this structure:
{
  "bidder_name": "Official Company Name",
  "results": [
    {
      "criterion_id": 1,
      "extracted_value": "...",
      "source_page": "...",
      "verbatim_quote": "...",
      "confidence": 0.95,
      "verdict": "Eligible/Not Eligible/Needs Manual Review",
      "explanation": "...",
      "match_confidence": 0.9
    },
    ...
  ]
}

Rules for Verdicts:
- Eligible: Evidence clearly satisfies the threshold.
- Not Eligible: Evidence clearly fails the threshold.
- Needs Manual Review: Evidence is missing, ambiguous, or low-confidence."""


def extract_evidence_and_compute_verdicts(bidder_id: int, db: Session):
    """Unified process to extract evidence and compute verdicts in ONE LLM call."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        return

    bidder.status = BidderStatus.EXTRACTING
    db.commit()

    try:
        criteria = (
            db.query(Criterion)
            .filter(Criterion.tender_id == bidder.tender_id, Criterion.approved == True)
            .all()
        )

        # Combine document text
        all_doc_text = ""
        doc_names = []
        for doc in bidder.documents:
            all_doc_text += f"\n\n=== Document: {doc.filename} ===\n{doc.extracted_text}"
            doc_names.append(doc.filename)

        # Format criteria for prompt
        criteria_list = []
        for c in criteria:
            criteria_list.append({
                "id": c.id,
                "text": c.text,
                "type": c.type,
                "threshold": c.threshold,
                "is_mandatory": c.is_mandatory
            })

        prompt = (
            f"CRITERIA SET:\n{criteria_list}\n\n"
            f"BIDDER DOCUMENTS:\n{all_doc_text}"
        )

        try:
            batch_result = llm_service.generate_json(prompt, SYSTEM_PROMPT)
            
            # 1. Update bidder name
            extracted_name = batch_result.get("bidder_name")
            if extracted_name and extracted_name not in ("Unknown Bidder", "Extracting Name..."):
                bidder.name = extracted_name

            # 2. Process results
            results_map = {r["criterion_id"]: r for r in batch_result.get("results", [])}
            
            for criterion in criteria:
                res = results_map.get(criterion.id)
                if res:
                    # Save Evidence
                    evidence = BidderEvidence(
                        bidder_id=bidder.id,
                        criterion_id=criterion.id,
                        extracted_value=res.get("extracted_value", "Not Found"),
                        source_doc=", ".join(doc_names),
                        source_page=str(res.get("source_page", "")),
                        verbatim_quote=res.get("verbatim_quote", ""),
                        confidence=float(res.get("confidence", 0.0)),
                    )
                    db.add(evidence)
                    
                    # Save Verdict
                    verdict_obj = Verdict(
                        bidder_id=bidder.id,
                        criterion_id=criterion.id,
                        verdict=res.get("verdict", VerdictValue.NEEDS_REVIEW),
                        explanation=res.get("explanation", ""),
                        extraction_confidence=float(res.get("confidence", 0.0)),
                        match_confidence=float(res.get("match_confidence", 0.0)),
                    )
                    db.add(verdict_obj)
                else:
                    # Placeholder for missing results
                    evidence = BidderEvidence(bidder_id=bidder.id, criterion_id=criterion.id, extracted_value="Not Found", confidence=0.0)
                    db.add(evidence)
                    verdict_obj = Verdict(bidder_id=bidder.id, criterion_id=criterion.id, verdict=VerdictValue.NEEDS_REVIEW, explanation="Missing in AI response")
                    db.add(verdict_obj)

        except Exception as e:
            print(f"Unified extraction failed: {e}")
            # Fallback placeholder logic...
            for criterion in criteria:
                db.add(BidderEvidence(bidder_id=bidder.id, criterion_id=criterion.id, extracted_value="Error", confidence=0.0))
                db.add(Verdict(bidder_id=bidder.id, criterion_id=criterion.id, verdict=VerdictValue.NEEDS_REVIEW, explanation=str(e)))

        # Compute overall verdict (non-LLM logic)
        from .verdict_engine import _compute_overall_verdict
        db.flush()
        _compute_overall_verdict(bidder, db)

        bidder.status = BidderStatus.VERDICTS_COMPUTED
        db.commit()

    except Exception as e:
        print(f"Critical error: {e}")
        bidder.status = BidderStatus.UPLOADED
        db.commit()
        raise e
