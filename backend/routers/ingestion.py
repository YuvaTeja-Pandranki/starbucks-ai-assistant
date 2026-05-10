import os

from fastapi import APIRouter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from backend.config import config

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])


class UploadRequest(BaseModel):
    filename: str
    content: str
    category: str


@router.post("/upload")
async def upload_document(request: UploadRequest):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(request.content)
    metadata = {"source": request.filename, "category": request.category}

    if config.PINECONE_API_KEY:
        from backend.services.pinecone_service import get_pinecone_client
        from langchain_huggingface import HuggingFaceEmbeddings

        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        vectors = embeddings.embed_documents(chunks)

        pc = get_pinecone_client()
        index = pc.Index(config.PINECONE_INDEX_NAME)

        upsert_data = [
            {
                "id": f"{request.filename}-chunk-{i}",
                "values": vectors[i],
                "metadata": {**metadata, "text": chunks[i]},
            }
            for i in range(len(chunks))
        ]
        index.upsert(vectors=upsert_data)
        store_used = "pinecone"
    else:
        from langchain_core.documents import Document
        from backend.services.rag_service import _get_embeddings, load_vectorstore, VECTORSTORE_PATH

        docs = [Document(page_content=chunk, metadata=metadata) for chunk in chunks]
        vectorstore = load_vectorstore()
        vectorstore.add_documents(docs)
        vectorstore.save_local(VECTORSTORE_PATH)
        store_used = "faiss"

    return {
        "filename": request.filename,
        "chunks_added": len(chunks),
        "store_used": store_used,
    }


@router.post("/rebuild")
async def rebuild_vectorstore():
    if config.PINECONE_API_KEY:
        from backend.services.pinecone_service import build_pinecone_vectorstore, get_pinecone_client

        pc = get_pinecone_client()
        existing = [idx.name for idx in pc.list_indexes()]
        if config.PINECONE_INDEX_NAME in existing:
            pc.delete_index(config.PINECONE_INDEX_NAME)

        build_pinecone_vectorstore()

        index = pc.Index(config.PINECONE_INDEX_NAME)
        stats = index.describe_index_stats()
        total_chunks = stats.get("total_vector_count", 0)
        store_used = "pinecone"
    else:
        from backend.services.rag_service import build_local_vectorstore
        build_local_vectorstore()
        total_chunks = 0
        store_used = "faiss"

    from backend.services.pinecone_service import _SOURCE_FILES
    files_processed = _SOURCE_FILES

    return {
        "total_chunks": total_chunks,
        "store_used": store_used,
        "files_processed": files_processed,
    }


@router.get("/status")
async def ingestion_status():
    if config.PINECONE_API_KEY:
        from backend.services.pinecone_service import get_pinecone_client

        pc = get_pinecone_client()
        existing = [idx.name for idx in pc.list_indexes()]

        if config.PINECONE_INDEX_NAME in existing:
            index = pc.Index(config.PINECONE_INDEX_NAME)
            stats = index.describe_index_stats()
            vector_count = stats.get("total_vector_count", 0)
            return {
                "store_type": "pinecone",
                "index_name": config.PINECONE_INDEX_NAME,
                "status": "ready",
                "message": f"Pinecone index '{config.PINECONE_INDEX_NAME}' is active with {vector_count} vectors.",
            }
        else:
            return {
                "store_type": "pinecone",
                "index_name": config.PINECONE_INDEX_NAME,
                "status": "missing",
                "message": f"Index '{config.PINECONE_INDEX_NAME}' does not exist. Run /rebuild to create it.",
            }
    else:
        from backend.services.rag_service import VECTORSTORE_PATH

        index_file = os.path.join(VECTORSTORE_PATH, "index.faiss")
        if os.path.exists(index_file):
            return {
                "store_type": "faiss",
                "index_name": "local",
                "status": "ready",
                "message": f"Local FAISS index found at {VECTORSTORE_PATH}.",
            }
        else:
            return {
                "store_type": "faiss",
                "index_name": "local",
                "status": "missing",
                "message": "No local FAISS index found. Run /rebuild to create it.",
            }
