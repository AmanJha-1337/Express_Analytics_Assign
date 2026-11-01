import json
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import FEEDBACK_PATH, UPLOAD_DIR
from app.ingestion import ingest_saved_file, ingest_url, list_documents
from app.rag_graph import ask_question
from app.schemas import (
    QueryRequest, QueryResponse, FeedbackRequest, IngestResponse
)

app = FastAPI(
    title="Self-Corrective RAG Documentation Assistant",
    description=(
        "Upload technical PDFs and ask grounded questions. "
        "Powered by LangGraph, ChromaDB, local embeddings, and Groq."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".html", ".htm"}
MAX_FILE_BYTES = 15 * 1024 * 1024


@app.get("/", tags=["General"])
def home():
    return {
        "message": "RAG Documentation Assistant is running.",
        "docs": "/docs",
        "upload_hint": "Use POST /ingest in Swagger UI to upload PDF files.",
    }


@app.get("/health", tags=["General"])
def health():
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse, tags=["RAG"])
def query(payload: QueryRequest):
    try:
        result = ask_question(payload.question.strip())
        return QueryResponse(
            question=payload.question,
            answer=result["answer"],
            sources=result["sources"],
            retries=result["retries"],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")

from fastapi import FastAPI, UploadFile, File

@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):

    content = await file.read()

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
        "message": "File received successfully"
    }

@app.get("/documents", tags=["Documents"])
def documents():
    return {"count": len(list_documents()), "documents": list_documents()}


@app.post("/feedback", tags=["Feedback"])
def feedback(payload: FeedbackRequest):
    FEEDBACK_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = payload.model_dump()
    from datetime import datetime, timezone
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    with FEEDBACK_PATH.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"message": "Feedback saved.", "rating": payload.rating}
