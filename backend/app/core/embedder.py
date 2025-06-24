from typing import List, Dict, Any
import numpy as np
import openai
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class Embedder:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        self.model_name = model_name
        self.client = OpenAI()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts using OpenAI's API.
        Implements retry logic with exponential backoff.
        """
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model_name
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"Error getting embeddings: {e}")
            raise

    async def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add embeddings to chunks of text.
        Returns chunks with their corresponding embeddings.
        """
        if not chunks:
            return []
            
        # Extract texts for embedding
        texts = [chunk["text"] for chunk in chunks]
        
        try:
            # Get embeddings
            embeddings = await self.get_embeddings(texts)
            
            # Add embeddings to chunks
            for i, embedding in enumerate(embeddings):
                chunks[i]["embedding"] = embedding
                
            return chunks
            
        except Exception as e:
            print(f"Error embedding chunks: {e}")
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
