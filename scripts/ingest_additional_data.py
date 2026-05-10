import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config import config

ADDITIONAL_POLICIES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "additional_policies",
)


def _get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def ingest_to_pinecone(all_docs, embeddings):
    from backend.services.pinecone_service import get_pinecone_client

    pc = get_pinecone_client()
    index = pc.Index(config.PINECONE_INDEX_NAME)

    texts = [doc.page_content for doc in all_docs]
    metadatas = [doc.metadata for doc in all_docs]
    vectors = embeddings.embed_documents(texts)

    # Use file-based IDs to avoid collisions with existing chunks
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = [
            {
                "id": f"additional-{metadatas[i+j]['source']}-chunk-{i+j}",
                "values": vectors[i + j],
                "metadata": {**metadatas[i + j], "text": texts[i + j]},
            }
            for j in range(min(batch_size, len(vectors) - i))
        ]
        index.upsert(vectors=batch)

    return "pinecone"


def ingest_to_faiss(all_docs):
    from backend.services.rag_service import VECTORSTORE_PATH, load_vectorstore

    vectorstore = load_vectorstore()
    vectorstore.add_documents(all_docs)
    vectorstore.save_local(VECTORSTORE_PATH)
    return "faiss"


if __name__ == "__main__":
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    txt_files = sorted(
        f for f in os.listdir(ADDITIONAL_POLICIES_DIR) if f.endswith(".txt")
    )

    if not txt_files:
        print("No .txt files found in data/additional_policies/")
        sys.exit(1)

    print(f"Found {len(txt_files)} files to ingest from data/additional_policies/")
    print()

    all_docs = []
    for filename in txt_files:
        filepath = os.path.join(ADDITIONAL_POLICIES_DIR, filename)
        loader = TextLoader(filepath, encoding="utf-8")
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = filename
            chunk.metadata["category"] = "additional_policy"
        all_docs.extend(chunks)
        print(f"  {filename}: {len(chunks)} chunks")

    print()
    print(f"Total chunks to upload: {len(all_docs)}")
    print("Generating embeddings...")

    embeddings = _get_embeddings()

    if config.PINECONE_API_KEY:
        print(f"Uploading to Pinecone index '{config.PINECONE_INDEX_NAME}'...")
        store_used = ingest_to_pinecone(all_docs, embeddings)
    else:
        print("No PINECONE_API_KEY found — adding to local FAISS index...")
        store_used = ingest_to_faiss(all_docs)

    print(f"\nSuccessfully added {len(all_docs)} chunks to {store_used}.")
    print()

    # Verify with a test query
    print("=== Verification Test Query ===")
    from backend.services.rag_service import retrieve_context

    test_query = "What are the steps for handling a customer complaint?"
    context, sources = retrieve_context(test_query)
    print(f"Query: {test_query}")
    print(f"Sources: {sources}")
    print(f"Preview: {context[:250]}")
    print()
    print("Ingestion complete — new policy documents are now searchable.")
