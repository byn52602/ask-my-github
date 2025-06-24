import os
import tempfile
from typing import Optional
from git import Repo, GitCommandError

class GitHubClient:
    @staticmethod
    def clone_repo(repo_url: str, branch: str = "main") -> Optional[str]:
        """
        Clone a GitHub repository to a temporary directory.
        Returns the path to the cloned repository or None if failed.
        """
        try:
            temp_dir = tempfile.mkdtemp()
            Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
            return temp_dir
        except GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
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
