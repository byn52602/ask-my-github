import os
import logging
import tempfile
import shutil
import uuid
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel

from ..core.github_client import GitHubClient
from ..core.chunker import Chunker
from ..core.retriever import Retriever
from ..core.embedder import Embedder

# Configure logging
logger = logging.getLogger("api.index")
logger.setLevel(logging.DEBUG)

# Clear any existing handlers
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# Create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(ch)

# Also add file handler
fh = logging.FileHandler('api.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

logger.debug("Logging is configured")

# Create router with tags for OpenAPI documentation
router = APIRouter(tags=["index"])

# Import shared retriever storage
from ..core.shared import set_retriever, get_retriever as get_shared_retriever, list_retrievers as list_shared_retrievers

def normalize_repo_url(repo_url: str) -> str:
    """Normalize repository URL for consistent storage and lookup."""
    if not repo_url:
        return repo_url
    # Remove .git if present
    repo_url = repo_url.rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    # Convert to lowercase to avoid case sensitivity issues
    return repo_url.lower()

def log_request(request: Request):
    """Log incoming request details."""
    logger.debug(
        f"Request: {request.method} {request.url} | "
        f"Headers: {dict(request.headers)} | "
        f"Query params: {dict(request.query_params)}"
    )

class IndexRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "master"

class IndexResponse(BaseModel):
    status: str
    repo_url: str
    chunks_processed: int
    message: Optional[str] = None

def get_retriever(repo_url: str) -> Optional[Retriever]:
    """Get or create a retriever for the given repository URL."""
    return _retrievers.get(repo_url)

@router.post("/index", response_model=IndexResponse)
async def index_repo(
    request: Request,
    index_request: IndexRequest
):
    """
    Index a GitHub repository by URL.
    Clones the repo, processes the files, and stores the embeddings.
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Received request to index repository: {index_request.repo_url}")
    
    # Initialize variables for cleanup
    repo_dir = None
    
    try:
        # Validate the repository URL
        if not index_request.repo_url or not index_request.repo_url.strip():
            error_msg = "Repository URL is required"
            logger.error(f"[{request_id}] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Clone the repository
        logger.info(f"[{request_id}] Cloning repository: {index_request.repo_url}")
        try:
            github_client = GitHubClient()
            repo_dir = github_client.clone_repo(index_request.repo_url, index_request.branch)
            if not repo_dir or not os.path.exists(repo_dir):
                error_msg = f"Failed to clone repository: {index_request.repo_url}"
                logger.error(f"[{request_id}] {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            logger.info(f"[{request_id}] Successfully cloned repository to: {repo_dir}")
        except Exception as e:
            error_msg = f"Error cloning repository: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        logger.debug(f"[{request_id}] Initializing components")
        chunker = Chunker(chunk_size=1000, chunk_overlap=200)
        embedder = Embedder()
        retriever = Retriever(embedder=embedder)
        
        # Process files and generate chunks
        logger.info(f"[{request_id}] Processing files in repository...")
        chunks = []
        
        try:
            for root, _, files in os.walk(repo_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Skip binary files and .git directory
                        if '.git' in file_path.split(os.sep) or file_path.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip', '.tar', '.gz')):
                            continue
                            
                        # Read file content and create chunks
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                        # Get the relative file path for the chunk metadata
                        rel_path = os.path.relpath(file_path, repo_dir)
                        # Use the chunk_file method to split the content
                        file_chunks = chunker.chunk_file(
                            file_path=rel_path,
                            content=content
                        )
                        
                        # Add line numbers to chunks
                        for chunk in file_chunks:
                            chunk['line_number'] = chunk.get('start', 1)
                            chunk['text'] = content[chunk['start']:chunk['end']]
                        
                        chunks.extend(file_chunks)
                        logger.debug(f"[{request_id}] Processed {file_path}: {len(file_chunks)} chunks")
                        
                    except Exception as e:
                        logger.warning(f"[{request_id}] Error processing {file_path}: {str(e)}")
                        continue
                        
            if not chunks:
                error_msg = "No valid text files found to process in the repository."
                logger.error(f"[{request_id}] {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
                
            logger.info(f"[{request_id}] Generated {len(chunks)} chunks from repository")
            
        except Exception as e:
            error_msg = f"Error processing repository files: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
        # Generate embeddings and store retriever
        try:
            logger.info(f"[{request_id}] Generating embeddings for {len(chunks)} chunks...")
            retriever.add_chunks(chunks)
            logger.info(f"[{request_id}] Successfully generated embeddings")
            
            # Store the retriever for this repository with normalized URL
            normalized_url = normalize_repo_url(index_request.repo_url)
            set_retriever(normalized_url, retriever)
            logger.info(f"[{request_id}] Indexed repository: {normalized_url} with {len(chunks)} chunks")
            logger.debug(f"[{request_id}] Current retrievers: {list_shared_retrievers()}")
            
            return IndexResponse(
                status="success",
                repo_url=index_request.repo_url,
                chunks_processed=len(chunks),
                message=f"Successfully indexed repository with {len(chunks)} chunks"
            )
            
        except Exception as e:
            error_msg = f"Failed to generate embeddings: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )
            
    except HTTPException as he:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
        
    finally:
        # Clean up the cloned repository if it exists
        if repo_dir and os.path.exists(repo_dir):
            try:
                shutil.rmtree(repo_dir)
                logger.info(f"[{request_id}] Cleaned up repository directory: {repo_dir}")
            except Exception as e:
                logger.warning(f"[{request_id}] Error cleaning up temp dir: {str(e)}")

@router.get("/status/{repo_url}", response_model=Dict[str, Any])
async def get_index_status(repo_url: str, request: Request):
    """Check if a repository is indexed and return basic stats."""
    request_id = f"req_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"[{request_id}] Checking status for {repo_url}")
    log_request(request)
    
    try:
        # URL decode and normalize the repository URL
        decoded_repo_url = urllib.parse.unquote(repo_url)
        normalized_url = normalize_repo_url(decoded_repo_url)
        logger.debug(f"[{request_id}] Decoded repo URL: {decoded_repo_url}")
        
        # Log all current retrievers for debugging
        logger.debug(f"[{request_id}] Current retrievers: {list_shared_retrievers()}")
        
        retriever = get_shared_retriever(normalized_url)
        logger.debug(f"[{request_id}] Retriever found: {retriever is not None}")
        
        if not retriever:
            error_msg = f"[{request_id}] Repository not found: {decoded_repo_url}"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # Prepare response
        has_embeddings = bool(retriever.chunks and len(retriever.chunks) > 0 and "embedding" in retriever.chunks[0])
        response = {
            "repo_url": decoded_repo_url,
            "is_indexed": True,
            "chunks_count": len(retriever.chunks) if retriever.chunks else 0,
            "has_embeddings": has_embeddings
        }
        
        logger.info(f"[{request_id}] Status check successful for {decoded_repo_url}")
        logger.debug(f"[{request_id}] Status response: {response}")
        
        return response
        
    except HTTPException as he:
        logger.error(f"[{request_id}] HTTPException in get_index_status: {str(he)}", exc_info=True)
        raise
    except Exception as e:
        error_msg = f"[{request_id}] Error checking repository status: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )