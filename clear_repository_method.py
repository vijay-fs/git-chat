def clear_repository(self, delete_files: bool = False) -> bool:
    """
    Clear the repository from memory and optionally delete the files from disk.
    
    Args:
        delete_files: Whether to delete the repository files from disk
        
    Returns:
        bool: True if the repository was successfully cleared, False otherwise
    """
    if not self.local_path:
        console.print("[yellow]No repository to clear")
        return False
        
    try:
        # Store the path before clearing it
        repo_path = self.local_path
        
        # Clear the repository from memory
        if self.repo:
            self.repo = None
            
        # Delete the files if requested
        if delete_files:
            import shutil
            
            with Progress() as progress:
                task = progress.add_task("[red]Deleting repository files...", total=1)
                
                # Check if the path exists and is a directory
                if os.path.exists(repo_path) and os.path.isdir(repo_path):
                    # Delete the directory and all its contents
                    shutil.rmtree(repo_path)
                    progress.update(task, advance=1)
                    console.print(f"[green]Repository files at {repo_path} have been deleted")
                else:
                    console.print(f"[yellow]Repository path {repo_path} does not exist or is not a directory")
        
        # Clear the local path
        self.local_path = None
        
        console.print("[green]Repository has been cleared from memory")
        return True
        
    except Exception as e:
        console.print(f"[red]Error clearing repository: {e}")
        return False
