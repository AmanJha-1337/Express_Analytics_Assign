from typing import TypedDict
from langchain_core.documents import Document
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

from app.config import GROQ_API_KEY, GROQ_MODEL, MAX_RETRIES, TOP_K
from app.vectorstore import get_vectorstore


class RAGState(TypedDict, total=False):
    question: str
    search_query: str
    documents: list[Document]
    relevant_documents: list[Document]
    retry_count: int
    answer: str


def get_llm():
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")
    return ChatGroq(
        model=GROQ_MODEL,
        temperature=0,
        api_key=GROQ_API_KEY,
        max_retries=2,
    )


def _content(response) -> str:
    value = response.content
    if isinstance(value, list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in value
        )
    return str(value)


def query_analysis(state: RAGState) -> dict:
    llm = get_llm()
    question = state["question"]
    retries = state.get("retry_count", 0)
    if retries == 0:
        prompt = (
            "Rewrite the user's technical question as a concise search query. "
            "Preserve its meaning and important technical terms. Return only the query.\n"
            f"Question: {question}"
        )
    else:
        previous = state.get("search_query", question)
        prompt = (
            "The previous retrieval did not find relevant documentation. "
            "Create a different, broader search query using useful synonyms. "
            "Return only the query.\n"
            f"Original question: {question}\nPrevious query: {previous}"
        )
    rewritten = _content(llm.invoke(prompt)).strip().strip('"')
    return {"search_query": rewritten or question}


def retrieval(state: RAGState) -> dict:
    store = get_vectorstore()
    docs = store.similarity_search(state.get("search_query", state["question"]), k=TOP_K)
    return {"documents": docs}


def document_grading(state: RAGState) -> dict:
    llm = get_llm()
    relevant = []
    question = state["question"]
    for doc in state.get("documents", []):
        prompt = (
            "You are grading retrieved technical documentation for a RAG system. "
            "Decide whether this passage contains information useful for answering "
            "the question. Reply with only YES or NO.\n"
            f"Question: {question}\nPassage:\n{doc.page_content[:3500]}"
        )
        verdict = _content(llm.invoke(prompt)).strip().upper()
        if verdict.startswith("YES"):
            relevant.append(doc)

    retries = state.get("retry_count", 0)
    if not relevant:
        retries += 1
    return {"relevant_documents": relevant, "retry_count": retries}


def generation(state: RAGState) -> dict:
    llm = get_llm()
    context_parts = []
    for doc in state["relevant_documents"]:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page")
        label = f"{source}" + (f", page {page}" if page else "")
        context_parts.append(f"[Source: {label}]\n{doc.page_content}")
    context = "\n\n---\n\n".join(context_parts)

    prompt = (
        "You are a technical documentation assistant. Answer the question using "
        "ONLY the supplied context. If the context does not contain the answer, "
        "say so instead of guessing. Be clear and practical. Cite claims inline "
        "using [filename, page N] or [filename].\n\n"
        f"Question: {state['question']}\n\nContext:\n{context}"
    )
    answer = _content(llm.invoke(prompt)).strip()
    return {"answer": answer}


def no_answer(state: RAGState) -> dict:
    return {
        "answer": (
            "I couldn't find sufficiently relevant information in the indexed "
            "documents to answer this question. Please upload relevant technical "
            "documentation or ask a question covered by the current corpus."
        )
    }


def route_after_grading(state: RAGState) -> str:
    if state.get("relevant_documents"):
        return "generate"
    if state.get("retry_count", 0) <= MAX_RETRIES:
        return "rewrite"
    return "no_answer"


def build_graph():
    graph = StateGraph(RAGState)
    graph.add_node("query_analysis", query_analysis)
    graph.add_node("retrieval", retrieval)
    graph.add_node("document_grading", document_grading)
    graph.add_node("generation", generation)
    graph.add_node("no_answer", no_answer)

    graph.set_entry_point("query_analysis")
    graph.add_edge("query_analysis", "retrieval")
    graph.add_edge("retrieval", "document_grading")
    graph.add_conditional_edges(
        "document_grading",
        route_after_grading,
        {
            "generate": "generation",
            "rewrite": "query_analysis",
            "no_answer": "no_answer",
        },
    )
    graph.add_edge("generation", END)
    graph.add_edge("no_answer", END)
    return graph.compile()


rag_app = build_graph()


def ask_question(question: str) -> dict:
    result = rag_app.invoke({
        "question": question,
        "search_query": question,
        "retry_count": 0,
    })
    docs = result.get("relevant_documents", [])
    sources = []
    seen = set()
    for doc in docs:
        key = (doc.metadata.get("source"), doc.metadata.get("page"), doc.metadata.get("chunk_id"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "source": doc.metadata.get("source", "unknown"),
            "page": doc.metadata.get("page"),
            "chunk_id": doc.metadata.get("chunk_id"),
            "excerpt": doc.page_content[:240].replace("\n", " "),
        })
    return {
        "answer": result.get("answer", "No answer generated."),
        "sources": sources,
        "retries": result.get("retry_count", 0),
    }
