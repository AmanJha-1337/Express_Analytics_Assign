import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import fitz
import httpx
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import (
    CHUNK_OVERLAP, CHUNK_SIZE, MANIFEST_PATH, UPLOAD_DIR
)
from app.vectorstore import get_vectorstore


def _read_file(path: Path) -> list[Document]:
    suffix = path.suffix.lower()
    docs: list[Document] = []

    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            for page_no, page in enumerate(pdf, start=1):
                text = page.get_text("text").strip()
                if text:
                    docs.append(Document(
                        page_content=text,
                        metadata={"source": path.name, "page": page_no, "file_type": "pdf"}
                    ))
    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if text:
            docs.append(Document(
                page_content=text,
                metadata={"source": path.name, "page": None, "file_type": suffix[1:]}
            ))
    elif suffix in {".html", ".htm"}:
        soup = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
        text = soup.get_text("\n", strip=True)
        if text:
            docs.append(Document(
                page_content=text,
                metadata={"source": path.name, "page": None, "file_type": "html"}
            ))
    else:
        raise ValueError("Unsupported file type. Upload PDF, TXT, MD, or HTML.")

    return docs


async def _read_url(url: str) -> tuple[str, list[Document]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"Invalid URL: {url}")
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else parsed.netloc
    text = soup.get_text("\n", strip=True)
    if not text:
        raise ValueError(f"No readable text found at {url}")
    safe_name = f"url_{hashlib.md5(url.encode()).hexdigest()[:10]}.txt"
    return safe_name, [Document(
        page_content=text,
        metadata={"source": safe_name, "page": None, "file_type": "url", "url": url, "title": title}
    )]


def _manifest() -> list[dict]:
    if not MANIFEST_PATH.exists():
        return []
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_manifest(items: list[dict]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(items, indent=2), encoding="utf-8")


def index_documents(source_name: str, raw_docs: list[Document]) -> dict:
    if not raw_docs:
        raise ValueError(f"No extractable text found in {source_name}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(raw_docs)
    if not chunks:
        raise ValueError(f"No chunks created for {source_name}")

    store = get_vectorstore()
    # Replace previous chunks from the same source so re-uploading is safe.
    try:
        store._collection.delete(where={"source": source_name})
    except Exception:
        pass

    ids = []
    for index, chunk in enumerate(chunks):
        chunk.metadata["source"] = source_name
        chunk.metadata["chunk_id"] = f"{source_name}:{index + 1}"
        digest = hashlib.sha256(
            f"{source_name}|{index}|{chunk.page_content}".encode("utf-8")
        ).hexdigest()
        ids.append(digest)

    store.add_documents(chunks, ids=ids)

    items = _manifest()
    items = [item for item in items if item["filename"] != source_name]
    item = {
        "filename": source_name,
        "chunks": len(chunks),
        "type": raw_docs[0].metadata.get("file_type", "document"),
        "added_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(item)
    _save_manifest(items)
    return item


def ingest_saved_file(path: Path, display_name: str | None = None) -> dict:
    docs = _read_file(path)
    return index_documents(display_name or path.name, docs)


async def ingest_url(url: str) -> dict:
    name, docs = await _read_url(url)
    return index_documents(name, docs)


def list_documents() -> list[dict]:
    return _manifest()
