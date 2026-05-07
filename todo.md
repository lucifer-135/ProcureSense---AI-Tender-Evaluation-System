# Prototype TODO
## AI-Based Tender Evaluation & Eligibility Analysis — Working Prototype

> **Prototype Goal:** Demonstrate the core pipeline end-to-end:
> 1. Upload one tender PDF → extract eligibility criteria → officer sees them listed
> 2. Upload one bidder's documents → extract relevant values → produce a verdict with citation
> 3. One human review step works end-to-end
> 4. A basic report comes out
>
> **Explicitly out of scope:** Robust error handling, security, role-based access, polished UI, audit log integrity guarantees, edge case coverage, performance at scale, scanned/handwritten document handling, currency conversion, deduplication, Docker/Nginx/MinIO setup.

---

## Phase 0 — Project Scaffolding

- [ ] **P0.1** Initialise the backend project (FastAPI + Python)
  - [ ] Create project directory structure: `backend/app/`, `backend/app/api/`, `backend/app/services/`, `backend/app/models/`, `backend/app/schemas/`
  - [ ] Set up `requirements.txt` with core deps: `fastapi`, `uvicorn`, `python-multipart`, `pymupdf`, `openai` (for local Ollama or OpenAI), `sqlalchemy`, `psycopg2-binary`, `celery`, `redis`, `weasyprint`, `jinja2`
  - [ ] Create a basic `main.py` with FastAPI app instance and CORS middleware
  - [ ] Verify the server starts with `uvicorn`

- [ ] **P0.2** Initialise the frontend project (React + TypeScript)
  - [ ] Scaffold with Vite: `npx -y create-vite@latest ./frontend --template react-ts`
  - [ ] Install core deps: `axios`, `react-query`, `react-dropzone`, `react-pdf`, `zustand`
  - [ ] Install shadcn/ui (follow shadcn init steps)
  - [ ] Verify the dev server starts

- [ ] **P0.3** Set up the database (PostgreSQL)
  - [ ] Create SQLAlchemy models for: `Tender`, `Criterion`, `Bidder`, `BidderEvidence`, `Verdict`, `HumanReview`
  - [ ] Write a simple `init_db.py` script to create tables
  - [ ] Verify tables are created in a local PostgreSQL instance

- [ ] **P0.4** Set up Celery + Redis (for async processing)
  - [ ] Configure Celery app with Redis as broker
  - [ ] Create one test task to verify the worker runs
  - [ ] Verify task is picked up and completed

---

## Phase 1 — Tender Ingestion & Criterion Extraction

### Backend

- [ ] **P1.1** Tender upload endpoint
  - [ ] `POST /api/tenders/upload` — accepts a single PDF file
  - [ ] Save the file to a local `uploads/` directory
  - [ ] Create a `Tender` record in DB (id, filename, upload_time, status)
  - [ ] Return the tender ID

- [ ] **P1.2** PDF text extraction
  - [ ] Use PyMuPDF to extract all text from the uploaded PDF
  - [ ] Store extracted text in the `Tender` record (or a linked `TenderText` table)
  - [ ] Handle digital/searchable PDFs only (skip OCR for prototype)

- [ ] **P1.3** Criterion extraction via LLM
  - [ ] Create a Celery task `extract_criteria`
  - [ ] Build the system prompt for the LLM (e.g., local Llama 3 via Ollama, or OpenAI) instructing it to:
    - Identify all eligibility criteria
    - Classify each as Technical / Financial / Compliance
    - Tag as Mandatory or Optional
    - Return a JSON array matching the `Criterion` schema
    - Include a confidence marker per criterion
  - [ ] Send extracted tender text + system prompt to the LLM API
  - [ ] Parse the JSON response and save each criterion to the `Criterion` table (linked to tender)
  - [ ] Update tender status to `criteria_extracted`

- [ ] **P1.4** Criterion listing endpoint
  - [ ] `GET /api/tenders/{tender_id}/criteria` — returns all extracted criteria
  - [ ] Include: id, text, type (Technical/Financial/Compliance), mandatory flag, expected value, confidence

- [ ] **P1.5** Criterion editing endpoint (minimal)
  - [ ] `PUT /api/criteria/{criterion_id}` — allow officer to edit text, type, mandatory flag
  - [ ] `DELETE /api/criteria/{criterion_id}` — allow officer to remove a criterion
  - [ ] `POST /api/tenders/{tender_id}/criteria` — allow officer to add a criterion manually
  - [ ] `POST /api/tenders/{tender_id}/approve-criteria` — officer confirms the criteria list; locks it for evaluation

### Frontend

- [ ] **P1.6** Tender upload page
  - [ ] File dropzone (react-dropzone) for a single PDF
  - [ ] Upload button → calls `POST /api/tenders/upload`
  - [ ] Show a loading/processing indicator while criteria are being extracted
  - [ ] Poll the tender status until `criteria_extracted`

- [ ] **P1.7** Criteria review page
  - [ ] Fetch and display the extracted criteria in a table
  - [ ] Columns: Criterion Text, Type, Mandatory/Optional, Confidence
  - [ ] Colour-code low-confidence criteria (yellow/orange highlight)
  - [ ] Inline edit for each criterion (text, type, mandatory toggle)
  - [ ] Delete button per criterion
  - [ ] "Add Criterion" button with a simple form
  - [ ] "Approve Criteria" button → locks criteria and proceeds to bidder upload

---

## Phase 2 — Bidder Document Ingestion & Evidence Extraction

### Backend

- [ ] **P2.1** Bidder upload endpoint
  - [ ] `POST /api/tenders/{tender_id}/bidders/upload` — accepts multiple files (PDFs) for one bidder
  - [ ] Save files to `uploads/bidders/{bidder_id}/`
  - [ ] Create a `Bidder` record (id, name, tender_id, status)
  - [ ] Return bidder ID

- [ ] **P2.2** Bidder document text extraction
  - [ ] Use PyMuPDF to extract text from each uploaded PDF
  - [ ] Store text per document in a `BidderDocument` table (bidder_id, filename, extracted_text)

- [ ] **P2.3** Criterion-targeted evidence extraction via LLM
  - [ ] Create a Celery task `extract_evidence`
  - [ ] For each criterion linked to the tender:
    - Build a targeted extraction prompt: send the criterion text + relevant bidder document text
    - Ask the LLM to find and extract the specific value/evidence that addresses this criterion
    - Ask the LLM to return: extracted value, source document name, page/section reference, verbatim quote, confidence score
  - [ ] Save each extraction result to `BidderEvidence` table (bidder_id, criterion_id, extracted_value, source_doc, source_page, verbatim_quote, confidence)
  - [ ] Update bidder status to `evidence_extracted`

- [ ] **P2.4** Evidence listing endpoint
  - [ ] `GET /api/bidders/{bidder_id}/evidence` — returns all extracted evidence for a bidder, grouped by criterion

### Frontend

- [ ] **P2.5** Bidder upload page
  - [ ] Input field for bidder name/company
  - [ ] Multi-file dropzone for PDFs
  - [ ] Upload button → calls the bidder upload endpoint
  - [ ] Show processing indicator while evidence is being extracted
  - [ ] Poll bidder status until `evidence_extracted`

---

## Phase 3 — Matching & Verdict Generation

### Backend

- [ ] **P3.1** Verdict computation engine
  - [ ] Create a Celery task `compute_verdicts`
  - [ ] For each (bidder, criterion) pair:
    - **Numeric/boolean criteria** → rule-based comparison (e.g., extracted turnover ≥ required threshold)
    - **Semantic/qualitative criteria** → send to the LLM with a matching prompt asking for Eligible / Not Eligible / Needs Manual Review + reasoning
    - Assign a match confidence score
  - [ ] Apply confidence thresholds (hardcoded defaults for prototype):
    - Extraction confidence < 0.75 → `Needs Manual Review`
    - Match confidence < 0.80 → `Needs Manual Review`
  - [ ] Save each verdict to `Verdict` table (bidder_id, criterion_id, verdict, explanation, extraction_confidence, match_confidence)

- [ ] **P3.2** Overall bidder verdict computation
  - [ ] All mandatory Eligible → overall `Eligible`
  - [ ] Any `Needs Manual Review` → overall `Needs Manual Review`
  - [ ] Any mandatory `Not Eligible` and no `Needs Manual Review` → overall `Not Eligible`
  - [ ] Save overall verdict to the `Bidder` record

- [ ] **P3.3** Verdict listing endpoint
  - [ ] `GET /api/bidders/{bidder_id}/verdicts` — returns criterion-level and overall verdicts
  - [ ] Each verdict includes: criterion text, extracted value, comparison result, verdict, explanation with citation

### Frontend

- [ ] **P3.4** Evaluation results page
  - [ ] Display a criteria × verdict matrix for the bidder
  - [ ] Colour-coded verdicts: green (Eligible), red (Not Eligible), amber (Needs Manual Review)
  - [ ] Click a verdict to expand: see the explanation, extracted value, source document, and verbatim quote
  - [ ] Show overall bidder verdict prominently at the top

---

## Phase 4 — Human Review (One Step, End-to-End)

### Backend

- [ ] **P4.1** Review queue endpoint
  - [ ] `GET /api/tenders/{tender_id}/review-queue` — returns all (bidder, criterion) pairs with verdict `Needs Manual Review`
  - [ ] Include: criterion text, extracted value, source citation, reason for flagging

- [ ] **P4.2** Submit review endpoint
  - [ ] `POST /api/verdicts/{verdict_id}/review` — accepts: decision (Eligible / Not Eligible), reason text, reviewer name
  - [ ] Save to `HumanReview` table (verdict_id, decision, reason, reviewer, timestamp)
  - [ ] Update the `Verdict` record with the human decision
  - [ ] Recompute the overall bidder verdict

### Frontend

- [ ] **P4.3** Human review page
  - [ ] List all items needing review, grouped by bidder
  - [ ] For each item show: criterion text, extracted evidence, source citation, reason it was flagged
  - [ ] Simple form to submit: Eligible / Not Eligible radio + reason text area + reviewer name input
  - [ ] Submit button → calls the review endpoint
  - [ ] Visual confirmation when a review is submitted
  - [ ] Show count of remaining items to review
  - [ ] When all reviews are done, show a "Generate Report" button

---

## Phase 5 — Basic Report Generation

### Backend

- [ ] **P5.1** Report generation endpoint
  - [ ] `POST /api/tenders/{tender_id}/report` — triggers report generation
  - [ ] Create a Jinja2 HTML template with:
    - Tender summary (filename, date, number of criteria)
    - Extracted criteria table
    - Per-bidder evaluation breakdown (criterion, extracted value, verdict, explanation)
    - Human review decisions with reviewer name and reason
  - [ ] Use WeasyPrint to convert HTML → PDF
  - [ ] Save the PDF to `outputs/` directory
  - [ ] Return the download URL

- [ ] **P5.2** Report download endpoint
  - [ ] `GET /api/tenders/{tender_id}/report/download` — serves the generated PDF file

### Frontend

- [ ] **P5.3** Report page
  - [ ] "Generate Report" button → calls the report generation endpoint
  - [ ] Loading indicator while report is being generated
  - [ ] "Download Report (PDF)" button once ready
  - [ ] Optionally: show a preview of the report content inline

---

## Phase 6 — Integration & Demo Flow

- [ ] **P6.1** End-to-end happy path test
  - [ ] Upload a sample tender PDF → verify criteria are extracted and displayed
  - [ ] Approve criteria → verify they are locked
  - [ ] Upload one bidder's PDFs → verify evidence is extracted
  - [ ] Verify verdicts are computed with explanations and citations
  - [ ] Submit a human review for a flagged item → verify overall verdict updates
  - [ ] Generate and download the report PDF → verify it contains all sections

- [ ] **P6.2** Prepare demo data
  - [ ] Create or source one sample tender PDF (can be a mock/simplified tender)
  - [ ] Create or source one set of bidder documents (mock financial statement, registration cert, etc.)
  - [ ] Pre-define expected criteria and verdicts for the demo

- [ ] **P6.3** Basic navigation / app shell
  - [ ] Simple sidebar or step-based navigation: Upload Tender → Review Criteria → Upload Bidder → View Results → Human Review → Report
  - [ ] Each step flows into the next logically
  - [ ] Minimal but clear UI — no polish needed, but it should be usable

---

## Data Models (Quick Reference)

```
Tender:        id, filename, file_path, extracted_text, status, created_at
Criterion:     id, tender_id, text, type, is_mandatory, expected_value_type, threshold, confidence, approved
Bidder:        id, tender_id, name, overall_verdict, status, created_at
BidderDocument: id, bidder_id, filename, file_path, extracted_text
BidderEvidence: id, bidder_id, criterion_id, extracted_value, source_doc, source_page, verbatim_quote, confidence
Verdict:       id, bidder_id, criterion_id, verdict, explanation, extraction_confidence, match_confidence, human_decision, human_reason
HumanReview:   id, verdict_id, decision, reason, reviewer, created_at
```

---

## Key API Endpoints (Quick Reference)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST   | `/api/tenders/upload` | Upload tender PDF |
| GET    | `/api/tenders/{id}/criteria` | List extracted criteria |
| PUT    | `/api/criteria/{id}` | Edit a criterion |
| DELETE | `/api/criteria/{id}` | Delete a criterion |
| POST   | `/api/tenders/{id}/criteria` | Add a criterion |
| POST   | `/api/tenders/{id}/approve-criteria` | Lock criteria for evaluation |
| POST   | `/api/tenders/{id}/bidders/upload` | Upload bidder docs |
| GET    | `/api/bidders/{id}/evidence` | List extracted evidence |
| GET    | `/api/bidders/{id}/verdicts` | List verdicts |
| GET    | `/api/tenders/{id}/review-queue` | Get items needing review |
| POST   | `/api/verdicts/{id}/review` | Submit a human review |
| POST   | `/api/tenders/{id}/report` | Generate report |
| GET    | `/api/tenders/{id}/report/download` | Download report PDF |

---

## Environment / Config Needed

- [ ] Local PostgreSQL instance running
- [ ] Local Redis instance running (for Celery)
- [ ] Local LLM running via Ollama (e.g., `ollama run llama3`) OR an OpenAI/Gemini API key in `.env`
- [ ] Python 3.11+
- [ ] Node.js 18+
