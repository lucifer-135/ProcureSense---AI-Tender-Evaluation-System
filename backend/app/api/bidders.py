import os
import shutil
import threading
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db, SessionLocal
from ..models import Bidder, BidderDocument, BidderStatus
from ..schemas import BidderResponse, EvidenceWithCriterion
from ..services.pdf_extractor import extract_text_from_pdf
from ..services.evidence_extractor import extract_evidence_and_compute_verdicts
from ..config import get_settings

router = APIRouter(prefix="/api", tags=["bidders"])


def _run_evidence_and_verdicts(bidder_id: int):
    db = SessionLocal()
    try:
        extract_evidence_and_compute_verdicts(bidder_id, db)
    finally:
        db.close()


@router.post("/tenders/{tender_id}/bidders/upload", response_model=BidderResponse)
async def upload_bidder(
    tender_id: int,
    name: str = Form(default="Extracting Name..."),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    bidder = Bidder(tender_id=tender_id, name=name, status=BidderStatus.UPLOADED)
    db.add(bidder)
    db.commit()
    db.refresh(bidder)

    upload_dir = os.path.join(settings.UPLOAD_DIR, "bidders", str(bidder.id))
    os.makedirs(upload_dir, exist_ok=True)

    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        extracted_text = extract_text_from_pdf(file_path)
        doc = BidderDocument(
            bidder_id=bidder.id,
            filename=file.filename,
            file_path=file_path,
            extracted_text=extracted_text,
        )
        db.add(doc)

    db.commit()

    # Run evidence extraction + verdict computation in background
    thread = threading.Thread(
        target=_run_evidence_and_verdicts, args=(bidder.id,), daemon=True
    )
    thread.start()

    db.refresh(bidder)
    return bidder


@router.get("/tenders/{tender_id}/bidders", response_model=List[BidderResponse])
def list_bidders(tender_id: int, db: Session = Depends(get_db)):
    return db.query(Bidder).filter(Bidder.tender_id == tender_id).all()


@router.get("/bidders/{bidder_id}", response_model=BidderResponse)
def get_bidder(bidder_id: int, db: Session = Depends(get_db)):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(404, "Bidder not found")
    return bidder


def _remove_path_if_safe(path: str, allowed_root: str):
    if not path:
        return

    abs_path = os.path.abspath(path)
    abs_root = os.path.abspath(allowed_root)
    if os.path.commonpath([abs_path, abs_root]) != abs_root:
        return

    if os.path.isdir(abs_path):
        shutil.rmtree(abs_path, ignore_errors=True)
    elif os.path.exists(abs_path):
        os.remove(abs_path)


@router.delete("/bidders/{bidder_id}", status_code=204)
def delete_bidder(bidder_id: int, db: Session = Depends(get_db)):
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    if not bidder:
        raise HTTPException(404, "Bidder not found")

    settings = get_settings()
    paths_to_remove = set()
    for document in bidder.documents:
        paths_to_remove.add(document.file_path)
        paths_to_remove.add(os.path.dirname(document.file_path))

    db.delete(bidder)
    db.commit()

    for path in paths_to_remove:
        _remove_path_if_safe(path, settings.UPLOAD_DIR)


@router.get("/bidders/{bidder_id}/evidence", response_model=List[EvidenceWithCriterion])
def list_evidence(bidder_id: int, db: Session = Depends(get_db)):
    from ..models import BidderEvidence, Criterion
    results = (
        db.query(BidderEvidence, Criterion)
        .join(Criterion, BidderEvidence.criterion_id == Criterion.id)
        .filter(BidderEvidence.bidder_id == bidder_id)
        .all()
    )
    output = []
    for ev, crit in results:
        output.append(EvidenceWithCriterion(
            id=ev.id,
            bidder_id=ev.bidder_id,
            criterion_id=ev.criterion_id,
            extracted_value=ev.extracted_value,
            source_doc=ev.source_doc,
            source_page=ev.source_page,
            verbatim_quote=ev.verbatim_quote,
            confidence=ev.confidence,
            criterion_text=crit.text,
            criterion_type=crit.type,
        ))
    return output
