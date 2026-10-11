"""Student Info tab (direct lookups) and Assistant tab (agent) - separate from the handbook /chat."""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from openai import OpenAIError

from app.schemas import AssistantRequest, AssistantResponse
from app.students import queries as q
from app.students.agent import run_agent

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/assistant", response_model=AssistantResponse)
def assistant(request: AssistantRequest):
    """Ask about students in plain English; the agent picks the database tools to use."""
    try:
        return run_agent(request.question, [t.model_dump() for t in request.history])
    except OpenAIError as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")


@router.get("")
def list_students(
    department: Optional[str] = None, year: Optional[int] = Query(None, ge=1, le=4),
    section: Optional[str] = None, sort_by: str = "roll_number", descending: bool = False,
    limit: int = Query(60, le=200),
):
    """Students of a department / year / section."""
    return q.list_students(department=department, year=year, section=section,
                           sort_by=sort_by, descending=descending, limit=limit)


@router.get("/search")
def search_by_name(name: str):
    return q.find_student(name=name)


@router.get("/{identifier}")
def get_student(identifier: str):
    """One student by roll number (24CS015) or student ID (STU10615)."""
    return _or_404(q.find_student, identifier=identifier)


@router.get("/{identifier}/attendance")
def get_attendance(identifier: str, from_date: Optional[str] = None, to_date: Optional[str] = None):
    return _or_404(q.get_attendance, student=identifier, from_date=from_date, to_date=to_date)


@router.get("/{identifier}/marks")
def get_marks(identifier: str, semester: Optional[int] = None):
    return _or_404(q.get_marks, student=identifier, semester=semester)


@router.get("/{identifier}/arrears")
def get_arrears(identifier: str, status: Optional[str] = None):
    return _or_404(q.get_arrears, student=identifier, status=status)


def _or_404(func, **kwargs):
    try:
        return func(**kwargs)
    except q.NotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
