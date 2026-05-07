from sqlalchemy.orm import Session
from ..models import Bidder, BidderStatus
from . import llm_service

SYSTEM_PROMPT = """You are an expert document analyst for government procurement.
Your task is to identify the official name of the Bidder (the company or entity submitting the proposal) from the provided document text.

Look for:
- Cover pages
- Letterheads
- "Name of the Bidder" fields
- Signature blocks

Return a JSON object with this exact field:
- "bidder_name": The official full name of the company/entity.

If you cannot find a clear name, return "Unknown Bidder"."""

def extract_bidder_name(bidder_id: int, db: Session):
    """Extract the bidder's name from their documents using AI."""
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        return

    bidder.status = BidderStatus.EXTRACTING_NAME
    db.commit()

    try:
        # Use first 5000 characters of the first document as it's most likely to contain the name
        text_sample = ""
        if bidder.documents:
            # Sort by filename or just take the first one
            first_doc = bidder.documents[0]
            text_sample = first_doc.extracted_text[:5000]

        if not text_sample:
            bidder.name = "Unknown Bidder"
            bidder.status = BidderStatus.UPLOADED
            db.commit()
            return

        prompt = f"EXTRACT BIDDER NAME FROM THIS TEXT:\n\n{text_sample}"
        result = llm_service.generate_json(prompt, SYSTEM_PROMPT)
        
        extracted_name = result.get("bidder_name", "Unknown Bidder")
        if extracted_name == "Unknown Bidder" and len(bidder.documents) > 1:
             # Try second document if first one failed
             second_doc = bidder.documents[1]
             text_sample = second_doc.extracted_text[:5000]
             prompt = f"EXTRACT BIDDER NAME FROM THIS TEXT:\n\n{text_sample}"
             result = llm_service.generate_json(prompt, SYSTEM_PROMPT)
             extracted_name = result.get("bidder_name", "Unknown Bidder")

        # Fallback to filename if still unknown
        if extracted_name == "Unknown Bidder" and bidder.documents:
            extracted_name = bidder.documents[0].filename.replace(".pdf", "").replace(".PDF", "").replace("_", " ").title()

        bidder.name = extracted_name
        db.commit()

    except Exception as e:
        print(f"Error extracting bidder name: {e}")
        # Fallback to filename on error
        if bidder.documents:
            bidder.name = bidder.documents[0].filename.replace(".pdf", "").replace(".PDF", "").replace("_", " ").title()
        else:
            bidder.name = "Unknown Bidder (Error)"
        db.commit()
