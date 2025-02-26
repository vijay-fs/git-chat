"""
File selection algorithm for Git-Claude-Chat.
"""
import os
import re
from typing import Dict, List, Tuple
from pathlib import Path
import math
from collections import Counter
from rich.console import Console

console = Console()

class FileSelector:
    """Selects relevant files from a repository based on a query."""
    
    def __init__(self, repo_path: str):
        """
        Initialize the FileSelector.
        
        Args:
            repo_path: Path to the repository
        """
        self.repo_path = repo_path
        
    def get_relevant_files(
        self, 
        query: str, 
        all_files: List[str], 
        max_files: int = 10, 
        max_tokens: int = 100000
    ) -> Tuple[Dict[str, str], int]:
        """
        Get the most relevant files for a query.
        
        Args:
            query: User's query
            all_files: List of all files in the repository
            max_files: Maximum number of files to return
            max_tokens: Maximum number of tokens to include
            
        Returns:
            Tuple[Dict[str, str], int]: Dictionary of file paths and contents, and token count
        """
        # Extract keywords from the query
        keywords = self._extract_keywords(query)
        console.print(f"[yellow]Extracted keywords: {', '.join(keywords)}")
        
        # Score files based on relevance to keywords
        scored_files = self._score_files(all_files, keywords)
        
        # Get the top files
        relevant_files = {}
        total_tokens = 0
        
        # First, include files with exact technology matches
        tech_files = self._get_technology_specific_files(query, all_files)
        for file_path in tech_files:
            if file_path in all_files and len(relevant_files) < max_files:
                content = self._read_file(file_path)
                if content:
                    # Estimate tokens (rough approximation: 4 chars = 1 token)
                    tokens = len(content) // 4
                    if total_tokens + tokens <= max_tokens:
                        relevant_files[file_path] = content
                        total_tokens += tokens
                        console.print(f"[green]Including technology-specific file: {file_path} ({tokens} tokens)")
        
        # Then add the highest scored files
        for file_path, score in scored_files:
            if file_path not in relevant_files and len(relevant_files) < max_files:
                content = self._read_file(file_path)
                if content:
                    # Estimate tokens (rough approximation: 4 chars = 1 token)
                    tokens = len(content) // 4
                    if total_tokens + tokens <= max_tokens:
                        relevant_files[file_path] = content
                        total_tokens += tokens
                        console.print(f"[green]Including scored file: {file_path} (score: {score:.2f}, {tokens} tokens)")
        
        # Always include README and package files if they exist and we have space
        important_files = [
            f for f in all_files 
            if f.lower().endswith('readme.md') or 
               f.lower() == 'package.json' or 
               f.lower() == 'requirements.txt'
        ]
        
        for file_path in important_files:
            if file_path not in relevant_files and len(relevant_files) < max_files:
                content = self._read_file(file_path)
                if content:
                    tokens = len(content) // 4
                    if total_tokens + tokens <= max_tokens:
                        relevant_files[file_path] = content
                        total_tokens += tokens
                        console.print(f"[green]Including important file: {file_path} ({tokens} tokens)")
        
        console.print(f"[green]Selected {len(relevant_files)} files with approximately {total_tokens} tokens")
        return relevant_files, total_tokens
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        Extract keywords from a query.
        
        Args:
            query: User's query
            
        Returns:
            List[str]: List of keywords
        """
        # Convert to lowercase and remove punctuation
        query = re.sub(r'[^\w\s]', ' ', query.lower())
        
        # Split into words
        words = query.split()
        
        # Remove common stop words
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
            'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
            'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'once',
            'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
            'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't',
            'can', 'will', 'don', 'should', 'now', 'using', 'use', 'used', 'uses'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Add technology-specific keywords that might be in the query
        tech_keywords = {
            'react', 'vue', 'angular', 'node', 'express', 'django', 'flask',
            'python', 'javascript', 'typescript', 'java', 'kotlin', 'swift',
            'go', 'rust', 'c#', 'csharp', 'dotnet', 'php', 'laravel', 'ruby',
            'rails', 'mongodb', 'mongo', 'mysql', 'postgresql', 'firebase', 'aws',
            'azure', 'gcp', 'docker', 'kubernetes', 'graphql', 'rest', 'api',
            'redux', 'vuex', 'mobx', 'tensorflow', 'pytorch', 'keras',
            'scikit', 'pandas', 'numpy', 'matplotlib', 'seaborn', 'dask',
            'spark', 'hadoop', 'kafka', 'rabbitmq', 'redis', 'elasticsearch',
            'webpack', 'babel', 'vite', 'rollup', 'jest', 'mocha', 'chai',
            'cypress', 'selenium', 'puppeteer', 'storybook', 'tailwind',
            'bootstrap', 'material', 'sass', 'less', 'styled', 'emotion',
            'nextjs', 'nuxt', 'gatsby', 'svelte', 'flutter', 'react-native',
            'ionic', 'electron', 'pwa', 'webassembly', 'wasm', 'deno', 'bun',
            'groq', 'mistral', 'llama', 'claude', 'gpt', 'openai', 'huggingface',
            'transformers', 'bert', 'llm', 'rag', 'langchain', 'pinecone',
            'database', 'db', 'connect', 'connection', 'config', 'configuration',
            'setup', 'install', 'env', 'environment', 'variable'
        }
        
        # Check if any tech keywords are in the original query (case insensitive)
        query_lower = query.lower()
        for tech in tech_keywords:
            if tech in query_lower and tech not in keywords:
                keywords.append(tech)
        
        # Add related keywords for specific technologies
        if 'mongo' in query_lower or 'mongodb' in query_lower:
            related_keywords = ['database', 'db', 'connect', 'connection', 'config', 'nosql']
            for keyword in related_keywords:
                if keyword not in keywords:
                    keywords.append(keyword)
                    
        if 'laravel' in query_lower:
            related_keywords = ['php', 'framework', 'config', 'env', 'database', 'db']
            for keyword in related_keywords:
                if keyword not in keywords:
                    keywords.append(keyword)
        
        # If the query is about connecting technologies, add connection-related keywords
        if 'connect' in query_lower or 'connection' in query_lower or 'setup' in query_lower:
            related_keywords = ['config', 'configuration', 'env', 'environment', 'variable', 'setting']
            for keyword in related_keywords:
                if keyword not in keywords:
                    keywords.append(keyword)
        
        return keywords
    
    def _score_files(self, files: List[str], keywords: List[str]) -> List[Tuple[str, float]]:
        """
        Score files based on relevance to keywords.
        
        Args:
            files: List of files
            keywords: List of keywords
            
        Returns:
            List[Tuple[str, float]]: List of (file_path, score) tuples
        """
        scores = []
        
        for file_path in files:
            # Skip very large files and binary files
            full_path = os.path.join(self.repo_path, file_path)
            try:
                if os.path.getsize(full_path) > 1000000:  # Skip files larger than ~1MB
                    continue
            except Exception:
                continue
                
            # Get the file extension
            ext = Path(file_path).suffix.lower()
            
            # Skip binary files and large data files
            if ext in ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', 
                      '.woff2', '.ttf', '.eot', '.mp3', '.mp4', '.avi', '.mov',
                      '.pdf', '.zip', '.tar', '.gz', '.rar', '.7z', '.bin', '.exe',
                      '.dll', '.so', '.dylib', '.class', '.pyc', '.pyd', '.pyo']:
                continue
                
            # Read the file content
            content = self._read_file(file_path)
            if not content:
                continue
                
            # Calculate the score
            score = self._calculate_score(file_path, content, keywords)
            scores.append((file_path, score))
            
        # Sort by score in descending order
        return sorted(scores, key=lambda x: x[1], reverse=True)
    
    def _calculate_score(self, file_path: str, content: str, keywords: List[str]) -> float:
        """
        Calculate the relevance score for a file.
        
        Args:
            file_path: Path to the file
            content: Content of the file
            keywords: List of keywords
            
        Returns:
            float: Relevance score
        """
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()
        
        # Get the file name and extension
        file_name = os.path.basename(file_path).lower()
        ext = Path(file_path).suffix.lower()
        
        # Base score
        score = 0.0
        
        # Score based on file extension
        code_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.kt', '.swift',
                          '.go', '.rs', '.cs', '.php', '.rb', '.c', '.cpp', '.h', '.hpp']
        config_extensions = ['.json', '.yml', '.yaml', '.toml', '.ini', '.cfg', '.conf']
        doc_extensions = ['.md', '.txt', '.rst', '.adoc']
        
        if ext in code_extensions:
            score += 2.0
        elif ext in config_extensions:
            score += 1.5
        elif ext in doc_extensions:
            score += 1.0
            
        # Bonus for README files
        if 'readme' in file_name:
            score += 3.0
            
        # Bonus for package files
        if file_name in ['package.json', 'requirements.txt', 'pyproject.toml', 
                         'setup.py', 'pom.xml', 'build.gradle', 'gemfile']:
            score += 2.5
            
        # Bonus for main/index files
        if file_name in ['main.py', 'index.js', 'app.py', 'server.js', 'index.ts', 'app.js']:
            score += 2.0
            
        # Score based on keyword matches
        for keyword in keywords:
            # Count occurrences of the keyword
            count = content_lower.count(keyword.lower())
            
            # Higher weight for keywords in the file name
            if keyword.lower() in file_name:
                score += 3.0
                
            # Add score based on frequency
            if count > 0:
                # Use logarithmic scaling to prevent very frequent terms from dominating
                score += math.log(count + 1) * 1.5
                
        # Normalize by file size (to prevent large files from having advantage just by size)
        # But use logarithmic scaling to not overly penalize larger files
        size_factor = math.log(len(content) + 1)
        if size_factor > 0:
            score = score / math.sqrt(size_factor)
            
        return score
    
    def _get_technology_specific_files(self, query: str, all_files: List[str]) -> List[str]:
        """
        Get technology-specific files based on the query.
        
        Args:
            query: User's query
            all_files: List of all files
            
        Returns:
            List[str]: List of technology-specific files
        """
        query_lower = query.lower()
        tech_files = []
        
        # Map of technologies to relevant file patterns
        tech_patterns = {
            'react': [r'react', r'jsx', r'tsx', r'component'],
            'vue': [r'vue', r'vuex', r'nuxt'],
            'angular': [r'angular', r'ng'],
            'node': [r'node', r'express', r'server\.js'],
            'python': [r'\.py$', r'flask', r'django', r'requirements\.txt'],
            'django': [r'django', r'urls\.py', r'views\.py', r'models\.py'],
            'flask': [r'flask', r'app\.py', r'routes\.py'],
            'javascript': [r'\.js$', r'\.jsx$'],
            'typescript': [r'\.ts$', r'\.tsx$', r'tsconfig'],
            'groq': [r'groq', r'llm', r'ai'],
            'mistral': [r'mistral', r'llm', r'ai'],
            'llama': [r'llama', r'llm', r'ai'],
            'claude': [r'claude', r'anthropic', r'llm', r'ai'],
            'gpt': [r'gpt', r'openai', r'llm', r'ai'],
            'langchain': [r'langchain', r'llm', r'ai', r'rag'],
            'docker': [r'docker', r'dockerfile', r'compose'],
            'kubernetes': [r'k8s', r'kubernetes', r'helm'],
            'aws': [r'aws', r'amazon', r'lambda', r's3', r'ec2'],
            'database': [r'db', r'database', r'sql', r'mongo', r'postgres', r'\.env', r'config'],
            'api': [r'api', r'rest', r'graphql', r'endpoint'],
            'auth': [r'auth', r'login', r'jwt', r'oauth'],
            'test': [r'test', r'spec', r'jest', r'mocha', r'cypress'],
            'mongodb': [r'mongo', r'mongodb', r'nosql', r'database\.php', r'\.env', r'config'],
            'laravel': [r'laravel', r'\.env', r'config', r'database\.php', r'composer\.json'],
            'connect': [r'\.env', r'config', r'database', r'connection', r'setup'],
        }
        
        # Check if any technology is mentioned in the query
        for tech, patterns in tech_patterns.items():
            if tech in query_lower or (tech == 'mongodb' and 'mongo' in query_lower) or (tech == 'connect' and ('connect' in query_lower or 'connection' in query_lower or 'setup' in query_lower)):
                # Find files matching the patterns
                for file_path in all_files:
                    file_path_lower = file_path.lower()
                    for pattern in patterns:
                        if re.search(pattern, file_path_lower):
                            tech_files.append(file_path)
                            break
        
        # Always include important configuration files for database connections
        important_config_files = ['.env', '.env.example', 'database.php', 'config/database.php', 'config/app.php', 'composer.json']
        for file_path in all_files:
            file_name = os.path.basename(file_path)
            if file_name in important_config_files or any(config_file in file_path for config_file in important_config_files):
                tech_files.append(file_path)
        
        return list(set(tech_files))  # Remove duplicates
    
    def _read_file(self, file_path: str) -> str:
        """
        Read the contents of a file.
        
        Args:
            file_path: Path to the file relative to the repository root
            
        Returns:
            str: Contents of the file, or None if the file cannot be read
        """
        # When using MongoDB, we need to get the file content from the database
        # This method is called from get_relevant_files, which is called from chat_with_codebase
        # In chat_with_codebase, we're using git_handler.get_file_content to get the actual content
        # So here we just return a placeholder that will be replaced later
        
        # For scoring purposes, we'll return a small placeholder
        # The actual content will be fetched from MongoDB in chat_with_codebase
        return f"[File content will be fetched from MongoDB: {file_path}]"
