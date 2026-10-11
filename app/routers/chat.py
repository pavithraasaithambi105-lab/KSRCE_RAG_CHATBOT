import logging

from fastapi import APIRouter, HTTPException
from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, OpenAIError

from app.llm import ask_llm
from app.rag.pipeline import retrieve, store
from app.schemas import ChatRequest, ChatResponse, Source

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _raise_upstream_error(operation: str, error: OpenAIError):
    logger.error(
        "AI provider %s failed: %s",
        operation,
        error,
        exc_info=(type(error), error, error.__traceback__),
    )
    if isinstance(error, AuthenticationError):
        raise HTTPException(
            status_code=503,
            detail="AI provider authentication failed. Set a valid LLM_API_KEY in the project-root .env file.",
        ) from error
    if isinstance(error, APITimeoutError):
        raise HTTPException(status_code=504, detail="The AI provider timed out. Please try again.") from error
    if isinstance(error, APIStatusError) and error.status_code == 429:
        raise HTTPException(status_code=503, detail="The AI provider is rate-limiting requests. Please try again later.") from error
    if isinstance(error, APIConnectionError):
        raise HTTPException(status_code=502, detail="The backend could not connect to the AI provider. Check the backend log.") from error
    if isinstance(error, APIStatusError):
        raise HTTPException(status_code=502, detail="The AI provider rejected the request. Check the backend log.") from error
    raise HTTPException(status_code=502, detail="The AI provider request failed. Check the backend log.") from error


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not store.chunks:
        raise HTTPException(status_code=400, detail="No documents indexed yet. Upload a PDF first.")
    try:
        hits = retrieve(request.question)
    except OpenAIError as e:
        _raise_upstream_error("embedding retrieval", e)
    try:
        answer = ask_llm(request.question, [chunk for chunk, _ in hits])
    except OpenAIError as e:
        _raise_upstream_error("chat completion", e)
    sources = [
        Source(
            source=c["source"], kind=c.get("kind", "text"), section=c.get("section", ""),
            pages=c["pages"], text=c["text"], score=round(score, 3),
        )
        for c, score in hits
    ]
    return ChatResponse(answer=answer, sources=sources)
