from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class Source(BaseModel):
    source: str
    kind: str
    section: str
    pages: List[int]
    score: float
    text: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source] = []


class IngestResponse(BaseModel):
    source: str
    pages: int
    chunks: int
    chunk_kinds: Dict[str, int]
    figures: Dict[str, int]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AssistantRequest(BaseModel):
    question: str
    history: List[ChatTurn] = []  # earlier turns, so follow-ups like "and his marks?" work


class AgentStep(BaseModel):
    tool: str
    arguments: Dict[str, Any]
    error: Optional[str] = None


class StudentCard(BaseModel):
    student_id: str
    roll_number: str
    name: str
    department: str
    year: int
    section: str
    cgpa: Optional[float]  # None for first-years
    email: str
    attendance_percentage: Optional[float]
    pending_arrears: int


class AssistantResponse(BaseModel):
    answer: str
    steps: List[AgentStep]  # which database tools the agent used, in order
    students: List[StudentCard] = []  # students looked up individually, shown as cards in the app
