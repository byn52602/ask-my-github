"""Shared state and utilities for the application."""
from typing import Dict
from ..core.retriever import Retriever

# Shared in-memory storage for retrievers
_retrievers: Dict[str, Retriever] = {}

def get_retriever(repo_url: str) -> Retriever | None:
    """Get a retriever for the given repository URL."""
    return _retrievers.get(repo_url)

def set_retriever(repo_url: str, retriever: Retriever) -> None:
    """Store a retriever for the given repository URL."""
    _retrievers[repo_url] = retriever

def list_retrievers() -> list[str]:
    """List all repository URLs that have retrievers."""
    return list(_retrievers.keys())
