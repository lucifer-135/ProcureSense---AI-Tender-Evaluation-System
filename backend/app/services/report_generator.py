import os
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from sqlalchemy.orm import Session
from ..models import Tender, Criterion, Bidder, Verdict, HumanReview, BidderEvidence
from ..config import get_settings


def _report_context(tender_id: int, db: Session) -> dict:
    """Collect report data once so HTML and PDF generation stay consistent."""
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    if not tender:
        raise ValueError("Tender not found")

    criteria = db.query(Criterion).filter(Criterion.tender_id == tender_id).all()
    bidders = db.query(Bidder).filter(Bidder.tender_id == tender_id).all()

    bidder_data = []
    for bidder in bidders:
        verdicts = db.query(Verdict).filter(Verdict.bidder_id == bidder.id).all()
        verdict_details = []
        for v in verdicts:
            criterion = db.query(Criterion).filter(Criterion.id == v.criterion_id).first()
            evidence = (
                db.query(BidderEvidence)
                .filter(
                    BidderEvidence.bidder_id == bidder.id,
                    BidderEvidence.criterion_id == v.criterion_id,
                )
                .first()
            )
            reviews = db.query(HumanReview).filter(HumanReview.verdict_id == v.id).all()

            verdict_details.append({
                "criterion_text": criterion.text if criterion else "",
                "criterion_type": criterion.type if criterion else "",
                "is_mandatory": criterion.is_mandatory if criterion else True,
                "verdict": v.human_decision or v.verdict,
                "original_verdict": v.verdict,
                "explanation": v.explanation,
                "extracted_value": evidence.extracted_value if evidence else "",
                "source_doc": evidence.source_doc if evidence else "",
                "source_page": evidence.source_page if evidence else "",
                "verbatim_quote": evidence.verbatim_quote if evidence else "",
                "extraction_confidence": v.extraction_confidence,
                "match_confidence": v.match_confidence,
                "reviews": [
                    {
                        "decision": r.decision,
                        "reason": r.reason,
                        "reviewer": r.reviewer,
                        "created_at": r.created_at.strftime("%Y-%m-%d %H:%M"),
                    }
                    for r in reviews
                ],
            })

        bidder_data.append({
            "name": bidder.name,
            "overall_verdict": bidder.overall_verdict,
            "verdicts": verdict_details,
        })

    return {
        "tender": tender,
        "criteria": criteria,
        "bidders": bidder_data,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }


def generate_report_html(tender_id: int, db: Session) -> str:
    """Generate an HTML report for the tender evaluation."""
    context = _report_context(tender_id, db)

    # Render template
    template_dir = os.path.join(os.path.dirname(__file__), "..", "..", "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")

    html = template.render(**context)

    return html


def _find_browser_executable() -> str | None:
    candidates = [
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("chromium"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate

    return None


def _render_html_to_pdf(html: str, pdf_path: str):
    browser = _find_browser_executable()
    if not browser:
        raise RuntimeError("No Chromium-based browser found for HTML-to-PDF rendering.")

    output_dir = os.path.dirname(os.path.abspath(pdf_path))
    os.makedirs(output_dir, exist_ok=True)

    tmp_dir = os.path.join(output_dir, f"report_render_{uuid.uuid4().hex}")
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        html_path = os.path.join(tmp_dir, "report.html")
        temp_pdf_path = os.path.join(tmp_dir, "report.pdf")
        user_data_dir = os.path.join(tmp_dir, "browser-profile")

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html)

        command = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--disable-extensions",
            f"--user-data-dir={user_data_dir}",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={temp_pdf_path}",
            Path(html_path).as_uri(),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        if result.returncode != 0 or not os.path.exists(temp_pdf_path):
            details = (result.stderr or result.stdout or "Browser PDF rendering failed.").strip()
            raise RuntimeError(details)

        os.replace(temp_pdf_path, pdf_path)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def save_report_pdf(tender_id: int, db: Session) -> str:
    """Render the HTML report template to PDF. Returns the PDF file path."""
    settings = get_settings()
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    html = generate_report_html(tender_id, db)
    pdf_path = os.path.join(settings.OUTPUT_DIR, f"report_tender_{tender_id}.pdf")
    _render_html_to_pdf(html, pdf_path)
    return pdf_path
