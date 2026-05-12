import os

from backend.config import config

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VECTORSTORE_PATH = os.path.join(_PROJECT_ROOT, "vectorstore")

_SOURCE_FILES = [
    "refund_policy.txt",
    "store_operations.txt",
    "compliance_rules.txt",
]


def _get_embeddings():
    from langchain_aws import BedrockEmbeddings
    import boto3
    client_kwargs = {"region_name": config.AWS_REGION}
    if config.AWS_ACCESS_KEY_ID and config.APP_ENV != "production":
        client_kwargs["aws_access_key_id"] = config.AWS_ACCESS_KEY_ID
        client_kwargs["aws_secret_access_key"] = config.AWS_SECRET_ACCESS_KEY
    bedrock_client = boto3.client("bedrock-runtime", **client_kwargs)
    return BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        client=bedrock_client,
    )


def build_local_vectorstore():
    from langchain_community.document_loaders import TextLoader
    from langchain_community.vectorstores import FAISS
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    all_docs = []

    for filename in _SOURCE_FILES:
        filepath = os.path.join(config.DATA_DIR, filename)
        loader = TextLoader(filepath, encoding="utf-8")
        docs = loader.load()
        chunks = splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["source"] = filename
        all_docs.extend(chunks)

    vectorstore = FAISS.from_documents(all_docs, _get_embeddings())
    os.makedirs(VECTORSTORE_PATH, exist_ok=True)
    vectorstore.save_local(VECTORSTORE_PATH)
    return vectorstore


def load_vectorstore():
    from langchain_community.vectorstores import FAISS

    index_file = os.path.join(VECTORSTORE_PATH, "index.faiss")
    if os.path.exists(index_file):
        return FAISS.load_local(
            VECTORSTORE_PATH,
            _get_embeddings(),
            allow_dangerous_deserialization=True,
        )
    return build_local_vectorstore()


def retrieve_context(query: str, k: int = 4) -> tuple[str, list[str]]:
    if config.PINECONE_API_KEY:
        from backend.services.pinecone_service import retrieve_from_pinecone
        return retrieve_from_pinecone(query, k=k)

    vectorstore = load_vectorstore()
    results = vectorstore.similarity_search(query, k=k)
    context = "\n\n".join(doc.page_content for doc in results)
    sources = list({doc.metadata.get("source", "unknown") for doc in results})
    return context, sources
