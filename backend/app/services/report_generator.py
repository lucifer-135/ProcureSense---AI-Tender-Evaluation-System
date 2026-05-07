import os
from datetime import datetime
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


def _render_html_to_pdf(html: str, pdf_path: str):
    from weasyprint import HTML
    
    output_dir = os.path.dirname(os.path.abspath(pdf_path))
    os.makedirs(output_dir, exist_ok=True)
    
    # WeasyPrint renders the HTML string directly to the PDF file
    HTML(string=html).write_pdf(pdf_path)


def save_report_pdf(tender_id: int, db: Session) -> str:
    """Render the HTML report template to PDF. Returns the PDF file path."""
    settings = get_settings()
    os.makedirs(settings.OUTPUT_DIR, exist_ok=True)

    html = generate_report_html(tender_id, db)
    pdf_path = os.path.join(settings.OUTPUT_DIR, f"report_tender_{tender_id}.pdf")
    _render_html_to_pdf(html, pdf_path)
    return pdf_path
