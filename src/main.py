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

# Load environment variables from .env file
load_dotenv()

app = typer.Typer(help="Git-Claude-Chat: Chat with Git repositories using Claude AI")
console = Console()

# Global state to store the current repository path
REPO_PATH = None

@app.command("clone")
def clone_repository(
    repo_url: str = typer.Argument(..., help="URL of the Git repository to clone"),
    output_path: Optional[str] = typer.Option(
        None, "--output", "-o", help="Local path to store the repository"
    ),
):
    """
    Clone a Git repository.
    """
    global REPO_PATH
    
    git_handler = GitHandler(repo_url=repo_url, local_path=output_path)
    
    try:
        REPO_PATH = git_handler.clone_repository()
        
        # Save the repository path to a config file for future use
        config_dir = Path.home() / ".git-claude-chat"
        config_dir.mkdir(exist_ok=True)
        
        with open(config_dir / "last_repo.txt", "w") as f:
            f.write(REPO_PATH)
            
        console.print(f"[green]Repository cloned successfully to {REPO_PATH}")
        console.print("[yellow]You can now use the 'chat' command to interact with the codebase")
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("chat")
def chat_with_codebase(
    message: str = typer.Argument(..., help="Message or question about the codebase"),
    repo_path: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Path to the Git repository"
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
    global REPO_PATH
    
    # Determine the repository path
    if repo_path:
        REPO_PATH = repo_path
    elif not REPO_PATH:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                REPO_PATH = f.read().strip()
        
    if not REPO_PATH:
        console.print("[red]No repository specified. Use the 'clone' command first or specify a path with --repo")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(local_path=REPO_PATH)
    
    try:
        # Get the list of files
        files = git_handler.get_file_list(ignore_patterns=ignore_patterns)
        
        if not files:
            console.print("[yellow]No files found in the repository")
            sys.exit(1)
            
        console.print(f"Repository has {len(files)} files. Using smart file selection...")
        
        # Use the FileSelector to get relevant files
        file_selector = FileSelector(REPO_PATH)
        code_files, token_count = file_selector.get_relevant_files(
            message, 
            files, 
            max_files=max_files,
            max_tokens=max_tokens_context
        )
        
        if not code_files:
            console.print("[yellow]No relevant files found for your query")
            sys.exit(1)
            
        console.print(f"[green]Selected {len(code_files)} relevant files with approximately {token_count} tokens")
            
        # Initialize the Claude client
        claude_client = ClaudeClient()
        
        console.print("[green]Sending your question to Claude...")
        
        # Get the response from Claude
        response = claude_client.chat_with_codebase(
            message, 
            code_files, 
            max_tokens=max_tokens_response,
            model=model
        )
        
        # Print the response as markdown
        console.print(Markdown(response))
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("analyze")
def analyze_codebase(
    repo_path: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Path to the Git repository"
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
    global REPO_PATH
    
    # Determine the repository path
    if repo_path:
        REPO_PATH = repo_path
    elif not REPO_PATH:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                REPO_PATH = f.read().strip()
        
    if not REPO_PATH:
        console.print("[red]No repository specified. Use the 'clone' command first or specify a path with --repo")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(local_path=REPO_PATH)
    
    try:
        # Get the list of files
        files = git_handler.get_file_list(ignore_patterns=ignore_patterns)
        
        if not files:
            console.print("[yellow]No files found in the repository")
            sys.exit(1)
            
        console.print(f"Repository has {len(files)} files. Using smart file selection...")
        
        # For analysis, we'll use a generic query that prioritizes important files
        analysis_query = "analyze code architecture structure main components"
        
        # Use the FileSelector to get relevant files
        file_selector = FileSelector(REPO_PATH)
        code_files, token_count = file_selector.get_relevant_files(
            analysis_query, 
            files, 
            max_files=max_files,
            max_tokens=max_tokens_context
        )
        
        if not code_files:
            console.print("[yellow]No relevant files found for analysis")
            sys.exit(1)
            
        console.print(f"[green]Selected {len(code_files)} relevant files with approximately {token_count} tokens")
            
        # Initialize the Claude client
        claude_client = ClaudeClient()
        
        console.print("[green]Analyzing codebase with Claude...")
        
        # Get the analysis from Claude
        analysis = claude_client.analyze_codebase(
            code_files, 
            max_tokens=max_tokens_response,
            model=model
        )
        
        # Print the analysis as markdown
        console.print(Markdown(analysis))
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

@app.command("list-files")
def list_files(
    repo_path: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Path to the Git repository"
    ),
    ignore_patterns: Optional[List[str]] = typer.Option(
        None, "--ignore", "-i", help="Patterns to ignore when listing files"
    ),
):
    """
    List all files in the repository.
    """
    global REPO_PATH
    
    # Determine the repository path
    if repo_path:
        REPO_PATH = repo_path
    elif not REPO_PATH:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                REPO_PATH = f.read().strip()
        
    if not REPO_PATH:
        console.print("[red]No repository specified. Use the 'clone' command first or specify a path with --repo")
        sys.exit(1)
        
    # Initialize the Git handler
    git_handler = GitHandler(local_path=REPO_PATH)
    
    try:
        # Get the list of files
        files = git_handler.get_file_list(ignore_patterns=ignore_patterns)
        
        if not files:
            console.print("[yellow]No files found in the repository")
            sys.exit(1)
            
        # Print the files
        console.print(f"[green]Found {len(files)} files in the repository:")
        for file in files:
            console.print(f"  {file}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    app()
