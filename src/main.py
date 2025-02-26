"""
Main module for Git-Claude-Chat CLI.
"""
import os
import sys
from pathlib import Path
from typing import Optional, List
import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

from src.git_handler import GitHandler
from src.claude_client import ClaudeClient
from src.file_selector import FileSelector
from src.mongodb_handler import MongoDBHandler

# Load environment variables from .env file
# Get the directory of the current script
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(script_dir, '.env')
load_dotenv(dotenv_path)

app = typer.Typer(help="Git-Claude-Chat: Chat with GitHub repositories using Claude AI")
console = Console()

# Global state to store the current repository ID
REPO_ID = None

@app.command("fetch")
def fetch_repository(
    repo_url: str = typer.Argument(..., help="URL of the GitHub repository to fetch"),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Repository owner (alternative to repo_url)"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", help="Repository name (alternative to repo_url)"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force re-fetching even if repository already exists"
    ),
):
    """
    Fetch a GitHub repository using the GitHub API.
    """
    global REPO_ID
    
    git_handler = GitHandler(repo_url=repo_url, owner=owner, repo=repo)
    
    try:
        REPO_ID = git_handler.fetch_repository(force=force)
        
        # Save the repository ID to a config file for future use
        config_dir = Path.home() / ".git-claude-chat"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "last_repo.txt", "w") as f:
            f.write(REPO_ID)
            
        console.print(f"[green]Repository fetched successfully with ID: {REPO_ID}")
        console.print("[yellow]You can now use the 'chat' command to interact with the codebase")
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("chat")
def chat_with_codebase(
    message: str = typer.Argument(..., help="Message or question about the codebase"),
    repo_id: Optional[str] = typer.Option(
        None, "--repo-id", help="ID of the repository in MongoDB"
    ),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Repository owner"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", help="Repository name"
    ),
    max_files: int = typer.Option(
        20, "--max-files", "-m", help="Maximum number of files to include in the context"
    ),
    ignore_patterns: Optional[List[str]] = typer.Option(
        None, "--ignore", "-i", help="Patterns to ignore when collecting files"
    ),
    model: str = typer.Option(
        "claude-3-opus-20240229", "--model", help="Claude model to use"
    ),
    max_tokens_response: int = typer.Option(
        4000, "--max-tokens", help="Maximum number of tokens in Claude's response"
    ),
    max_tokens_context: int = typer.Option(
        100000, "--max-context", help="Maximum number of tokens to include in the context"
    ),
):
    """
    Chat with Claude about the codebase.
    """
    global REPO_ID
    
    # Determine the repository ID
    target_repo_id = repo_id or REPO_ID
    
    # If owner and repo are provided, try to find the repository in MongoDB
    if not target_repo_id and owner and repo:
        mongodb = MongoDBHandler()
        repo_info = mongodb.get_repository_by_name(owner, repo)
        if repo_info:
            target_repo_id = str(repo_info["_id"])
    
    if not target_repo_id:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                target_repo_id = f.read().strip()
        
    if not target_repo_id:
        console.print("[red]No repository specified. Use the 'fetch' command first or specify a repository with --repo-id, or --owner and --repo")
        sys.exit(1)
        
    # Initialize the MongoDB handler
    mongodb = MongoDBHandler()
    
    # Get repository info
    repo_info = mongodb.get_repository_info(target_repo_id)
    if not repo_info:
        console.print(f"[red]Repository with ID {target_repo_id} not found in the database")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(owner=repo_info["owner"], repo=repo_info["name"])
    git_handler.repo_id = target_repo_id
    
    try:
        # Get the list of files
        all_files = git_handler.get_all_files()
        
        if not all_files:
            console.print("[red]No files found in the repository")
            sys.exit(1)
            
        console.print(f"[green]Found {len(all_files)} files in the repository")
        
        # Initialize the file selector
        file_selector = FileSelector(repo_info["full_name"])
        
        # Get the most relevant files for the query
        console.print(f"[yellow]Selecting relevant files for: {message}")
        relevant_files, token_count = file_selector.get_relevant_files(
            message, all_files, max_files, max_tokens_context
        )
        
        if not relevant_files:
            console.print("[red]No relevant files found for the query")
            sys.exit(1)
            
        console.print(f"[green]Selected {len(relevant_files)} relevant files (approx. {token_count} tokens)")
        
        # Prepare the files dictionary for Claude
        files_dict = {}
        for file_path, _ in relevant_files.items():
            content = git_handler.get_file_content(file_path)
            if content:
                files_dict[file_path] = content
                
        # Initialize the Claude client
        claude_client = ClaudeClient()
        
        # Chat with Claude
        console.print("[yellow]Sending request to Claude...")
        response = claude_client.chat_with_codebase(
            message, files_dict, max_tokens_response, model
        )
        
        # Print the response
        console.print("\n[bold green]Claude's response:[/bold green]")
        console.print(Markdown(response))
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("analyze")
def analyze_codebase(
    repo_id: Optional[str] = typer.Option(
        None, "--repo-id", help="ID of the repository in MongoDB"
    ),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Repository owner"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", help="Repository name"
    ),
    max_files: int = typer.Option(
        20, "--max-files", "-m", help="Maximum number of files to include in the context"
    ),
    ignore_patterns: Optional[List[str]] = typer.Option(
        None, "--ignore", "-i", help="Patterns to ignore when collecting files"
    ),
    model: str = typer.Option(
        "claude-3-opus-20240229", "--model", help="Claude model to use"
    ),
    max_tokens_response: int = typer.Option(
        4000, "--max-tokens", help="Maximum number of tokens in Claude's response"
    ),
    max_tokens_context: int = typer.Option(
        100000, "--max-context", help="Maximum number of tokens to include in the context"
    ),
):
    """
    Get a general analysis of the codebase.
    """
    global REPO_ID
    
    # Determine the repository ID
    target_repo_id = repo_id or REPO_ID
    
    # If owner and repo are provided, try to find the repository in MongoDB
    if not target_repo_id and owner and repo:
        mongodb = MongoDBHandler()
        repo_info = mongodb.get_repository_by_name(owner, repo)
        if repo_info:
            target_repo_id = str(repo_info["_id"])
    
    if not target_repo_id:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                target_repo_id = f.read().strip()
        
    if not target_repo_id:
        console.print("[red]No repository specified. Use the 'fetch' command first or specify a repository with --repo-id, or --owner and --repo")
        sys.exit(1)
        
    # Initialize the MongoDB handler
    mongodb = MongoDBHandler()
    
    # Get repository info
    repo_info = mongodb.get_repository_info(target_repo_id)
    if not repo_info:
        console.print(f"[red]Repository with ID {target_repo_id} not found in the database")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(owner=repo_info["owner"], repo=repo_info["name"])
    git_handler.repo_id = target_repo_id
    
    try:
        # Get the list of files
        all_files = git_handler.get_all_files()
        
        if not all_files:
            console.print("[red]No files found in the repository")
            sys.exit(1)
            
        console.print(f"[green]Found {len(all_files)} files in the repository")
        
        # Initialize the file selector
        file_selector = FileSelector(repo_info["full_name"])
        
        # Get a representative sample of files
        console.print("[yellow]Selecting representative files for analysis...")
        relevant_files, token_count = file_selector.get_representative_files(
            all_files, max_files, max_tokens_context
        )
        
        if not relevant_files:
            console.print("[red]No relevant files found for analysis")
            sys.exit(1)
            
        console.print(f"[green]Selected {len(relevant_files)} representative files (approx. {token_count} tokens)")
        
        # Prepare the files dictionary for Claude
        files_dict = {}
        for file_path, _ in relevant_files.items():
            content = git_handler.get_file_content(file_path)
            if content:
                files_dict[file_path] = content
                
        # Initialize the Claude client
        claude_client = ClaudeClient()
        
        # Ask Claude for an analysis
        console.print("[yellow]Sending request to Claude...")
        analysis_prompt = (
            "Please analyze this codebase and provide a comprehensive overview. Include:\n"
            "1. The main purpose and functionality of the project\n"
            "2. The architecture and key components\n"
            "3. Technologies and frameworks used\n"
            "4. Code organization and patterns\n"
            "5. Potential areas for improvement\n"
        )
        
        response = claude_client.chat_with_codebase(
            analysis_prompt, files_dict, max_tokens_response, model
        )
        
        # Print the response
        console.print("\n[bold green]Codebase Analysis:[/bold green]")
        console.print(Markdown(response))
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("list")
def list_files(
    repo_id: Optional[str] = typer.Option(
        None, "--repo-id", help="ID of the repository in MongoDB"
    ),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Repository owner"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", help="Repository name"
    ),
    ignore_patterns: Optional[List[str]] = typer.Option(
        None, "--ignore", "-i", help="Patterns to ignore when listing files"
    ),
):
    """
    List all files in the repository.
    """
    global REPO_ID
    
    # Determine the repository ID
    target_repo_id = repo_id or REPO_ID
    
    # If owner and repo are provided, try to find the repository in MongoDB
    if not target_repo_id and owner and repo:
        mongodb = MongoDBHandler()
        repo_info = mongodb.get_repository_by_name(owner, repo)
        if repo_info:
            target_repo_id = str(repo_info["_id"])
    
    if not target_repo_id:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                target_repo_id = f.read().strip()
        
    if not target_repo_id:
        console.print("[red]No repository specified. Use the 'fetch' command first or specify a repository with --repo-id, or --owner and --repo")
        sys.exit(1)
        
    # Initialize the MongoDB handler
    mongodb = MongoDBHandler()
    
    # Get repository info
    repo_info = mongodb.get_repository_info(target_repo_id)
    if not repo_info:
        console.print(f"[red]Repository with ID {target_repo_id} not found in the database")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(owner=repo_info["owner"], repo=repo_info["name"])
    git_handler.repo_id = target_repo_id
    
    try:
        # Get the list of files
        all_files = git_handler.get_all_files()
        
        if not all_files:
            console.print("[red]No files found in the repository")
            sys.exit(1)
            
        # Filter files based on ignore patterns
        if ignore_patterns:
            filtered_files = []
            for file_path in all_files:
                if not any(pattern in file_path for pattern in ignore_patterns):
                    filtered_files.append(file_path)
            all_files = filtered_files
            
        # Print the files
        console.print(f"[green]Found {len(all_files)} files in the repository:")
        for file_path in sorted(all_files):
            console.print(f"  {file_path}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("delete")
def delete_repository(
    repo_id: Optional[str] = typer.Option(
        None, "--repo-id", help="ID of the repository in MongoDB"
    ),
    owner: Optional[str] = typer.Option(
        None, "--owner", help="Repository owner"
    ),
    repo: Optional[str] = typer.Option(
        None, "--repo", help="Repository name"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """
    Delete a repository from the database.
    """
    global REPO_ID
    
    # Determine the repository ID
    target_repo_id = repo_id or REPO_ID
    
    # If owner and repo are provided, try to find the repository in MongoDB
    if not target_repo_id and owner and repo:
        mongodb = MongoDBHandler()
        repo_info = mongodb.get_repository_by_name(owner, repo)
        if repo_info:
            target_repo_id = str(repo_info["_id"])
    
    if not target_repo_id:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                target_repo_id = f.read().strip()
        
    if not target_repo_id:
        console.print("[red]No repository specified. Use the 'fetch' command first or specify a repository with --repo-id, or --owner and --repo")
        sys.exit(1)
        
    # Initialize the MongoDB handler
    mongodb = MongoDBHandler()
    
    # Get repository info
    repo_info = mongodb.get_repository_info(target_repo_id)
    if not repo_info:
        console.print(f"[red]Repository with ID {target_repo_id} not found in the database")
        sys.exit(1)
        
    # Confirm deletion
    if not force:
        confirm = typer.confirm(f"Are you sure you want to delete repository {repo_info['full_name']}?")
        if not confirm:
            console.print("[yellow]Deletion cancelled")
            return
            
    try:
        # Delete the repository
        success = mongodb.delete_repository(target_repo_id)
        
        if success:
            console.print(f"[green]Repository {repo_info['full_name']} deleted successfully")
            
            # If we deleted the global repo, update it
            if REPO_ID == target_repo_id:
                REPO_ID = None
                
                # Also clear the config file if it exists
                config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
                if config_file.exists():
                    config_file.unlink()
        else:
            console.print("[red]Failed to delete repository")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    app()
