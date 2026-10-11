from typing import List

import numpy as np

from app.config import settings
from app.llm import client

_BATCH_SIZE = 64


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed texts and return unit-length float32 vectors, shape (len(texts), dim)."""
    vectors = []
    for i in range(0, len(texts), _BATCH_SIZE):
        response = client.embeddings.create(
            model=settings.embedding_model, input=texts[i : i + _BATCH_SIZE]
        )
        vectors.extend(item.embedding for item in response.data)

    matrix = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    return matrix / np.clip(norms, 1e-12, None)
