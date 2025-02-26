"""
Git repository handling module for Git-Claude-Chat.
"""
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict
import git
from rich.console import Console
from rich.progress import Progress

console = Console()

class GitHandler:
    """Handles Git repository operations."""
    
    def __init__(self, repo_url: Optional[str] = None, local_path: Optional[str] = None):
        """
        Initialize the GitHandler.
        
        Args:
            repo_url: URL of the Git repository to clone
            local_path: Local path to store the repository
        """
        self.repo_url = repo_url
        self.local_path = local_path
        self.repo = None
        
    def clone_repository(self) -> str:
        """
        Clone the Git repository.
        
        Returns:
            str: Path to the cloned repository
        """
        if not self.repo_url:
            raise ValueError("Repository URL is required")
            
        if not self.local_path:
            # Create a temporary directory if no local path is provided
            self.local_path = tempfile.mkdtemp(prefix="git-claude-chat-")
            
        with Progress() as progress:
            task = progress.add_task(f"[green]Cloning {self.repo_url}...", total=1)
            
            try:
                self.repo = git.Repo.clone_from(self.repo_url, self.local_path)
                progress.update(task, advance=1)
                console.print(f"[green]Repository cloned successfully to {self.local_path}")
                return self.local_path
            except git.GitCommandError as e:
                console.print(f"[red]Error cloning repository: {e}")
                raise
    
    def get_file_list(self, ignore_patterns: Optional[List[str]] = None) -> List[str]:
        """
        Get a list of all files in the repository.
        
        Args:
            ignore_patterns: List of patterns to ignore
            
        Returns:
            List[str]: List of file paths
        """
        if not self.repo and self.local_path:
            try:
                self.repo = git.Repo(self.local_path)
            except git.InvalidGitRepositoryError:
                raise ValueError(f"{self.local_path} is not a valid Git repository")
                
        if not self.repo:
            raise ValueError("Repository not cloned yet")
            
        repo_path = Path(self.local_path)
        files = []
        
        default_ignore = ['.git', '__pycache__', '.pyc', '.pyo', '.pyd', '.DS_Store']
        ignore_patterns = ignore_patterns or []
        ignore_patterns.extend(default_ignore)
        
        for path in repo_path.rglob('*'):
            if path.is_file():
                rel_path = path.relative_to(repo_path)
                # Skip files matching ignore patterns
                if not any(pattern in str(rel_path) for pattern in ignore_patterns):
                    files.append(str(rel_path))
                    
        return files
    
    def read_file(self, file_path: str) -> str:
        """
        Read the contents of a file in the repository.
        
        Args:
            file_path: Path to the file relative to the repository root
            
        Returns:
            str: Contents of the file
        """
        if not self.local_path:
            raise ValueError("Repository not cloned yet")
            
        full_path = os.path.join(self.local_path, file_path)
        
        # Skip large files
        try:
            file_size = os.path.getsize(full_path)
            if file_size > 1000000:  # Skip files larger than ~1MB
                return f"[Large file: {file_size} bytes - content omitted]"
        except Exception:
            pass
            
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(full_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Ensure content is properly encoded for API transmission
                    content = content.encode('utf-8', errors='replace').decode('utf-8')
                    return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                console.print(f"[red]Error reading file {file_path}: {e}")
                return f"[Error reading file: {e}]"
                
        # If all encodings fail, treat as binary
        return "[Binary file or unsupported encoding]"
    
    def get_repo_structure(self) -> Dict:
        """
        Get the structure of the repository.
        
        Returns:
            Dict: Dictionary representing the repository structure
        """
        if not self.local_path:
            raise ValueError("Repository not cloned yet")
            
        files = self.get_file_list()
        
        structure = {}
        for file in files:
            parts = file.split('/')
            current = structure
            
            # Build the nested dictionary structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # If it's a file
                    current[part] = None
                else:  # If it's a directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
        return structure
