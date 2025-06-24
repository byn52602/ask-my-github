from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from .embedder import Embedder

logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder or Embedder()
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: List[List[float]] = []
        self.logger = logger.getChild(self.__class__.__name__)

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunks to the retriever and generate embeddings for them.
        """
        if not chunks:
            return
            
        try:
            # Only embed chunks that don't already have embeddings
            chunks_to_embed = [c for c in chunks if not c.get("embedding")]
            
            if chunks_to_embed:
                self.embedder.embed_chunks(chunks_to_embed)
            
            # Add all chunks to our storage
            self.chunks.extend(chunks)
            self.embeddings.extend([c.get("embedding", []) for c in chunks])
            self.logger.debug(f"Added {len(chunks)} chunks to retriever")
            
        except Exception as e:
            self.logger.error(f"Error adding chunks: {str(e)}", exc_info=True)
            raise

    def _calculate_similarity(self, query_embedding: List[float], chunk_embedding: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if not query_embedding or not chunk_embedding:
            return 0.0
            
        try:
            # Convert to numpy arrays for efficient calculation
            query_vec = np.array(query_embedding)
            chunk_vec = np.array(chunk_embedding)
            
            # Calculate cosine similarity
            dot_product = np.dot(query_vec, chunk_vec)
            query_norm = np.linalg.norm(query_vec)
            chunk_norm = np.linalg.norm(chunk_vec)
            
            if query_norm == 0 or chunk_norm == 0:
                return 0.0
                
            return float(dot_product / (query_norm * chunk_norm))
            
        except Exception as e:
            self.logger.error(f"Error calculating similarity: {str(e)}", exc_info=True)
            return 0.0

    def get_relevant_chunks(
        self, 
        query: str, 
        top_k: int = 5,  # Increased from 3 to 5
        min_similarity: float = 0.3  # Lowered from 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant chunks for a given query.
        Returns a list of chunks sorted by relevance.
        """
        if not self.chunks:
            self.logger.warning("No chunks available in retriever")
            return []
            
        try:
            self.logger.debug(f"Getting relevant chunks for query: '{query}'")
            
            # Get query embedding
            query_embeddings = self.embedder.get_embeddings([query])
            if not query_embeddings:
                self.logger.warning("Failed to get query embedding")
                return []
                
            query_embedding = query_embeddings[0]
            self.logger.debug(f"Query embedding shape: {len(query_embedding) if query_embedding else 'None'}")
            
            # Calculate similarities for all chunks
            scored_chunks = []
            for i, chunk in enumerate(self.chunks):
                if 'embedding' not in chunk or not chunk['embedding']:
                    self.logger.warning(f"Chunk {i} has no embedding, skipping")
                    continue
                    
                try:
                    similarity = self._calculate_similarity(query_embedding, chunk['embedding'])
                    chunk_with_score = chunk.copy()
                    chunk_with_score['score'] = similarity
                    chunk_with_score['is_high_confidence'] = similarity >= min_similarity
                    scored_chunks.append(chunk_with_score)
                except Exception as e:
                    self.logger.warning(f"Error calculating similarity for chunk {i}: {str(e)}")
            
            if not scored_chunks:
                self.logger.warning("No chunks with valid embeddings found")
                return []
            
            # Sort by score in descending order
            scored_chunks.sort(key=lambda x: x['score'], reverse=True)
            
            # Log top 3 scores for debugging
            top_scores = [f"{c['score']:.3f}" for c in scored_chunks[:3]]
            self.logger.debug(f"Top similarity scores: {', '.join(top_scores)}")
            
            # Filter by minimum similarity if we have high confidence results
            high_confidence_chunks = [c for c in scored_chunks if c['is_high_confidence']]
            
            # If we have high confidence results, use those, otherwise use the best available
            result_chunks = high_confidence_chunks if high_confidence_chunks else scored_chunks
            
            # Return top-k chunks, but at least return something if we have anything
            return result_chunks[:top_k] if result_chunks else scored_chunks[:top_k]
            
        except Exception as e:
            self.logger.error(f"Error in get_relevant_chunks: {str(e)}", exc_info=True)
            return []

    def clear(self) -> None:
        """Clear all stored chunks and embeddings."""
        self.chunks = []
        self.embeddings = []

    def get_chunk_count(self) -> int:
        """Return the number of chunks currently stored."""
        return len(self.chunks)
