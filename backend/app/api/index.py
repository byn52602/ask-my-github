from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class IndexRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"

@router.post("/index")
async def index_repo(request: IndexRequest):
    """
    Index a GitHub repository by URL.
    Clones the repo, processes the files, and stores the embeddings.
    """
    try:
        # TODO: Implement repository indexing logic
        return {"status": "Indexing started", "repo_url": request.repo_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
