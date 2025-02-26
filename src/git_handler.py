"""
GitHub repository handling module for Git-Claude-Chat.
"""
import os
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any
import github
from github import Github
from rich.console import Console
from rich.progress import Progress

from src.mongodb_handler import MongoDBHandler

console = Console()

class GitHandler:
    """Handles GitHub repository operations."""
    
    def __init__(self, repo_url: Optional[str] = None, owner: Optional[str] = None, repo: Optional[str] = None):
        """
        Initialize the GitHandler.
        
        Args:
            repo_url: URL of the GitHub repository (e.g., 'https://github.com/username/repo')
            owner: Repository owner (alternative to repo_url)
            repo: Repository name (alternative to repo_url)
        """
        self.github_token = os.environ.get("GITHUB_TOKEN")
        if not self.github_token:
            console.print("[yellow]Warning: GITHUB_TOKEN environment variable not set. Using unauthenticated access with rate limits.")
            self.github = Github()
        else:
            self.github = Github(self.github_token)
            
        self.repo_url = repo_url
        self.owner = owner
        self.repo_name = repo
        self.repo = None
        self.repo_id = None
        
        # Parse repo_url if provided
        if repo_url and not (owner and repo):
            self._parse_repo_url()
            
        # Initialize MongoDB handler
        self.mongodb = MongoDBHandler()
        
    def _parse_repo_url(self) -> None:
        """Parse repository URL to extract owner and repo name."""
        try:
            # Handle different GitHub URL formats
            if "github.com" in self.repo_url:
                # Remove .git extension if present
                clean_url = self.repo_url.rstrip(".git")
                
                # Extract owner and repo from URL
                parts = clean_url.split("/")
                if "github.com" in parts:
                    idx = parts.index("github.com")
                    if len(parts) > idx + 2:
                        self.owner = parts[idx + 1]
                        self.repo_name = parts[idx + 2]
                else:
                    # Handle github.com/owner/repo format
                    if len(parts) >= 2:
                        self.owner = parts[-2]
                        self.repo_name = parts[-1]
            else:
                raise ValueError(f"Invalid GitHub repository URL: {self.repo_url}")
                
            console.print(f"[green]Parsed repository: {self.owner}/{self.repo_name}")
        except Exception as e:
            console.print(f"[red]Error parsing repository URL: {e}")
            raise ValueError(f"Invalid GitHub repository URL: {self.repo_url}")
            
    def fetch_repository(self, force: bool = False) -> str:
        """
        Fetch the GitHub repository data and store it in MongoDB.
        
        Args:
            force: Force re-fetching even if repository already exists
            
        Returns:
            str: ID of the repository in MongoDB
        """
        if not self.owner or not self.repo_name:
            raise ValueError("Repository owner and name are required")
            
        with Progress() as progress:
            task = progress.add_task(f"[green]Fetching repository {self.owner}/{self.repo_name}...", total=1)
            
            try:
                # Check if repository already exists in MongoDB
                existing_repo = self.mongodb.get_repository_by_name(self.owner, self.repo_name)
                if existing_repo and not force:
                    self.repo_id = str(existing_repo["_id"])
                    progress.update(task, advance=1)
                    console.print(f"[green]Repository already exists in database with ID: {self.repo_id}")
                    return self.repo_id
                
                # Fetch repository from GitHub
                self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
                
                # Store repository information in MongoDB
                repo_info = {
                    "full_name": self.repo.full_name,
                    "name": self.repo.name,
                    "owner": self.repo.owner.login,
                    "description": self.repo.description,
                    "url": self.repo.html_url,
                    "default_branch": self.repo.default_branch,
                    "language": self.repo.language,
                    "fetched_at": self.repo.updated_at.isoformat()
                }
                
                # If force is True and repository exists, delete it first
                if force and existing_repo:
                    console.print(f"[yellow]Force option specified. Deleting existing repository...")
                    self.repo_id = str(existing_repo["_id"])
                    self.mongodb.delete_repository(self.repo_id)
                
                self.repo_id = self.mongodb.store_repository_info(repo_info)
                
                # Fetch and store file contents
                self._fetch_repository_contents()
                
                progress.update(task, advance=1)
                console.print(f"[green]Repository fetched successfully with ID: {self.repo_id}")
                return self.repo_id
                
            except github.GithubException as e:
                progress.update(task, advance=1)
                console.print(f"[red]GitHub API Error: {e.status} - {e.data.get('message', '')}")
                raise
            except Exception as e:
                progress.update(task, advance=1)
                console.print(f"[red]Error: {e}")
                raise
                
    def _fetch_repository_contents(self, path: str = "") -> None:
        """
        Recursively fetch repository contents and store them in MongoDB.
        
        Args:
            path: Path within the repository to fetch
        """
        try:
            console.print(f"[blue]Fetching contents at path: {path}")
            contents = self.repo.get_contents(path)
            console.print(f"[blue]Found {len(contents)} items at path: {path}")
            
            for content in contents:
                console.print(f"[blue]Processing: {content.path} (type: {content.type})")
                
                if content.type == "dir":
                    # Recursively fetch directory contents
                    self._fetch_repository_contents(content.path)
                elif content.type == "file":
                    # Skip large files and binary files
                    if self._should_skip_file(content.path, content.size):
                        console.print(f"[yellow]Skipping file: {content.path} (size: {content.size} bytes)")
                        continue
                        
                    try:
                        # Get file content
                        console.print(f"[blue]Decoding content for: {content.path}")
                        file_content = content.decoded_content.decode('utf-8')
                        
                        # Store file content in MongoDB
                        console.print(f"[blue]Storing content for: {content.path}")
                        self.mongodb.store_file_content(self.repo_id, content.path, file_content)
                        console.print(f"[green]Successfully stored: {content.path}")
                    except UnicodeDecodeError:
                        console.print(f"[yellow]Skipping binary file: {content.path}")
                    except Exception as e:
                        console.print(f"[red]Error fetching file {content.path}: {e}")
        except github.GithubException as e:
            console.print(f"[red]GitHub API Error fetching contents at {path}: {e.status} - {e.data.get('message', '')}")
        except Exception as e:
            console.print(f"[red]Error fetching contents at {path}: {e}")
            
    def _should_skip_file(self, path: str, size: int) -> bool:
        """
        Determine if a file should be skipped based on its path and size.
        
        Args:
            path: File path
            size: File size in bytes
            
        Returns:
            bool: True if the file should be skipped, False otherwise
        """
        # Skip files larger than 1MB
        if size > 1024 * 1024:
            return True
            
        # Skip common binary file types
        binary_extensions = [
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z',
            '.exe', '.dll', '.so', '.dylib',
            '.pyc', '.pyo', '.pyd',
            '.mp3', '.mp4', '.avi', '.mov', '.flv',
            '.ttf', '.woff', '.woff2', '.eot'
        ]
        
        return any(path.lower().endswith(ext) for ext in binary_extensions)
        
    def get_file_content(self, file_path: str) -> Optional[str]:
        """
        Get the content of a file from MongoDB.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Optional[str]: File content or None if not found
        """
        if not self.repo_id:
            raise ValueError("Repository not fetched yet")
            
        return self.mongodb.get_file_content(self.repo_id, file_path)
        
    def get_all_files(self) -> List[str]:
        """
        Get all file paths in the repository from MongoDB.
        
        Returns:
            List[str]: List of file paths
        """
        if not self.repo_id:
            raise ValueError("Repository not fetched yet")
            
        return self.mongodb.get_all_files(self.repo_id)
        
    def get_repository_structure(self) -> Dict[str, Any]:
        """
        Get the repository structure as a nested dictionary.
        
        Returns:
            Dict[str, Any]: Repository structure
        """
        if not self.repo_id:
            raise ValueError("Repository not fetched yet")
            
        files = self.get_all_files()
        structure = {}
        
        for file_path in files:
            parts = file_path.split('/')
            current = structure
            
            # Build the nested structure
            for i, part in enumerate(parts):
                if i == len(parts) - 1:  # Last part (file)
                    current[part] = file_path
                else:  # Directory
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                    
        return structure
