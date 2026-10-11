from typing import List

from openai import OpenAI

from app.config import settings

client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions using the provided document excerpts. "
    "Excerpts can be plain text, tables (in Markdown) or text descriptions of figures such as "
    "organisation charts and flowcharts; read tables row by row and follow the hierarchy or steps "
    "in figure descriptions. Base your answer only on the context. If the context does not "
    "contain the answer, say you could not find it in the document. Cite pages like (p. 3) when "
    "you use them. Answer clearly and concisely."
)


def ask_llm(question: str, context_chunks: List[dict]) -> str:
    context = "\n\n---\n\n".join(
        f"[{c['source']}, {c.get('kind', 'text')}, pages {', '.join(map(str, c['pages']))}]\n{c['text']}"
        for c in context_chunks
    )
    response = client.chat.completions.create(
        model=settings.llm_model,
        max_tokens=settings.llm_max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return response.choices[0].message.content
