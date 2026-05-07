# Technology Stack
## AI-Based Tender Evaluation and Eligibility Analysis for Government Procurement (CRPF)

**Version:** 1.0  
**Status:** Round 1 Submission  

---

## 1. Architecture Overview

The system is structured as a four-stage pipeline with a human review layer and an audit backbone running across all stages.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STAGE 1: INGESTION                           │
│   Document Upload → Format Detection → OCR → Text Extraction        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Clean text + metadata per document
┌──────────────────────────────▼──────────────────────────────────────┐
│                    STAGE 2: UNDERSTANDING                           │
│   Tender → Criterion Extraction + Classification                    │
│   Bidder Docs → Semantic Segmentation + Value Extraction            │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Structured criteria + extracted evidence
┌──────────────────────────────▼──────────────────────────────────────┐
│                     STAGE 3: EVALUATION                             │
│   Criterion Matching → Verdict Assignment → Confidence Scoring      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ Verdicts with citations + confidence
┌──────────────────────────────▼──────────────────────────────────────┐
│                    STAGE 4: OUTPUT                                  │
│   Human Review Queue → Report Generation → PDF Export              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│            CROSS-CUTTING: AUDIT LOG (append-only, hashed)           │
└─────────────────────────────────────────────────────────────────────┘
```

Each stage is independently deployable and can fail gracefully without corrupting the outputs of previous stages. The audit log is written at every state transition, not just at the beginning and end.

---

## 2. Stage 1: Document Ingestion Pipeline

### 2.1 Format Detection and Routing

Uploaded files are classified on arrival into one of four categories and routed accordingly:

| Input Type | Detection Method | Route |
|---|---|---|
| Digital/searchable PDF | PyMuPDF text layer check | Direct text extraction |
| Scanned PDF | PyMuPDF — no text layer | OCR pipeline |
| DOCX / XLSX | python-docx / openpyxl | Structured extraction |
| Image (JPEG, PNG, TIFF) | File extension + MIME type | OCR pipeline |

**Library: PyMuPDF (fitz)** for PDF handling — fastest Python PDF library, handles both text extraction and page-to-image conversion for scanned pages.

### 2.2 OCR Pipeline

**Primary OCR Engine: Tesseract 5 (LSTM mode)**  
Reasons: Open-source, no external API call required (supports air-gap deployment), strong on printed text in English and Hindi, actively maintained, and well-supported in Python via `pytesseract`.

**Pre-processing before OCR** (using OpenCV):
- Deskew (correct page tilt using Hough line detection)
- Denoise (Gaussian blur + adaptive thresholding)
- Binarisation (Otsu's method for scanned pages with uneven lighting)
- Upscaling (bicubic interpolation if DPI < 200)
- Border removal (strip scanning artifacts)

**Fallback: Google Cloud Vision API / Azure Document Intelligence**  
For documents where Tesseract confidence falls below 0.70 (especially phone-photographed certificates, handwritten annotations, or very low-DPI scans), the system can route to a cloud OCR service. This is opt-in, controlled by the deployment configuration, and required for Round 2 sandbox use where air-gap is not mandated.

**Confidence tracking:** Tesseract outputs per-word confidence scores. These are aggregated per page and per document and recorded in the audit log. Documents with average page confidence < 0.75 are flagged before any downstream processing.

### 2.3 Table Extraction

Many tender and bidder documents contain structured tables (financial summaries, compliance matrices, specification sheets). Standard OCR or text extraction flattens these unacceptably.

**Library: Camelot** for digital PDFs (lattice and stream modes).  
**Library: img2table** for scanned/image tables — uses OpenCV to detect table borders and reconstruct cell structure before OCR.  
**Fallback:** pdfplumber for borderless tables in text PDFs.

Extracted tables are serialised as JSON arrays of rows and stored alongside the flat text, so the matching engine can query them separately.

---

## 3. Stage 2: Understanding — Criterion Extraction

### 3.1 Model Choice: Large Language Model (LLM)

**Primary Model: Claude claude-sonnet-4-20250514 (via Anthropic API)**

Reasons for this choice:
- **Long context window (200K tokens):** A single large tender document can be sent in one call, avoiding the chunking errors that cause missed cross-references.
- **Instruction-following precision:** Eligibility criteria must be extracted in a strict schema. Claude's instruction adherence is strong enough to reliably produce structured JSON without post-hoc parsing heroics.
- **Reasoning transparency:** The system prompt asks Claude to explain why it classifies a criterion as mandatory or optional — this reasoning is recorded in the audit log.
- **Safety:** Anthropic's model is a commercially available, auditable LLM — appropriate for a government-adjacent application.

**Alternative considered: GPT-4o**  
Also capable, similar context window. Claude is preferred for schema adherence and because Anthropic's API terms are more compatible with government data sensitivity requirements (data not used for training by default).

**Alternative considered: Local open-source LLM (Llama 3 70B, Mistral)**  
Viable for air-gap deployment but requires expensive GPU infrastructure. Flagged as Round 2 on-premise option if CRPF mandates no cloud API calls.

### 3.2 Criterion Extraction Prompt Design

The tender document is sent to the LLM with a structured system prompt that instructs it to:

1. Identify every eligibility criterion — not commercial terms, not technical specifications for the delivered product, but conditions a **bidder** must satisfy to be considered.
2. Classify each as Technical / Financial / Compliance.
3. Determine mandatory vs. optional from language signals ("shall", "must", "required" → mandatory; "preferred", "desirable", "if applicable" → optional).
4. Extract the verbatim text of the criterion and any numerical threshold, date range, or certification name referenced.
5. Output as a JSON array conforming to the `Criterion` schema.
6. Flag any criterion it is uncertain about with a `"confidence": "low"` marker.

The extracted criteria list is then shown to the Procurement Officer for review before any evaluation proceeds.

### 3.3 Bidder Submission Understanding

Each bidder's document set is processed through a two-phase extraction:

**Phase 1 — Document Classification:** Each file is classified by document type (financial statement, registration certificate, experience letter, technical brochure, etc.) using a zero-shot classification prompt sent to the LLM. This creates a structured manifest of what each bidder has submitted.

**Phase 2 — Criterion-Targeted Extraction:** For each criterion, the system identifies the most relevant document(s) from the manifest and sends targeted extraction prompts. Example:

> "The following is a page from a CA-certified financial statement. Extract the annual turnover for FY 2022-23 in Indian Rupees. If the value is present, return it as a number. If you cannot find it or are uncertain, say so explicitly."

This targeted approach avoids sending the entire submission for every criterion — reducing cost, latency, and hallucination risk.

**Currency and Unit Normalisation:** Extracted numeric values are normalised using a rule-based post-processor before LLM comparison. All financial values are converted to INR in lakhs. Dates are normalised to ISO-8601. This prevents the LLM from making arithmetic errors in unit conversion.

---

## 4. Stage 3: Evaluation — Matching and Verdict Assignment

### 4.1 Matching Engine Design

The matching engine is deliberately **not a pure LLM step**. It is a hybrid:

- **Rule-based comparison** for well-structured, numeric criteria (turnover ≥ X, date within last N years, boolean certificate present/absent). These are deterministic — given normalised values, the verdict is computed by code, not by the model.
- **LLM-assisted judgment** for criteria that require semantic understanding (e.g., "similar projects" — does a road construction project count as similar to a building construction project?). The LLM is asked to reason through the match and return a verdict with an explanation.

This hybrid ensures that simple, clear criteria are decided with 100% reproducibility, while only genuinely ambiguous cases invoke the more expensive (and less deterministic) LLM reasoning.

### 4.2 Confidence Scoring

Each verdict carries two confidence scores:

- **Extraction confidence:** How reliably was the value extracted from the document? (Aggregated from OCR confidence + LLM self-assessed confidence.)
- **Match confidence:** How clearly does the extracted value satisfy the criterion? (High for numeric comparisons with clean data; lower for semantic matches.)

Thresholds (configurable, defaults):
- Extraction confidence < 0.75 → verdict becomes "Needs Manual Review"
- Match confidence < 0.80 → verdict becomes "Needs Manual Review"

### 4.3 Contradiction Detection

When a bidder submits multiple documents and the system extracts different values for the same criterion from different documents (e.g., two different turnover figures from two documents), a contradiction is logged and the criterion is automatically escalated to "Needs Manual Review." Both values are presented to the reviewer, with source citations.

### 4.4 Missing Evidence Handling

If a required document type is absent from a bidder's submission:
- The criterion is flagged as "Document Not Found — Needs Manual Review."
- The bidder is not automatically marked Not Eligible — the officer may follow up or the document may have been submitted under an unexpected filename.

---

## 5. Stage 4: Output — Reporting and Export

### 5.1 Report Generation

**Library: ReportLab / WeasyPrint** for PDF generation from structured HTML templates.

The consolidated evaluation report includes:
- Cover page with tender ID, issue date, evaluation date, and officer details
- Extracted criteria table (as reviewed and approved by the officer)
- Per-bidder evaluation matrix (criteria × bidders grid with colour-coded verdicts)
- Detailed per-bidder breakdown with source citations
- Manual review decisions with reviewer attribution
- Appendix: full audit log summary

### 5.2 Citation Rendering

Every cited passage is included in the report as a block quote with:
- Document name and page number
- Verbatim extracted text (or image thumbnail for scanned documents)
- The criterion being evaluated

This allows an audit officer to independently verify every automated verdict by going back to the source document.

---

## 6. Technology Stack Summary

### 6.1 Backend

| Component | Technology | Reason |
|---|---|---|
| API framework | FastAPI (Python) | Async support, automatic OpenAPI docs, fast |
| Task queue | Celery + Redis | Long-running OCR and LLM jobs must not block the HTTP thread |
| PDF processing | PyMuPDF (fitz) | Fastest Python PDF library; text + image extraction |
| OCR | Tesseract 5 + pytesseract | Open-source, offline-capable, strong on printed text |
| OCR pre-processing | OpenCV | Standard image processing library |
| Table extraction | Camelot, img2table, pdfplumber | Coverage across digital and scanned tables |
| DOCX parsing | python-docx | Standard library for Word files |
| XLSX parsing | openpyxl | Standard library for Excel files |
| LLM — criterion extraction | Claude claude-sonnet-4-20250514 (Anthropic API) | Long context, strong schema adherence |
| LLM — semantic matching | Claude claude-sonnet-4-20250514 (Anthropic API) | Same model, consistent reasoning |
| Rule-based matching | Custom Python | Numeric and boolean criteria — deterministic |
| Unit normalisation | Custom Python | Reliable, auditable, no LLM needed |
| Report generation | WeasyPrint + Jinja2 HTML templates | Flexible, printable PDF output |
| Audit log | Append-only PostgreSQL table + SHA-256 hashing | ACID guarantees, tamper-evident |

### 6.2 Frontend

| Component | Technology | Reason |
|---|---|---|
| UI framework | React + TypeScript | Widely used, component-based, strong typing |
| UI components | shadcn/ui | Clean, accessible, government-appropriate aesthetics |
| State management | Zustand | Lightweight, sufficient for this application's complexity |
| File upload | React Dropzone | Handles large multi-file uploads gracefully |
| PDF preview | react-pdf | In-browser document preview for the review queue |
| API communication | Axios + React Query | Caching and background refetching for polling job status |

### 6.3 Infrastructure

| Component | Technology | Reason |
|---|---|---|
| Containerisation | Docker + Docker Compose | Reproducible deployments; Round 2 sandbox compatibility |
| Database | PostgreSQL | Relational model suits structured evaluation data + audit log |
| File storage | MinIO (S3-compatible) | Self-hosted; no dependency on AWS for sensitive documents |
| Secrets management | HashiCorp Vault (or .env in sandbox) | API keys, DB credentials |
| Reverse proxy | Nginx | Standard, performant |
| Monitoring | Prometheus + Grafana | Job queue depth, OCR latency, LLM call latency |
| Deployment target (Round 2) | Single-server Docker Compose | Matches sandbox constraints; no Kubernetes complexity needed |

---

## 7. Key Architectural Decisions and Rationale

### 7.1 Why a Hybrid Rule + LLM Matching Engine?

A pure LLM approach for all matching would introduce non-determinism into criteria that have objectively correct answers (e.g., "turnover ≥ ₹5 crore"). The same LLM prompt may return slightly different reasoning across runs, which is unacceptable for an auditable government process. By handling numeric and boolean criteria deterministically in code and reserving the LLM for semantic judgment, we get both reliability and flexibility.

### 7.2 Why Claude Over a Local Model?

For Round 2's sandbox context, the accuracy and instruction-following capability of Claude claude-sonnet-4-20250514 on long, complex government documents is significantly better than currently available local open-source models of feasible hardware size. A 70B parameter local model running on 2× A100s can approach this quality but at substantial infrastructure cost and with worse schema adherence. The architecture is designed so the LLM component is swappable — replacing the Anthropic API call with a local vLLM endpoint requires changing one configuration value, not the pipeline structure.

### 7.3 Why Criterion-Targeted Extraction Over Full-Document Summarisation?

Sending an entire 80-page bidder submission to the LLM and asking "does this bidder meet all criteria?" is a recipe for missed evidence and hallucinated answers. By routing each criterion to the most relevant document(s) first (via document classification), and then sending a targeted extraction prompt, we reduce context noise and improve extraction precision. It also makes each extraction independently auditable.

### 7.4 Why Confidence Thresholds Are Configurable?

Different tenders have different risk profiles. A high-value defence tender warrants a more conservative threshold (everything uncertain gets reviewed). A low-value consumables tender might allow higher automation. Making thresholds configurable per-tender lets the Procurement Officer calibrate the human review workload appropriately.

---

## 8. Risks and Trade-offs

| Risk | Severity | Mitigation |
|---|---|---|
| LLM hallucination — invented evidence | High | Criterion-targeted extraction with source citation; human review of all verdicts before finalisation; never accept LLM output that doesn't cite a specific document passage |
| Poor OCR quality on low-quality scans | High | Multi-stage pre-processing; cloud OCR fallback; automatic flagging of low-confidence pages; human review queue |
| LLM prompt injection in bidder documents | Medium | Bidder documents are never concatenated into the system prompt directly; they are sent as user-turn content with a fixed system prompt that cannot be overridden by document content |
| Criterion missed by extraction | Medium | Officer reviews extracted criteria list before evaluation; ground-truth comparison in Round 2 evaluation |
| LLM API latency / rate limits | Medium | Celery job queue with exponential backoff; parallel processing of independent bidder-criterion pairs within rate limits |
| Sensitive document data sent to cloud API | Medium | Data minimisation — only the relevant document page is sent, not the full submission; configurable to local LLM for air-gap deployment |
| Rule-based normalisation fails on unusual formats | Low | Fallback to LLM extraction for values the normaliser cannot parse; flagged in audit log |
| Non-determinism across re-runs | Low | LLM temperature set to 0 for all extraction and matching calls; rule-based components are deterministic; full inputs stored so any run can be reproduced |

---

## 9. Round 2 Implementation Plan

Assuming a sandbox is provided with representative mock tender documents and bidder submissions:

### Week 1 — Foundation
- Set up Docker Compose environment (FastAPI, Celery, Redis, PostgreSQL, MinIO)
- Implement document ingestion: format detection, PyMuPDF extraction, Tesseract OCR pipeline
- Implement audit log schema and append-only write layer

### Week 2 — Understanding Pipeline
- Implement tender criterion extraction with Claude — prompt engineering, schema definition, officer review UI
- Implement bidder document classification
- Implement criterion-targeted extraction prompts per document type

### Week 3 — Evaluation Engine
- Implement rule-based matching for numeric and boolean criteria
- Implement LLM-assisted semantic matching for experience and qualitative criteria
- Implement confidence scoring, contradiction detection, missing-document handling
- Implement overall verdict computation logic

### Week 4 — Output and Review
- Implement human review queue UI (React)
- Implement report generation (WeasyPrint + Jinja2 templates)
- Implement audit log export
- End-to-end integration testing on mock documents
- Accuracy measurement against ground-truth verdicts

### Buffer / Polish
- Threshold configuration UI for the Procurement Officer
- Edge case hardening (currency conversion, cross-reference resolution, multi-language certificates)
- Security review (input sanitisation, role-based access)
- Demo preparation

---

## 10. Open Questions for Round 2

- Will the sandbox provide ground-truth verdicts for accuracy measurement, or will evaluation be qualitative?
- Is internet access available in the sandbox (for Anthropic API), or is an air-gap local LLM required?
- What is the maximum document size and bidder count in the test scenario?
- Are any tender documents in Hindi or other languages, or is English the exclusive language?
- Is a signature/stamp verification requirement part of any criterion (e.g., "CA-certified statement" must carry a visible stamp)?
