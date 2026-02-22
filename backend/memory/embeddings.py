"""Embedding utilities for the RAG pipeline.

Generates vector embeddings from text chunks using a lightweight
sentence-transformer model so they can be stored in Pinecone.
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Default model – small and fast; swap for a larger model in production.
_DEFAULT_MODEL = "all-MiniLM-L6-v2"


@dataclass
class EmbeddingService:
    """Generate embeddings from text using ``sentence-transformers``."""

    model_name: str = _DEFAULT_MODEL
    _model: object = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ #
    # Lazy model loading
    # ------------------------------------------------------------------ #
    def _get_model(self):  # noqa: ANN202
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
                logger.info("Loaded embedding model: %s", self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install it with: pip install sentence-transformers"
                )
        return self._model

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embeddings for a list of text strings."""
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def embed_single(self, text: str) -> list[float]:
        """Return the embedding vector for a single text string."""
        return self.embed([text])[0]

    @staticmethod
    def text_to_id(text: str) -> str:
        """Deterministic ID for a text chunk (SHA-256 hex digest)."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
