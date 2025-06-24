from typing import List, Dict, Any, Optional
import numpy as np
from .embedder import Embedder

class Retriever:
    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder or Embedder()
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []

    async def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunks to the retriever and generate embeddings for them.
        """
        if not chunks:
            return
            
        # Only embed chunks that don't already have embeddings
        chunks_to_embed = [c for c in chunks if "embedding" not in c]
        
        if chunks_to_embed:
            await self.embedder.embed_chunks(chunks_to_embed)
        
        # Add all chunks to our storage
        self.chunks.extend(chunks)
        self.embeddings.extend([c.get("embedding", []) for c in chunks])

    async def get_relevant_chunks(
        self, 
        query: str, 
        top_k: int = 3,
        min_similarity: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a given query.
        Returns a list of chunks sorted by relevance.
        """
        if not self.chunks:
            return []
            
        # Get query embedding
        query_embedding = (await self.embedder.get_embeddings([query]))[0]
        
        # Calculate similarities
        similarities = []
        for i, chunk_embedding in enumerate(self.embeddings):
            if not chunk_embedding:  # Skip chunks without embeddings
                continue
                
            similarity = self.embedder.cosine_similarity(
                query_embedding, 
                chunk_embedding
            )
            similarities.append((i, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Get top-k chunks above min_similarity threshold
        result = []
        for idx, score in similarities[:top_k]:
            if score < min_similarity:
                continue
                
            chunk = self.chunks[idx].copy()
            chunk["score"] = score
            result.append(chunk)
        
        return result
    
    def clear(self) -> None:
        """Clear all stored chunks and embeddings."""
        self.chunks = []
        self.embeddings = []

    def get_chunk_count(self) -> int:
        """Return the number of chunks currently stored."""
        return len(self.chunks)
