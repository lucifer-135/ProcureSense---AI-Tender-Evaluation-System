import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.report_generator import save_report_pdf

router = APIRouter(prefix="/api/tenders", tags=["reports"])


@router.post("/{tender_id}/report")
def generate_report(tender_id: int, db: Session = Depends(get_db)):
    try:
        path = save_report_pdf(tender_id, db)
        filename = os.path.basename(path)
        return {"status": "generated", "filename": filename, "path": path}
    except Exception as e:
        raise HTTPException(500, f"Report generation failed: {str(e)}")


@router.get("/{tender_id}/report/download")
def download_report(tender_id: int):
    from ..config import get_settings
    settings = get_settings()

    path = os.path.join(settings.OUTPUT_DIR, f"report_tender_{tender_id}.pdf")
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))

    raise HTTPException(404, "PDF report not found. Generate it first.")
