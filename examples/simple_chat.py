#!/usr/bin/env python3
"""
Simple example of using Git-Claude-Chat programmatically.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the parent directory to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.git_handler import GitHandler
from src.claude_client import ClaudeClient

# Load environment variables from .env file
load_dotenv()

def main():
    """Main function."""
    # Check if Claude API key is set
    if not os.environ.get("CLAUDE_API_KEY"):
        print("Error: CLAUDE_API_KEY environment variable is not set")
        print("Please set it in a .env file or export it in your shell")
        sys.exit(1)
        
    # Example repository URL
    repo_url = "https://github.com/openai/openai-python.git"
    
    # Clone the repository
    print(f"Cloning repository: {repo_url}")
    git_handler = GitHandler(repo_url=repo_url)
    repo_path = git_handler.clone_repository()
    
    # Get the list of files
    print("Getting file list...")
    files = git_handler.get_file_list()
    
    # Limit to 10 files for this example
    files = files[:10]
    print(f"Using {len(files)} files for context")
    
    # Read the contents of each file
    code_files = {}
    for file in files:
        content = git_handler.read_file(file)
        code_files[file] = content
        
    # Initialize the Claude client
    claude_client = ClaudeClient()
    
    # Example question
    question = "What is the main purpose of this library and how do I use it?"
    
    print(f"Asking Claude: {question}")
    response = claude_client.chat_with_codebase(question, code_files)
    
    print("\nClaude's response:")
    print("-" * 80)
    print(response)
    print("-" * 80)

if __name__ == "__main__":
    main()
