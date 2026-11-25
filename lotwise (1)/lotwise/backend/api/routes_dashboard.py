"""Dashboard endpoints: counts + chart data."""

from fastapi import APIRouter

from utils import db

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def get_stats():
    """Counts and small aggregations for the dashboard cards + charts."""
    return db.dashboard_stats()
