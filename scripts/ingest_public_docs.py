import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import PyPDF2
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import config
from backend.services.pinecone_service import get_pinecone_client

PUBLIC_DOCS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "public_docs",
)


def extract_text_from_pdf(filepath: str) -> str:
    text_parts = []
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
    return "\n".join(text_parts)


def ingest_public_docs():
    pdf_files = sorted(f for f in os.listdir(PUBLIC_DOCS_DIR) if f.endswith(".pdf"))
    if not pdf_files:
        print("No PDF files found in data/public_docs/")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF(s) in data/public_docs/")
    print()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_docs = []

    for filename in pdf_files:
        filepath = os.path.join(PUBLIC_DOCS_DIR, filename)
        print(f"Reading: {filename}")
        raw_text = extract_text_from_pdf(filepath)
        print(f"  Extracted {len(raw_text):,} characters")

        doc = Document(
            page_content=raw_text,
            metadata={"source": filename, "category": "public_document"},
        )
        chunks = splitter.split_documents([doc])
        for i, chunk in enumerate(chunks):
            chunk.metadata["source"] = filename
            chunk.metadata["category"] = "public_document"

        print(f"  Chunked into {len(chunks)} pieces")
        all_docs.extend(chunks)
        print()

    print(f"Total chunks to upload: {len(all_docs)}")
    print("Generating embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    texts = [doc.page_content for doc in all_docs]
    metadatas = [doc.metadata for doc in all_docs]
    vectors = embeddings.embed_documents(texts)
    print(f"Embeddings generated for {len(vectors)} chunks")
    print()

    print(f"Uploading to Pinecone index '{config.PINECONE_INDEX_NAME}'...")
    pc = get_pinecone_client()
    index = pc.Index(config.PINECONE_INDEX_NAME)

    batch_size = 100
    uploaded = 0
    for i in range(0, len(vectors), batch_size):
        batch = [
            {
                "id": f"pubdoc-{metadatas[i+j]['source']}-chunk-{i+j}",
                "values": vectors[i + j],
                "metadata": {**metadatas[i + j], "text": texts[i + j]},
            }
            for j in range(min(batch_size, len(vectors) - i))
        ]
        index.upsert(vectors=batch)
        uploaded += len(batch)
        print(f"  Uploaded batch: {uploaded}/{len(vectors)} chunks")

    print()
    print(f"Successfully ingested {len(all_docs)} chunks into Pinecone.")
    print()

    # Verify with a test query
    print("=== Verification Test Query ===")
    from backend.services.rag_service import retrieve_context

    test_query = "What are the food safety requirements for food service workers?"
    context, sources = retrieve_context(test_query)
    print(f"Query: {test_query}")
    print(f"Sources: {sources}")
    print(f"Preview: {context[:300]}")
    print()
    print("Public docs ingestion complete — documents are now searchable via RAG.")


if __name__ == "__main__":
    ingest_public_docs()
