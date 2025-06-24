import os
import tempfile
import logging
import shutil
from typing import Optional
from git import Repo, GitCommandError
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class GitHubClient:
    @staticmethod
    def _normalize_repo_url(repo_url: str) -> str:
        """Normalize GitHub repository URL to HTTPS format."""
        if not repo_url:
            return repo_url
            
        # If it's an SSH URL (git@github.com:user/repo.git)
        if repo_url.startswith('git@github.com:'):
            return f"https://github.com/{repo_url.split(':', 1)[1]}"
            
        # If it's a GitHub URL without .git
        if repo_url.startswith(('https://github.com', 'http://github.com')) and not repo_url.endswith('.git'):
            return f"{repo_url}.git"
            
        return repo_url

    @classmethod
    def clone_repo(cls, repo_url: str, branch: str = "main") -> Optional[str]:
        """
        Clone a GitHub repository to a temporary directory.
        Returns the path to the cloned repository or None if failed.
        """
        temp_dir = None
        normalized_url = cls._normalize_repo_url(repo_url)
        
        logger.info(f"Cloning repository: {repo_url} (normalized: {normalized_url}), branch: {branch}")
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp(prefix="github_repo_")
            logger.debug(f"Created temp directory: {temp_dir}")
            
            # Clone the repository
            logger.info(f"Cloning {normalized_url} to {temp_dir}")
            Repo.clone_from(
                normalized_url,
                temp_dir,
                branch=branch,
                depth=1,
                single_branch=True
            )
            
            logger.info(f"Successfully cloned repository to {temp_dir}")
            return temp_dir
            
        except GitCommandError as e:
            error_msg = f"Failed to clone repository {repo_url}: {str(e)}"
            logger.error(error_msg)
            logger.debug(f"Git command error details: {e.stderr}")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error cloning {repo_url}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None

    @staticmethod
    def cleanup(repo_path: str):
        """Clean up the cloned repository directory."""
        try:
            if os.path.exists(repo_path):
                import shutil
                shutil.rmtree(repo_path)
        except Exception as e:
            print(f"Error cleaning up repository: {e}")
