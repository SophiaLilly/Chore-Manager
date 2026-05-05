# application/api/routes/health.py

# Partial Imports
from fastapi import APIRouter


router = APIRouter()


@router.get("/")
def root():
    return {"status": "Chore Manager Backend is running"}


@router.get("/health")
def health():
    return {"status": "ok"}
