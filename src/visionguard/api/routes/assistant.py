"""Intelligent Grounded Query Assistant API routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from visionguard.query.grounded_assistant import grounded_assistant

router = APIRouter(prefix="/api/assistant", tags=["Grounded Assistant"])

class QueryRequest(BaseModel):
    query: str
    user_role: str = "operator"

@router.post("/query")
def submit_grounded_query(req: QueryRequest):
    """
    Submits a natural language traffic question.
    Returns deterministic, grounded response citing verified database facts.
    """
    return grounded_assistant.process_query(req.query, user_role=req.user_role)
