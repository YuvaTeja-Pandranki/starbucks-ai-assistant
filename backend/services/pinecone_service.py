import time

from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone, ServerlessSpec

from backend.config import config

_SOURCE_FILES = [
    "refund_policy.txt",
    "store_operations.txt",
    "compliance_rules.txt",
]


def _get_embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )


def get_pinecone_client() -> Pinecone:
    return Pinecone(api_key=config.PINECONE_API_KEY)


def create_index_if_not_exists() -> str:
    pc = get_pinecone_client()
    existing = [idx.name for idx in pc.list_indexes()]

    if config.PINECONE_INDEX_NAME not in existing:
        print(f"Creating Pinecone index '{config.PINECONE_INDEX_NAME}'...")
        pc.create_index(
            name=config.PINECONE_INDEX_NAME,
            dimension=config.PINECONE_DIMENSION,
            metric=config.PINECONE_METRIC,
            spec=ServerlessSpec(
                cloud=config.PINECONE_CLOUD,
                region=config.PINECONE_REGION,
            ),
        )
        print("Waiting for index to become ready...")
        while True:
            status = pc.describe_index(config.PINECONE_INDEX_NAME).status
            if status.get("ready", False):
                break
            time.sleep(2)
        print(f"Index '{config.PINECONE_INDEX_NAME}' is ready.")
    else:
        print(f"Index '{config.PINECONE_INDEX_NAME}' already exists.")

    return config.PINECONE_INDEX_NAME


def build_pinecone_vectorstore(index_name: str | None = None):
    index_name = index_name or create_index_if_not_exists()
    embeddings = _get_embeddings()
    pc = get_pinecone_client()
    index = pc.Index(index_name)

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_docs = []

    for filename in _SOURCE_FILES:
        import os
        filepath = os.path.join(config.DATA_DIR, filename)
        loader = TextLoader(filepath, encoding="utf-8")
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = filename
        all_docs.extend(chunks)

    print(f"Embedding and uploading {len(all_docs)} chunks to Pinecone...")

    texts = [doc.page_content for doc in all_docs]
    metadatas = [doc.metadata for doc in all_docs]
    vectors = embeddings.embed_documents(texts)

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch_vectors = [
            {
                "id": f"chunk-{i + j}",
                "values": vectors[i + j],
                "metadata": {**metadatas[i + j], "text": texts[i + j]},
            }
            for j in range(min(batch_size, len(vectors) - i))
        ]
        index.upsert(vectors=batch_vectors)

    print(f"Successfully uploaded {len(all_docs)} chunks to index '{index_name}'.")
    return index


def load_pinecone_vectorstore():
    pc = get_pinecone_client()
    return pc.Index(config.PINECONE_INDEX_NAME)


def retrieve_from_pinecone(query: str, k: int = 4) -> tuple[str, list[str]]:
    embeddings = _get_embeddings()
    query_vector = embeddings.embed_query(query)

    index = load_pinecone_vectorstore()
    results = index.query(vector=query_vector, top_k=k, include_metadata=True)

    chunks = [match["metadata"].get("text", "") for match in results["matches"]]
    sources = list({match["metadata"].get("source", "unknown") for match in results["matches"]})

    context = "\n\n".join(chunks)
    return context, sources
