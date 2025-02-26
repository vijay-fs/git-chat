#!/usr/bin/env python3
"""
Script to clear the Git repository used by Git-Claude-Chat.
"""
import os
import sys
from pathlib import Path
import shutil
from rich.console import Console

console = Console()

def clear_repository(delete_files=False):
    """
    Clear the repository from memory and optionally delete the files from disk.
    
    Args:
        delete_files: Whether to delete the repository files from disk
    """
    # Try to load from config
    config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
    
    if not config_file.exists():
        console.print("[yellow]No repository to clear. Config file not found.")
        return
        
    # Read the repository path
    with open(config_file, "r") as f:
        repo_path = f.read().strip()
        
    if not repo_path:
        console.print("[yellow]No repository path found in config file.")
        return
        
    console.print(f"[yellow]Found repository at: {repo_path}")
    
    # Delete the files if requested
    if delete_files:
        if os.path.exists(repo_path) and os.path.isdir(repo_path):
            console.print(f"[yellow]Deleting repository files at {repo_path}...")
            try:
                shutil.rmtree(repo_path)
                console.print(f"[green]Repository files at {repo_path} have been deleted")
            except Exception as e:
                console.print(f"[red]Error deleting repository files: {e}")
                return
        else:
            console.print(f"[yellow]Repository path {repo_path} does not exist or is not a directory")
    
    # Clear the config file
    try:
        config_file.unlink()
        console.print("[green]Repository config has been cleared")
    except Exception as e:
        console.print(f"[red]Error clearing repository config: {e}")
        return

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Clear the Git repository used by Git-Claude-Chat")
    parser.add_argument("--delete", "-d", action="store_true", help="Delete the repository files from disk")
    
    args = parser.parse_args()
    
    clear_repository(delete_files=args.delete)
