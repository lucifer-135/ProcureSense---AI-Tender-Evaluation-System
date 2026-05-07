from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import tenders, bidders, verdicts, reports

from .config import get_settings

app = FastAPI(
    title="AI Tender Evaluation System",
    description="AI-based tender evaluation and eligibility analysis for government procurement",
    version="1.0.0",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tenders.router)
app.include_router(bidders.router)
app.include_router(verdicts.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {"message": "AI Tender Evaluation API", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok"}
