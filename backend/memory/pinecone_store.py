"""Pinecone vector-store integration for FalconEye's RAG pipeline.

Handles upserting document chunks and querying for relevant context.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field

from backend.memory.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class PineconeStore:
    """Thin wrapper around the Pinecone SDK for vector storage."""

    index_name: str
    embedding_service: EmbeddingService = field(default_factory=EmbeddingService)
    _index: object = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ #
    # Lazy index connection
    # ------------------------------------------------------------------ #
    def _get_index(self):  # noqa: ANN202
        if self._index is None:
            try:
                from pinecone import Pinecone

                api_key = os.getenv("PINECONE_API_KEY")
                if not api_key:
                    raise EnvironmentError(
                        "PINECONE_API_KEY environment variable is not set."
                    )
                pc = Pinecone(api_key=api_key)
                self._index = pc.Index(self.index_name)
                logger.info("Connected to Pinecone index: %s", self.index_name)
            except ImportError:
                raise ImportError(
                    "pinecone is required. Install it with: pip install pinecone"
                )
        return self._index

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def upsert(self, texts: list[str], metadata: list[dict] | None = None) -> int:
        """Embed and upsert *texts* into the Pinecone index.

        Returns the number of vectors upserted.
        """
        index = self._get_index()
        vectors_data = self.embedding_service.embed(texts)
        meta = metadata or [{} for _ in texts]

        vectors = [
            {
                "id": EmbeddingService.text_to_id(text),
                "values": vec,
                "metadata": {**m, "text": text},
            }
            for text, vec, m in zip(texts, vectors_data, meta)
        ]

        index.upsert(vectors=vectors)
        logger.info("Upserted %d vectors into %s", len(vectors), self.index_name)
        return len(vectors)

    def query(self, query_text: str, top_k: int = 5) -> list[dict]:
        """Query the index and return the *top_k* most relevant chunks."""
        index = self._get_index()
        query_vec = self.embedding_service.embed_single(query_text)

        results = index.query(vector=query_vec, top_k=top_k, include_metadata=True)
        return [
            {
                "id": match["id"],
                "score": match["score"],
                "text": match.get("metadata", {}).get("text", ""),
                "metadata": match.get("metadata", {}),
            }
            for match in results.get("matches", [])
        ]
