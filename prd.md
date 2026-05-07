# Product Requirements Document
## AI-Based Tender Evaluation and Eligibility Analysis for Government Procurement (CRPF)

**Version:** 1.0  
**Status:** Round 1 Submission  
**Domain:** GovTech / Procurement Automation  

---

## 1. Problem Understanding

### 1.1 The Reality of Government Procurement

Government procurement in India — especially for security and paramilitary organisations like CRPF — is governed by a dense web of rules: GFR 2017, CVC guidelines, Defence Procurement Procedures, and organisation-specific SOPs. Tenders are written by legal and administrative officers, not software engineers. The language is formal, often archaic, and deliberately careful. A single eligibility clause might span three sub-clauses, carry cross-references to annexures, and be qualified by exceptions buried in footnotes.

Bidder submissions are equally heterogeneous. A single bidder might submit 40–80 pages: a company profile (Word doc), CA-certified financial statements (scanned PDF), GST registration (JPEG of a physical printout), experience certificates on client letterhead (photographed with a phone), and technical compliance matrices (structured Excel tables). The same underlying fact — say, a turnover figure — might appear in three of these documents with minor variations in number due to rounding, currency formatting, or reporting period.

The current evaluation process is a committee of officers working through printed copies, cross-checking each document against a printed eligibility checklist. The problems are structural:

- **Speed:** A 10-bidder tender can take 3–5 days of committee time.
- **Inconsistency:** Two officers may interpret the same ambiguous clause differently.
- **Oversight risk:** With hundreds of pages per bidder, a missed document is easy.
- **Auditability:** Handwritten notes on printed sheets are difficult to digitise, archive, or challenge.
- **No escalation logic:** There is no systematic mechanism to distinguish "clearly ineligible" from "borderline — needs judgment."

This platform addresses all five problems.

### 1.2 Scope of Round 1

Round 1 is a written solution submission. No real tender or bid data will be used. The PRD defines what the system must do, how it should behave under edge cases, what constitutes a correct output, and how success is measured — so that a Round 2 implementation has a precise target to build toward.

---

## 2. Goals and Non-Goals

### 2.1 Goals

- Automatically extract structured eligibility criteria from any tender document uploaded in PDF, DOCX, or image format.
- Parse heterogeneous bidder submission packages (typed PDFs, scanned copies, Word files, photos) and extract values relevant to each criterion.
- Match extracted bidder evidence against each criterion and produce one of three verdicts: **Eligible**, **Not Eligible**, or **Needs Manual Review**.
- Provide a criterion-level explanation for every verdict, citing the source document, the extracted value, and the rule applied.
- Never silently disqualify a bidder — all uncertain cases must be surfaced with the reason for uncertainty.
- Produce a consolidated, exportable evaluation report suitable for formal government use, with a complete audit trail.

### 2.2 Non-Goals (Round 1 / Round 2 Scope Boundary)

- The system does **not** make the final procurement decision — it supports the human officer who does.
- The system does **not** evaluate the quality or technical merit of bids — only eligibility against stated criteria.
- The system does **not** handle tender drafting or publishing workflows.
- The system does **not** integrate with e-procurement portals (GeM, CPPP) in Round 2 — mock sandbox only.
- The system does **not** provide legal advice or interpret criteria that are genuinely legally ambiguous — these are escalated to human review.

---

## 3. Users and Personas

### 3.1 Procurement Officer (Primary User)
A CRPF administrative officer responsible for issuing tenders and managing the evaluation process. Comfortable with standard government digital tools but not a technical user. Needs to upload documents, review AI outputs, override verdicts where needed, and export a signed report.

**Key needs:** Trust in outputs, full visibility into reasoning, ability to override, clean export.

### 3.2 Evaluation Committee Member
A subject-matter expert (technical, financial, or legal) who reviews flagged "Needs Manual Review" cases and provides a human verdict. May only see the cases assigned to them, not the full system.

**Key needs:** Clear framing of what is ambiguous, the specific document passage in question, and a simple interface to record their decision.

### 3.3 Audit Officer / CVC Inspector
Reviews the evaluation record after the fact to verify that the process was fair and compliant. Does not interact with the live system — consumes the audit log and final report.

**Key needs:** Immutable, timestamped record of every automated decision, every human override, and every input document.

---

## 4. Functional Requirements

### 4.1 Tender Ingestion and Criterion Extraction

**FR-01:** The system must accept tender documents in PDF, DOCX, and image formats (JPEG, PNG, TIFF).

**FR-02:** The system must extract all eligibility criteria from the tender document automatically, without requiring manual annotation.

**FR-03:** Each extracted criterion must be classified into one of three types:
- **Technical** — specifications, capabilities, certifications, past experience
- **Financial** — turnover thresholds, net worth, bid security amounts
- **Compliance** — legal registrations, tax filings, blacklisting declarations

**FR-04:** Each criterion must be tagged as **Mandatory** or **Optional**, derived from the language of the tender (e.g., "shall," "must," "required" → mandatory; "preferred," "desirable," "wherever applicable" → optional).

**FR-05:** The system must present the extracted criteria list to the Procurement Officer for review and correction before evaluation begins. The officer must be able to add, edit, or remove a criterion, and mark any criterion as mandatory or optional.

**FR-06:** Each criterion must be stored in a structured, machine-readable form that includes: criterion ID, text (verbatim from tender), type, mandatory flag, expected value type (boolean, numeric, date range, text match), and threshold or target value where applicable.

**FR-07:** The system must flag criteria it could not parse with confidence and present them for manual specification by the officer.

### 4.2 Bidder Submission Ingestion and Parsing

**FR-08:** The system must accept bidder submission packages as a folder or ZIP archive containing any mix of PDF, DOCX, XLSX, JPEG, PNG, and TIFF files.

**FR-09:** The system must apply OCR to all scanned and image-format documents before processing. OCR must handle printed text, typed text, and handwritten annotations (best-effort for handwriting).

**FR-10:** Parsed text must be segmented by document and by logical section (headers, tables, running text, footers, stamps, signatures).

**FR-11:** For each criterion, the system must locate the most relevant passage or value in the bidder's submission, extract it, and record the source: document name, page number, section heading, and the verbatim text or value extracted.

**FR-12:** The system must handle variation in how bidders present the same information — e.g., turnover stated as "₹ 5,23,45,000," "INR 52.345 million," or "Rs. 5.23 Cr" must all be normalised to a common unit before comparison.

**FR-13:** The system must correlate information across documents when a single criterion may be evidenced by multiple files (e.g., GST registration corroborated by both a registration certificate and a GST return).

**FR-14:** If a required document type appears to be missing from a submission, the system must flag it as "Document Not Found" rather than marking the criterion as failed.

### 4.3 Matching and Verdict Generation

**FR-15:** For each (bidder, criterion) pair, the system must assign one of three verdicts:
- **Eligible:** The extracted evidence clearly satisfies the criterion.
- **Not Eligible:** The extracted evidence clearly fails the criterion.
- **Needs Manual Review:** The evidence is ambiguous, partially available, low-confidence, or the criterion itself is subject to interpretation.

**FR-16:** No bidder shall be assigned a "Not Eligible" overall verdict if any criterion-level verdict is "Needs Manual Review" — the overall verdict in that case must also be "Needs Manual Review."

**FR-17:** The overall verdict for a bidder is:
- **Eligible:** All mandatory criteria are Eligible.
- **Not Eligible:** At least one mandatory criterion is Not Eligible, and no criterion is Needs Manual Review.
- **Needs Manual Review:** Any criterion is Needs Manual Review.

**FR-18:** Every verdict must include a structured explanation with: criterion text, extracted value, comparison result, and a plain-English reason for the verdict.

**FR-19:** Confidence scores must be attached to every extraction (document parsing step) and every match (criterion evaluation step). Low-confidence extractions must automatically trigger "Needs Manual Review."

**FR-20:** The system must define configurable confidence thresholds (default: extraction confidence < 0.75 → flag; match confidence < 0.80 → flag). The Procurement Officer must be able to adjust these thresholds.

### 4.4 Human Review Workflow

**FR-21:** All "Needs Manual Review" cases must be presented in a dedicated review queue, grouped by criterion type, with the ambiguous passage highlighted and the reason for flagging stated.

**FR-22:** An evaluation committee member must be able to record: Eligible, Not Eligible, or Defer, with a mandatory free-text reason.

**FR-23:** Human review decisions must be recorded with the reviewer's identity, timestamp, and the reason. These become part of the audit trail.

**FR-24:** After all manual reviews are complete, the system must recompute overall bidder verdicts incorporating the human decisions.

### 4.5 Reporting and Export

**FR-25:** The system must generate a **Consolidated Evaluation Report** containing:
- Tender summary and extracted criteria list
- Per-bidder summary: overall verdict, criteria-by-criteria breakdown, and evidence references
- List of all manual review decisions with reviewer attribution
- Flagged cases and their resolution

**FR-26:** The report must be exportable as a structured PDF, formatted for formal government use (letter-head compatible, page-numbered, dated, with a signature block).

**FR-27:** The system must maintain a complete, immutable **Audit Log** recording every input document, every extraction, every match decision, every confidence score, every human override, and every export event — with timestamps.

**FR-28:** The audit log must be exportable as a structured JSON file, readable independently of the platform.

---

## 5. Non-Functional Requirements

### 5.1 Accuracy
- Criterion extraction from well-formatted tender documents: ≥ 90% recall of ground-truth criteria.
- OCR on clean scanned documents: ≥ 95% character accuracy.
- Overall evaluation accuracy (Eligible / Not Eligible verdicts on unambiguous cases): ≥ 92%.

### 5.2 Explainability
Every automated verdict must be traceable to a specific sentence or value in a specific document. "Black box" verdicts are not acceptable.

### 5.3 Auditability
The audit log must be append-only. No record may be deleted or modified after creation. Every record must carry a cryptographic hash of its content to detect tampering.

### 5.4 Performance
- Tender criterion extraction: ≤ 3 minutes for a 100-page document.
- Bidder submission processing: ≤ 5 minutes per bidder for a 50-page submission package.
- Full evaluation of 10 bidders: ≤ 60 minutes end-to-end.

### 5.5 Security
- All uploaded documents must be stored encrypted at rest.
- Access must be role-based: Procurement Officer, Committee Member, Audit Officer.
- No document data may leave the designated processing environment (air-gap compatible deployment option required for Round 2).

### 5.6 Reliability
- The system must not lose any uploaded document or evaluation record under any failure condition.
- All processing must be idempotent — re-running the same inputs must produce the same outputs.

---

## 6. Edge Cases and Handling

| Edge Case | Expected Behaviour |
|---|---|
| Scanned document with poor image quality | OCR attempted; if confidence < threshold, document flagged for manual review with the specific page cited |
| Criterion stated in indirect or cross-referencing language (e.g., "as per Annexure III") | System resolves internal cross-references; if unresolvable, criterion flagged for manual specification |
| Bidder presents turnover in a foreign currency | System converts using RBI reference rate for the date of the financial document; conversion noted in explanation |
| Same document submitted by bidder twice under different filenames | Deduplication applied; one copy retained, flagged in audit log |
| A criterion is mandatory but no bidder has submitted evidence for it | All bidders flagged for that criterion under "Document Not Found" |
| Contradictory values across two documents from the same bidder | Both values extracted; criterion flagged as "Needs Manual Review" with both values shown |
| Handwritten financial figures on a certificate | OCR attempted; if not parseable, flagged as "Needs Manual Review" with the page image attached |
| Optional criterion with no evidence | Recorded as "Not Submitted — Optional" with no verdict impact |
| Tender criterion is a date range (e.g., "within last 5 years") | System uses the tender issue date as the reference date; all date comparisons anchored to it |
| Bidder submission is partially corrupted or unreadable | Readable portion processed; unreadable files flagged individually; bidder not disqualified on that basis alone |

---

## 7. Human-in-the-Loop Design

The system is designed so that human judgment is preserved at every critical decision point. Automation accelerates and standardises — it does not replace the officer.

**Before evaluation:** The officer reviews and approves the extracted criteria list. No evaluation runs without this sign-off.

**During evaluation:** Low-confidence extractions and ambiguous matches are automatically escalated, never resolved by the model alone.

**After evaluation:** The officer reviews the full report before it is finalised. Any verdict can be overridden, with a mandatory reason.

**At export:** The final report is explicitly marked as "AI-assisted, human-reviewed and approved by [Officer Name, Date, Designation]" — not "AI-generated."

The principle is: the AI is a reliable assistant that surfaces all evidence and flags all uncertainty. The human is the decision-maker who signs off.

---

## 8. Audit Trail Specification

Every event in the system is recorded as an immutable log entry with the following structure:

```
{
  "event_id": "uuid",
  "timestamp": "ISO-8601",
  "event_type": "DOCUMENT_UPLOADED | CRITERION_EXTRACTED | VERDICT_ASSIGNED | HUMAN_REVIEW | OVERRIDE | REPORT_EXPORTED",
  "actor": "system | user_id",
  "tender_id": "...",
  "bidder_id": "...",
  "criterion_id": "...",
  "details": { ... event-specific payload ... },
  "content_hash": "sha256 of details payload"
}
```

The audit log is append-only and exportable. It constitutes the complete decision record for CVC or RTI purposes.

---

## 9. Success Metrics

| Metric | Target |
|---|---|
| % of criteria correctly extracted (vs. ground truth) | ≥ 90% |
| % of unambiguous verdicts correctly assigned | ≥ 92% |
| % of ambiguous cases correctly escalated (not silently decided) | 100% |
| Time to process a 10-bidder tender end-to-end | ≤ 60 minutes |
| Officer trust score (post-pilot survey) | ≥ 4/5 |
| Audit log completeness (% of decisions traceable) | 100% |

---

## 10. Out of Scope for Round 2 (Future Roadmap)

- Integration with GeM / CPPP e-procurement portals
- Automated scoring and ranking of technically-qualified bidders
- Support for multi-stage tenders (EOI → RFP → L1 selection)
- Vernacular language tender support (Hindi, regional languages)
- Real-time collaboration between multiple committee members
