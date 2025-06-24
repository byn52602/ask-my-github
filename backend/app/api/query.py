import os
import logging
import uuid
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from openai import OpenAI

from ..core.retriever import Retriever

# Configure logging
logger = logging.getLogger("api.query")
logger.setLevel(logging.DEBUG)

# Configure file handler
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'api.log')

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Add console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

router = APIRouter(tags=["query"])

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not openai_client.api_key:
    logger.warning("OPENAI_API_KEY environment variable is not set")

class ChunkResponse(BaseModel):
    text: str
    file_path: str
    line_number: Optional[int] = None
    score: Optional[float] = None

class QueryRequest(BaseModel):
    question: str
    repo_url: str
    top_k: int = 3
    min_similarity: float = 0.7

class QueryResponse(BaseModel):
    answer: str
    chunks: List[ChunkResponse]

# Import shared retriever storage
from ..core.shared import get_retriever as get_shared_retriever, list_retrievers as list_shared_retrievers

def normalize_repo_url(repo_url: str) -> str:
    """Normalize repository URL for consistent storage and lookup."""
    if not repo_url:
        return repo_url
    # Remove .git if present and normalize
    repo_url = repo_url.rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    # Convert to lowercase to avoid case sensitivity issues
    return repo_url.lower()

def get_retriever(repo_url: str) -> Optional[Retriever]:
    """Get a retriever for the given repository."""
    normalized_url = normalize_repo_url(repo_url)
    logger.debug(f"Looking up retriever for URL (normalized): {normalized_url}")
    logger.debug(f"Available retrievers: {list_shared_retrievers()}")
    return get_shared_retriever(normalized_url)

def generate_answer(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Generate an answer to a question using GPT-4 based on relevant chunks.
    
    Args:
        question: The user's question
        chunks: List of relevant code chunks with metadata
        
    Returns:
        str: Generated answer or error message
    """
    try:
        # Prepare the prompt with the question and relevant chunks
        prompt = (
            "You are a helpful assistant that answers questions about code. "
            "Use the following code snippets to answer the question. "
            "If you're not sure, say so.\n\n"
            f"Question: {question}\n\n"
            "Relevant code snippets:\n"
        )
        
        # Add each chunk to the prompt with source information
        for i, chunk in enumerate(chunks, 1):
            file_path = chunk.get('file_path', 'unknown')
            content = chunk.get('text', '')
            prompt += f"\n--- Snippet {i} from {file_path} ---\n{content}\n"
        
        prompt += "\nAnswer:\n"
        
        logger.debug(f"Sending prompt to GPT-4: {prompt[:500]}...")  # Log first 500 chars
        
        # Initialize OpenAI client
        client = OpenAI()
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions about code."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        
        # Extract and return the answer
        if not response.choices or not response.choices[0].message:
            logger.error("Unexpected response format from OpenAI API")
            return "I'm sorry, I couldn't generate a proper response. Please try again."
            
        answer = response.choices[0].message.content.strip()
        logger.debug(f"Generated answer: {answer[:200]}...")  # Log first 200 chars of answer
        
        return answer
        
    except Exception as e:
        error_msg = f"Error generating answer: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return f"I'm sorry, I encountered an error while generating an answer: {str(e)}"

@router.post("/query", response_model=QueryResponse)
async def query_repo(request: QueryRequest):
    """
    Query the indexed repository with a question.
    Returns an answer and relevant code chunks.
    
    Args:
        request: The query request containing the question and repository URL
        
    Returns:
        QueryResponse containing the answer and relevant chunks
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Received query for repository: {request.repo_url}")
    logger.debug(f"[{request_id}] Question: {request.question}")
    
    # Validate input
    if not request.repo_url or not request.repo_url.strip():
        error_msg = "Repository URL is required"
        logger.error(f"[{request_id}] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    if not request.question or not request.question.strip():
        error_msg = "Question cannot be empty"
        logger.error(f"[{request_id}] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    try:
        # Get the retriever for the repository
        normalized_url = normalize_repo_url(request.repo_url)
        logger.debug(f"[{request_id}] Looking up retriever for: {normalized_url}")
        
        retriever = get_shared_retriever(normalized_url)
        if not retriever or not hasattr(retriever, 'chunks') or not retriever.chunks:
            error_msg = f"No indexed data found for repository: {request.repo_url}. Please index the repository first."
            logger.error(f"[{request_id}] {error_msg}")
            logger.debug(f"[{request_id}] Available retrievers: {list_shared_retrievers()}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        logger.info(f"[{request_id}] Found retriever with {len(retriever.chunks)} chunks")
        
        # Get relevant chunks
        logger.info(f"[{request_id}] Searching for relevant chunks...")
        try:
            chunks = retriever.get_relevant_chunks(
                query=request.question,
                top_k=request.top_k,
                min_similarity=request.min_similarity
            )
            
            if not chunks:
                logger.info(f"[{request_id}] No relevant chunks found for the question")
                return QueryResponse(
                    answer="I couldn't find any relevant information in the repository to answer your question.",
                    chunks=[]
                )
                
            logger.info(f"[{request_id}] Found {len(chunks)} relevant chunks")
            
            # Generate answer using GPT-4
            logger.info(f"[{request_id}] Generating answer...")
            answer = generate_answer(request.question, chunks)
            
            # Prepare response chunks with limited text length
            chunk_responses = []
            for chunk in chunks:
                # Limit chunk text length for response
                chunk_text = chunk.get('text', '')[:1000]  # Limit to first 1000 chars
                if len(chunk.get('text', '')) > 1000:
                    chunk_text += "... [truncated]"
                    
                chunk_responses.append(ChunkResponse(
                    text=chunk_text,
                    file_path=chunk.get('file_path', 'unknown'),
                    line_number=chunk.get('line_number'),
                    score=round(chunk.get('score', 0), 4)  # Round score to 4 decimal places
                ))
            
            logger.info(f"[{request_id}] Successfully generated response")
            return QueryResponse(
                answer=answer,
                chunks=chunk_responses
            )
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
        
    except Exception as e:
        error_msg = f"Unexpected error processing query: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your query. Please try again later."
        )