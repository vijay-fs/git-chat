"""
Claude API client for Git-Claude-Chat.
"""
import os
from typing import Dict, List, Optional, Union
import anthropic
from rich.console import Console

console = Console()

class ClaudeClient:
    """Client for interacting with Claude API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude client.
        
        Args:
            api_key: Claude API key (if not provided, will look for CLAUDE_API_KEY env var)
        """
        api_key_raw = api_key or os.environ.get("CLAUDE_API_KEY")
        
        if not api_key_raw:
            raise ValueError(
                "Claude API key is required. Either pass it directly or set the CLAUDE_API_KEY environment variable."
            )
        
        # Clean the API key - remove any non-ASCII characters and whitespace
        try:
            # First try to clean by encoding/decoding with replace for non-ASCII chars
            self.api_key = api_key_raw.encode('ascii', errors='ignore').decode('ascii').strip()
            
            # If the key starts with 'sk-', make sure we keep only that part and what follows
            if 'sk-' in self.api_key:
                sk_index = self.api_key.find('sk-')
                if sk_index >= 0:
                    self.api_key = self.api_key[sk_index:]
                    
            console.print(f"[green]API key processed successfully")
        except Exception as e:
            console.print(f"[red]Error processing API key: {e}")
            raise ValueError("Invalid API key format") from e
            
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def chat_with_codebase(
        self, 
        message: str, 
        code_files: Dict[str, str],
        max_tokens: int = 4000,
        model: str = "claude-3-opus-20240229"
    ) -> str:
        """
        Chat with Claude about the codebase.
        
        Args:
            message: User's message/question about the code
            code_files: Dictionary of file paths and their contents
            max_tokens: Maximum number of tokens in the response
            model: Claude model to use
            
        Returns:
            str: Claude's response
        """
        try:
            # Prepare the system prompt
            console.print("[yellow]Preparing system prompt...")
            system_prompt = self._prepare_system_prompt(code_files)
            
            # Ensure message is properly encoded
            console.print("[yellow]Encoding user message...")
            safe_message = message.encode('utf-8', errors='replace').decode('utf-8')
            
            console.print("[yellow]Sending request to Claude API...")
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": safe_message}
                ]
            )
            return response.content[0].text
        except UnicodeEncodeError as e:
            console.print(f"[red]Encoding error: {e}")
            console.print(f"[red]Error location: {e.object[:e.start]}[bold red]→{e.object[e.start:e.end]}←[/bold red]{e.object[e.end:e.end+10]}")
            raise
        except Exception as e:
            console.print(f"[red]Error communicating with Claude API: {e}")
            console.print(f"[red]Error type: {type(e).__name__}")
            raise
    
    def _prepare_system_prompt(self, code_files: Dict[str, str]) -> str:
        """
        Prepare the system prompt with code context.
        
        Args:
            code_files: Dictionary of file paths and their contents
            
        Returns:
            str: System prompt with code context
        """
        try:
            # Start with a base system prompt
            system_prompt = """You are an expert software engineer and code assistant. 
You are analyzing a Git repository codebase. 
Your task is to help the user understand the code, answer questions about it, and provide insights.
Be thorough, accurate, and helpful in your responses.

The following files from the repository are available for your analysis:
"""
            
            # Add file list
            for file_path in code_files.keys():
                system_prompt += f"- {file_path}\n"
                
            system_prompt += "\nHere are the contents of these files:\n\n"
            
            # Add file contents with clear separators
            for file_path, content in code_files.items():
                console.print(f"[dim]Processing file: {file_path}[/dim]")
                
                # Skip very large files or binary files
                if (content.startswith("[Binary file") or 
                    content.startswith("[Large file") or 
                    content.startswith("[Error reading file") or
                    len(content) > 100000):
                    system_prompt += f"--- {file_path} ---\n{content}\n\n"
                else:
                    try:
                        # Ensure content is properly encoded
                        safe_content = content.encode('utf-8', errors='replace').decode('utf-8')
                        system_prompt += f"--- {file_path} ---\n{safe_content}\n\n"
                    except Exception as e:
                        console.print(f"[red]Error encoding file {file_path}: {e}")
                        system_prompt += f"--- {file_path} ---\n[Encoding error - content omitted]\n\n"
                    
            system_prompt += """
When answering questions:
1. Reference specific files and line numbers when relevant
2. Explain code patterns and architecture decisions
3. Provide code examples when helpful
4. If you're unsure about something, acknowledge the uncertainty
"""
            
            # Final encoding check for the entire system prompt
            try:
                system_prompt = system_prompt.encode('utf-8', errors='replace').decode('utf-8')
            except Exception as e:
                console.print(f"[red]Error in final encoding of system prompt: {e}")
                
            return system_prompt
            
        except Exception as e:
            console.print(f"[red]Error preparing system prompt: {e}")
            console.print(f"[red]Error type: {type(e).__name__}")
            raise
        
    def analyze_codebase(
        self, 
        code_files: Dict[str, str],
        max_tokens: int = 4000,
        model: str = "claude-3-opus-20240229"
    ) -> str:
        """
        Get a general analysis of the codebase.
        
        Args:
            code_files: Dictionary of file paths and their contents
            max_tokens: Maximum number of tokens in the response
            model: Claude model to use
            
        Returns:
            str: Claude's analysis
        """
        # Use the chat method with a specific analysis request
        analysis_request = """
        Please provide a high-level analysis of this codebase. Include:
        1. The main purpose and functionality
        2. Key components and their relationships
        3. Technologies and frameworks used
        4. Code organization and architecture
        5. Any notable patterns or design decisions
        """
        
        return self.chat_with_codebase(analysis_request, code_files, max_tokens, model)
