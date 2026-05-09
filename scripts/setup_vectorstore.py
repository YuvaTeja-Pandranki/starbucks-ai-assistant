import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich import print

from backend.services.rag_service import build_local_vectorstore, retrieve_context

if __name__ == "__main__":
    print("[bold cyan]Building local FAISS vectorstore...[/bold cyan]")
    build_local_vectorstore()
    print("[bold green]Done! Vectorstore is ready.[/bold green]")

    query = "What is the refund threshold for manager approval?"
    print(f"\n[bold yellow]Test query:[/bold yellow] {query}")
    context, sources = retrieve_context(query)

    print(f"[bold]Sources:[/bold] {sources}")
    print(f"[bold]Context preview (first 300 chars):[/bold]\n{context[:300]}")
