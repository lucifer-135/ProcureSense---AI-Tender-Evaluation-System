from sqlalchemy.orm import Session
from ..models import Tender, Criterion, TenderStatus
from . import llm_service

SYSTEM_PROMPT = """You are an expert government procurement analyst. Your task is to extract ALL eligibility criteria from the provided tender document text.

For each criterion, return a JSON array of objects with these exact fields:
- "text": The verbatim criterion text from the tender document
- "type": One of "Technical", "Financial", or "Compliance"
- "is_mandatory": true if the language uses "shall", "must", "required", "mandatory"; false if "preferred", "desirable", "optional", "if applicable"
- "expected_value_type": One of "boolean", "numeric", "date", "text"
- "threshold": The target value or threshold if specified (e.g., ">=5 Crore", "within last 5 years"), or empty string if none
- "confidence": A float 0.0-1.0 indicating how confident you are in this extraction

Rules:
- Extract ONLY eligibility criteria — conditions a BIDDER must satisfy to qualify
- Do NOT extract commercial terms, delivery schedules, or product specifications
- Include ALL criteria, even if they seem redundant
- If a criterion is ambiguous, still extract it but set confidence lower
- Return ONLY the JSON array, no other text"""


def extract_criteria_for_tender(tender_id: int, db: Session):
    """Extract eligibility criteria from a tender's text using the LLM."""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        return

    tender.status = TenderStatus.EXTRACTING
    db.commit()

    try:
        prompt = f"Extract all eligibility criteria from this tender document:\n\n{tender.extracted_text}"
        results = llm_service.generate_json(prompt, SYSTEM_PROMPT)

        if not isinstance(results, list):
            results = [results]

        for item in results:
            criterion = Criterion(
                tender_id=tender.id,
                text=item.get("text", ""),
                type=item.get("type", "Technical"),
                is_mandatory=item.get("is_mandatory", True),
                expected_value_type=item.get("expected_value_type", "text"),
                threshold=item.get("threshold", ""),
                confidence=float(item.get("confidence", 0.8)),
                approved=False,
            )
            db.add(criterion)

        tender.status = TenderStatus.CRITERIA_EXTRACTED
        db.commit()

    except Exception as e:
        tender.status = TenderStatus.UPLOADED
        db.commit()
        raise e
