from functools import lru_cache

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import CHROMA_DIR, EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


@lru_cache(maxsize=1)
def get_vectorstore():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name="technical_documentation",
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embeddings(),
        collection_metadata={"hnsw:space": "cosine"},
    )
