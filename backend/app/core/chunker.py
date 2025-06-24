from typing import List, Dict, Any
import os

class Chunker:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_file(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """
        Split a file's content into chunks.
        Returns a list of chunks with metadata.
        """
        chunks = []
        start = 0
        content_length = len(content)
        
        while start < content_length:
            end = min(start + self.chunk_size, content_length)
            chunk_content = content[start:end]
            
            chunks.append({
                "text": chunk_content,
                "file_path": file_path,
                "start": start,
                "end": end
            })
            
            if end == content_length:
                break
                
            start = end - self.chunk_overlap
            if start >= end:  # Prevent infinite loop
                break
                
        return chunks

    def process_directory(self, dir_path: str) -> List[Dict[str, Any]]:
        """
        Recursively process all files in a directory.
        Returns a list of all chunks from all files.
        """
        all_chunks = []
        
        for root, _, files in os.walk(dir_path):
            for file in files:
                if self._should_skip_file(file):
                    continue
                    
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        chunks = self.chunk_file(file_path, content)
                        all_chunks.extend(chunks)
                except (UnicodeDecodeError, IOError) as e:
                    print(f"Error processing {file_path}: {e}")
                    continue
                    
        return all_chunks

    def _should_skip_file(self, filename: str) -> bool:
        """Determine if a file should be skipped based on its extension."""
        skip_extensions = {
            '.png', '.jpg', '.jpeg', '.gif', '.bmp',  # Images
            '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # Documents
            '.zip', '.tar', '.gz', '.rar', '.7z',     # Archives
            '.pyc', '.pyo', '.pyd', '.so', '.dll',    # Compiled files
            '.git', '.svn', '.hg', '.DS_Store'         # Version control
        }
        
        _, ext = os.path.splitext(filename)
        return ext.lower() in skip_extensions or filename.startswith('.')

# Example usage:
# chunker = Chunker()
# chunks = chunker.process_directory("/path/to/repo")
