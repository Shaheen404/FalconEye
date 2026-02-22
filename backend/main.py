"""FalconEye – FastAPI Application Entry-point.

Run with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.crew_routes import router as crew_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

app = FastAPI(
    title="FalconEye API",
    description="RAG-enhanced OSINT Agentic Tool",
    version="0.1.0",
)

# ---- CORS (allow the Vite dev server) --------------------------------- #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routes ------------------------------------------------------------ #
app.include_router(crew_router)


@app.get("/")
async def root():
    return {"app": "FalconEye", "version": "0.1.0"}
