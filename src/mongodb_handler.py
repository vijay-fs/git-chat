"""
MongoDB handler for Git-Claude-Chat.
"""
import os
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from rich.console import Console

console = Console()

class MongoDBHandler:
    """Handles MongoDB operations for storing repository data."""
    
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        """
        Initialize the MongoDB handler.
        
        Args:
            uri: MongoDB connection URI
            db_name: MongoDB database name
        """
        self.uri = uri or os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        self.db_name = db_name or os.environ.get("MONGODB_DB", "git_claude_chat")
        self.client = None
        self.db = None
        
        self._connect()
        
    def _connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = MongoClient(self.uri)
            self.db = self.client[self.db_name]
            console.print("[green]Connected to MongoDB successfully")
        except Exception as e:
            console.print(f"[red]Error connecting to MongoDB: {e}")
            raise
            
    def store_repository_info(self, repo_info: Dict[str, Any]) -> str:
        """
        Store repository information in MongoDB.
        
        Args:
            repo_info: Dictionary containing repository information
            
        Returns:
            str: ID of the stored repository
        """
        try:
            result = self.db.repositories.update_one(
                {"full_name": repo_info["full_name"]},
                {"$set": repo_info},
                upsert=True
            )
            
            # Get the ID of the inserted/updated document
            if result.upserted_id:
                repo_id = str(result.upserted_id)
            else:
                repo_doc = self.db.repositories.find_one({"full_name": repo_info["full_name"]})
                repo_id = str(repo_doc["_id"])
                
            console.print(f"[green]Repository information stored in MongoDB with ID: {repo_id}")
            return repo_id
        except Exception as e:
            console.print(f"[red]Error storing repository information: {e}")
            raise
            
    def store_file_content(self, repo_id: str, file_path: str, content: str) -> None:
        """
        Store file content in MongoDB.
        
        Args:
            repo_id: Repository ID
            file_path: Path of the file
            content: Content of the file
        """
        try:
            self.db.files.update_one(
                {"repo_id": repo_id, "path": file_path},
                {"$set": {"content": content}},
                upsert=True
            )
            console.print(f"[green]File content stored for {file_path}")
        except Exception as e:
            console.print(f"[red]Error storing file content: {e}")
            raise
            
    def get_repository_info(self, repo_id: str) -> Optional[Dict[str, Any]]:
        """
        Get repository information from MongoDB.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Optional[Dict[str, Any]]: Repository information or None if not found
        """
        try:
            from bson.objectid import ObjectId
            repo_info = self.db.repositories.find_one({"_id": ObjectId(repo_id)})
            return repo_info
        except Exception as e:
            console.print(f"[red]Error getting repository information: {e}")
            return None
            
    def get_repository_by_name(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get repository information by owner and repo name.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Optional[Dict[str, Any]]: Repository information or None if not found
        """
        try:
            full_name = f"{owner}/{repo}"
            repo_info = self.db.repositories.find_one({"full_name": full_name})
            return repo_info
        except Exception as e:
            console.print(f"[red]Error getting repository by name: {e}")
            return None
            
    def get_file_content(self, repo_id: str, file_path: str) -> Optional[str]:
        """
        Get file content from MongoDB.
        
        Args:
            repo_id: Repository ID
            file_path: Path of the file
            
        Returns:
            Optional[str]: File content or None if not found
        """
        try:
            file_doc = self.db.files.find_one({"repo_id": repo_id, "path": file_path})
            return file_doc["content"] if file_doc else None
        except Exception as e:
            console.print(f"[red]Error getting file content: {e}")
            return None
            
    def get_all_files(self, repo_id: str) -> List[str]:
        """
        Get all file paths for a repository.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            List[str]: List of file paths
        """
        try:
            files = self.db.files.find({"repo_id": repo_id})
            return [file["path"] for file in files]
        except Exception as e:
            console.print(f"[red]Error getting all files: {e}")
            return []
            
    def delete_repository(self, repo_id: str) -> bool:
        """
        Delete repository and its files from MongoDB.
        
        Args:
            repo_id: Repository ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            from bson.objectid import ObjectId
            # Delete repository document
            self.db.repositories.delete_one({"_id": ObjectId(repo_id)})
            
            # Delete all files associated with the repository
            self.db.files.delete_many({"repo_id": repo_id})
            
            console.print(f"[green]Repository {repo_id} and its files deleted from MongoDB")
            return True
        except Exception as e:
            console.print(f"[red]Error deleting repository: {e}")
            return False
