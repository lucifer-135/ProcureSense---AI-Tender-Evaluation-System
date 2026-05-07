import os
import shutil
import threading
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from ..models import Tender, Criterion, TenderStatus
from ..schemas import (
    TenderResponse, CriterionCreate, CriterionUpdate, CriterionResponse,
)
from ..services.pdf_extractor import extract_text_from_pdf
from ..services.criteria_extractor import extract_criteria_for_tender
from ..config import get_settings
from typing import List

router = APIRouter(prefix="/api/tenders", tags=["tenders"])


def _run_extraction(tender_id: int):
    db = SessionLocal()
    try:
        extract_criteria_for_tender(tender_id, db)
    finally:
        db.close()


@router.post("/upload", response_model=TenderResponse)
async def upload_tender(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    extracted_text = extract_text_from_pdf(file_path)

    tender = Tender(
        filename=file.filename,
        file_path=file_path,
        extracted_text=extracted_text,
        status=TenderStatus.UPLOADED,
    )
    db.add(tender)
    db.commit()
    db.refresh(tender)

    # Start criteria extraction in background
    thread = threading.Thread(target=_run_extraction, args=(tender.id,), daemon=True)
    thread.start()

    return tender


@router.get("/", response_model=List[TenderResponse])
def list_tenders(db: Session = Depends(get_db)):
    return db.query(Tender).order_by(Tender.created_at.desc()).all()


@router.get("/{tender_id}", response_model=TenderResponse)
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")
    return tender


def _remove_path_if_safe(path: str, allowed_roots: list[str]):
    if not path:
        return

    abs_path = os.path.abspath(path)
    abs_roots = [os.path.abspath(root) for root in allowed_roots]
    if not any(os.path.commonpath([abs_path, root]) == root for root in abs_roots):
        return

    if os.path.isdir(abs_path):
        shutil.rmtree(abs_path, ignore_errors=True)
    elif os.path.exists(abs_path):
        os.remove(abs_path)


@router.delete("/{tender_id}", status_code=204)
def delete_tender(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")

    settings = get_settings()
    upload_root = settings.UPLOAD_DIR
    output_root = settings.OUTPUT_DIR

    paths_to_remove = {tender.file_path}
    for bidder in tender.bidders:
        for document in bidder.documents:
            paths_to_remove.add(document.file_path)
            paths_to_remove.add(os.path.dirname(document.file_path))

    paths_to_remove.update({
        os.path.join(output_root, f"report_tender_{tender_id}.html"),
        os.path.join(output_root, f"report_tender_{tender_id}.pdf"),
    })

    db.delete(tender)
    db.commit()

    for path in paths_to_remove:
        _remove_path_if_safe(path, [upload_root, output_root])


@router.get("/{tender_id}/criteria", response_model=List[CriterionResponse])
def list_criteria(tender_id: int, db: Session = Depends(get_db)):
    return db.query(Criterion).filter(Criterion.tender_id == tender_id).all()


@router.post("/{tender_id}/criteria", response_model=CriterionResponse)
def add_criterion(tender_id: int, data: CriterionCreate, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")
    criterion = Criterion(tender_id=tender_id, **data.model_dump())
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.put("/criteria/{criterion_id}", response_model=CriterionResponse)
def update_criterion(criterion_id: int, data: CriterionUpdate, db: Session = Depends(get_db)):
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(404, "Criterion not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(criterion, key, value)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.delete("/criteria/{criterion_id}", status_code=204)
def delete_criterion(criterion_id: int, db: Session = Depends(get_db)):
    criterion = db.query(Criterion).filter(Criterion.id == criterion_id).first()
    if not criterion:
        raise HTTPException(404, "Criterion not found")
    db.delete(criterion)
    db.commit()


@router.post("/{tender_id}/approve-criteria", response_model=TenderResponse)
def approve_criteria(tender_id: int, db: Session = Depends(get_db)):
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise HTTPException(404, "Tender not found")
    db.query(Criterion).filter(Criterion.tender_id == tender_id).update({"approved": True})
    tender.status = TenderStatus.APPROVED
    db.commit()
    db.refresh(tender)
    return tender
