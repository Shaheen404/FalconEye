"""RAG pipeline – scrape → chunk → embed → store → retrieve.

Provides a ``build_rag_tool`` helper that returns a CrewAI-compatible tool
backed by the Pinecone vector store.
"""

from __future__ import annotations

import logging
import os
import textwrap
from typing import Any

from backend.memory.pinecone_store import PineconeStore

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Text chunking
# ------------------------------------------------------------------ #
def chunk_text(text: str, max_chars: int = 500, overlap: int = 50) -> list[str]:
    """Split *text* into overlapping chunks of roughly *max_chars* length."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start += max_chars - overlap
    return chunks


# ------------------------------------------------------------------ #
# Ingest helper
# ------------------------------------------------------------------ #
def ingest_text(
    text: str,
    index_name: str,
    source: str = "unknown",
    max_chars: int = 500,
) -> int:
    """Chunk and ingest *text* into the Pinecone index.

    Returns the number of vectors upserted.
    """
    chunks = chunk_text(text, max_chars=max_chars)
    metadata = [{"source": source}] * len(chunks)
    store = PineconeStore(index_name=index_name)
    return store.upsert(chunks, metadata)


# ------------------------------------------------------------------ #
# CrewAI RAG tool builder
# ------------------------------------------------------------------ #
def build_rag_tool(index_name: str | None = None) -> Any:
    """Return a CrewAI-compatible tool that queries the Pinecone index."""
    try:
        from crewai.tools import tool as crewai_tool
    except ImportError:
        raise ImportError("crewai is required. Install it with: pip install crewai")

    idx = index_name or os.getenv("PINECONE_INDEX", "falconeye")
    store = PineconeStore(index_name=idx)

    @crewai_tool("RAG Search")
    def rag_search(query: str) -> str:
        """Search the vector memory for context relevant to *query*."""
        results = store.query(query, top_k=5)
        if not results:
            return "No relevant context found in memory."
        parts = [
            f"[{r['score']:.2f}] {textwrap.shorten(r['text'], 300)}"
            for r in results
        ]
        return "\n---\n".join(parts)

    return rag_search
