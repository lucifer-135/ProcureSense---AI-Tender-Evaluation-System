"""Run this script to create all database tables."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import engine, Base
from app.models import (
    Tender, Criterion, Bidder, BidderDocument,
    BidderEvidence, Verdict, HumanReview,
)


def init():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done! All tables created successfully.")


if __name__ == "__main__":
    init()
