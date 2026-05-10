import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print

parser = argparse.ArgumentParser(description="Build vectorstore for Starbucks AI Assistant")
parser.add_argument(
    "--store",
    choices=["faiss", "pinecone"],
    default="pinecone",
    help="Which vectorstore backend to use (default: pinecone)",
)
args = parser.parse_args()

if args.store == "pinecone":
    from backend.services.pinecone_service import build_pinecone_vectorstore, retrieve_from_pinecone

    print("[bold cyan]Building Pinecone cloud vectorstore...[/bold cyan]")
    build_pinecone_vectorstore()
    print("[bold green]Pinecone vectorstore ready.[/bold green]")

    query = "What is the refund threshold for manager approval?"
    print(f"\n[bold yellow]Test query:[/bold yellow] {query}")
    context, sources = retrieve_from_pinecone(query)
    print(f"[bold]Sources:[/bold] {sources}")
    print(f"[bold]Context preview (first 300 chars):[/bold]\n{context[:300]}")
    print("\n[bold green]Store used: Pinecone (cloud)[/bold green]")

else:
    from backend.services.rag_service import build_local_vectorstore, retrieve_context

    print("[bold cyan]Building local FAISS vectorstore...[/bold cyan]")
    build_local_vectorstore()
    print("[bold green]FAISS vectorstore ready.[/bold green]")

    query = "What is the refund threshold for manager approval?"
    print(f"\n[bold yellow]Test query:[/bold yellow] {query}")
    context, sources = retrieve_context(query)
    print(f"[bold]Sources:[/bold] {sources}")
    print(f"[bold]Context preview (first 300 chars):[/bold]\n{context[:300]}")
    print("\n[bold green]Store used: FAISS (local)[/bold green]")
