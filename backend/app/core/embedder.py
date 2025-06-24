from typing import List, Dict, Any, Optional
import numpy as np
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

logger = logging.getLogger(__name__)

class Embedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.client = OpenAI()
        self.logger = logger.getChild(self.__class__.__name__)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using OpenAI's API.
        Implements retry logic with exponential backoff.
        """
        try:
            if not texts:
                return []
                
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            
            if not response or not hasattr(response, 'data'):
                self.logger.error("Invalid response from embeddings API")
                return []
                
            return [item.embedding for item in response.data]
            
        except Exception as e:
            self.logger.error(f"Error getting embeddings: {str(e)}", exc_info=True)
            raise

    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add embeddings to chunks of text.
        Returns chunks with their corresponding embeddings.
        """
        if not chunks:
            return []
            
        try:
            # Extract texts for embedding
            texts = []
            text_indices = []
            
            # Only process chunks that don't already have embeddings
            for i, chunk in enumerate(chunks):
                if not chunk.get("embedding"):
                    texts.append(chunk["text"])
                    text_indices.append(i)
            
            if not texts:
                self.logger.debug("No new chunks to embed")
                return chunks
            
            # Get embeddings for all texts at once
            self.logger.debug(f"Getting embeddings for {len(texts)} chunks")
            embeddings = self.get_embeddings(texts)
            
            # Add embeddings back to chunks
            for idx, embedding in zip(text_indices, embeddings):
                chunks[idx]["embedding"] = embedding
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error in embed_chunks: {str(e)}", exc_info=True)
            # Return chunks without embeddings if there's an error
            return chunks

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        a_norm = np.linalg.norm(a)
        b_norm = np.linalg.norm(b)
        if a_norm == 0 or b_norm == 0:
            return 0.0
        return np.dot(a, b) / (a_norm * b_norm)
