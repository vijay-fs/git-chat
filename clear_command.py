@app.command("clear")
def clear_repository(
    repo_path: Optional[str] = typer.Option(
        None, "--repo", "-r", help="Path to the Git repository"
    ),
    delete_files: bool = typer.Option(
        False, "--delete", "-d", help="Whether to delete the repository files from disk"
    ),
):
    """
    Clear a cloned repository from memory and optionally delete the files from disk.
    """
    global REPO_PATH
    
    # Determine the repository path
    if repo_path:
        target_repo_path = repo_path
    elif REPO_PATH:
        target_repo_path = REPO_PATH
    else:
        # Try to load from config
        config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
        if config_file.exists():
            with open(config_file, "r") as f:
                target_repo_path = f.read().strip()
        else:
            console.print("[red]No repository specified. Use the 'clone' command first or specify a path with --repo")
            sys.exit(1)
    
    # Initialize the Git handler
    git_handler = GitHandler(local_path=target_repo_path)
    
    try:
        # Clear the repository
        success = git_handler.clear_repository(delete_files=delete_files)
        
        if success:
            # If we cleared the global repo, update it
            if REPO_PATH == target_repo_path:
                REPO_PATH = None
                
                # Also clear the config file if it exists
                config_file = Path.home() / ".git-claude-chat" / "last_repo.txt"
                if config_file.exists():
                    config_file.unlink()
                    
            console.print("[green]Repository has been cleared successfully")
        else:
            console.print("[red]Failed to clear repository")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        sys.exit(1)
