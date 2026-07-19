"""
rag_engine.py — PDF ingestion + retrieval (RAG) for CARA.

Uses LangChain's PDF loader + text splitter, sentence-transformers embeddings
(via langchain-huggingface), and a persistent Chroma vector store
(via langchain-chroma) so uploaded documents survive server restarts.
"""

import logging
import os

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("cara.rag")

PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_store")
COLLECTION_NAME = "cara_documents"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_embeddings = None
_vectorstore = None


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=PERSIST_DIR,
        )
    return _vectorstore


def index_pdf(file_path: str) -> int:
    """
    Load a PDF from disk, chunk it, embed it, and add it to the persistent
    Chroma vector store. Returns the number of chunks indexed.
    """
    loader = PyPDFLoader(file_path)
    pages = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(pages)

    if not chunks:
        return 0

    # Tag each chunk with its source filename for traceability.
    source_name = os.path.basename(file_path)
    for chunk in chunks:
        chunk.metadata["source"] = source_name

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)

    logger.info("Indexed %d chunks from %s", len(chunks), source_name)
    return len(chunks)


def search_documents(query: str, k: int = 4) -> list[str]:
    """
    Retrieve the top-k most relevant chunks for a query from the vector store.
    Returns a list of plain-text chunk contents (empty list if no index exists yet).
    """
    vectorstore = get_vectorstore()

    try:
        # If the collection is empty, Chroma may raise or return nothing.
        results = vectorstore.similarity_search(query, k=k)
    except Exception as exc:  # noqa: BLE001
        logger.warning("similarity_search failed (likely an empty index): %s", exc)
        return []

    return [doc.page_content for doc in results]
