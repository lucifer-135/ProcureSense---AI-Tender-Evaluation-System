# ProcureSense — AI-Powered Tender Evaluation System

![Tender Evaluation Dashboard](https://img.shields.io/badge/AI-GovTech-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react)
![Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=googlegemini)

## 📋 Overview

**ProcureSense** is a specialized AI-driven platform designed to automate the evaluation of tender eligibility criteria for government procurement, specifically tailored for organizations like the **CRPF**. 

Government procurement involves navigating a dense web of rules (GFR 2017, CVC guidelines). Evaluating a single tender with multiple bidders can take days of manual effort, checking hundreds of pages of documents (PDFs, scans, images) against complex eligibility clauses. ProcureSense automates this heavy lifting while ensuring full transparency and human oversight.

---

## ✨ Key Features

- **🧠 Automated Criterion Extraction**: Uses LLMs to identify and classify technical, financial, and compliance requirements from tender documents.
- **📄 Heterogeneous Document Parsing**: Seamlessly handles digital PDFs, scanned copies (OCR), Word files, and images.
- **⚖️ Smart Verdict Engine**: A hybrid rule-based and LLM-driven engine that assigns verdicts (**Eligible**, **Not Eligible**, or **Needs Manual Review**) with explainable reasoning.
- **👤 Human-in-the-Loop**: Escalates low-confidence or ambiguous cases to subject matter experts for manual review.
- **📑 Consolidated Reports**: Generates formal, audit-ready PDF evaluation reports with complete audit trails and source citations.
- **🛡️ Audit Trail**: Immutable logs of every automated and human decision made during the process.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **AI Engine**: [Google Gemini 3 Flash](https://ai.google.dev/)
- **PDF Processing**: [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/)
- **OCR**: [Tesseract 5](https://github.com/tesseract-ocr/tesseract) + OpenCV
- **Reporting**: ReportLab / WeasyPrint
- **Database**: SQLAlchemy + SQLite

### Frontend
- **Framework**: [React 19](https://react.dev/) + [Vite](https://vitejs.dev/)
- **Language**: TypeScript
- **State Management**: [Zustand](https://docs.pmnd.rs/zustand/)
- **Data Fetching**: [TanStack Query](https://tanstack.com/query)
- **Styling**: Vanilla CSS (Premium Glassmorphic Theme)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- [Tesseract OCR](https://tesseract-ocr.github.io/tessdoc/Installation.html) installed.

### Installation

#### 1. Clone the repository
```bash
git clone https://github.com/lucifer-135/ProcureSense---AI-Tender-Evaluation-System.git
cd ProcureSense---AI-Tender-Evaluation-System
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Configure Environment:**
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=sqlite:///./tender_eval.db
GEMINI_API_KEY=your_google_gemini_api_key
```

**Initialize & Run:**
```bash
python init_db.py
uvicorn app.main:app --reload
```

#### 3. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```

---

## 📖 Usage Workflow

1. **Upload Tender**: Parse requirements from the main tender document.
2. **Review Criteria**: Verify the AI-extracted eligibility rules.
3. **Upload Bidders**: Batch upload bidder submission documents.
4. **Evaluate**: Run the AI engine to generate verdicts.
5. **Manual Review**: Resolve flagged cases and download the final **Evaluation Report**.

---

## 📁 Project Structure

```text
├── backend/
│   ├── app/                # API, LLM Services, Models
│   ├── uploads/            # Document storage
│   └── requirements.txt    # Python deps
├── frontend/
│   ├── src/                # UI Components, Pages, State
│   └── package.json        # Frontend deps
└── docs/                   # PRD and Technical documentation
```

---

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Developed for the AI-Based Tender Evaluation Challenge.*
