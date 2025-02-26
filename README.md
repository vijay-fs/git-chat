# Git-Claude-Chat

A Python tool that allows you to fetch a GitHub repository using the GitHub API and chat with the codebase using Claude AI. Data is stored in a local MongoDB database.

## Features

- Fetch GitHub repositories using the GitHub API
- Store repository data in MongoDB
- Analyze codebase structure
- Chat with Claude AI about the code
- Ask questions about code functionality and architecture
- List files in the repository
- Delete repositories from the database

## Requirements

- Python 3.7+
- MongoDB running locally (default: mongodb://localhost:27017/)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/git-claude-chat.git
   cd git-claude-chat
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the project root with:
   ```
   # Claude API key
   CLAUDE_API_KEY=your_claude_api_key_here

   # GitHub API token
   GITHUB_TOKEN=your_github_token_here

   # MongoDB connection
   MONGODB_URI=mongodb://localhost:27017/
   MONGODB_DB=git_claude_chat
   ```

4. Start MongoDB (if not already running):
   ```
   mongod --dbpath /path/to/data/directory
   ```

## Usage

Run the tool with:

```bash
python -m src.main [COMMAND] [OPTIONS] [ARGUMENTS]
```

Or use the CLI interface:

```bash
python -m src.main --help
```

## Commands

### Fetch Repository

Fetch a GitHub repository using the GitHub API and store it in MongoDB.

```bash
python -m src.main fetch [REPO_URL] [OPTIONS]
```

Options:
- `--owner`: Repository owner (alternative to repo_url)
- `--repo`: Repository name (alternative to repo_url)

Example:
```bash
python -m src.main fetch https://github.com/username/repo.git
# OR
python -m src.main fetch --owner username --repo repo
```

### Chat with Codebase

Ask questions about the codebase and get responses from Claude AI.

```bash
python -m src.main chat [MESSAGE] [OPTIONS]
```

Options:
- `--repo-id`: ID of the repository in MongoDB (if not specified, uses the last fetched repository)
- `--owner`: Repository owner (alternative to repo-id)
- `--repo`: Repository name (alternative to repo-id)
- `--max-files`, `-m`: Maximum number of files to include in the context (default: 20)
- `--ignore`, `-i`: Patterns to ignore when collecting files
- `--model`: Claude model to use (default: claude-3-opus-20240229)
- `--max-tokens`: Maximum number of tokens in Claude's response (default: 4000)
- `--max-context`: Maximum number of tokens to include in the context (default: 100000)

Example:
```bash
python -m src.main chat "Explain the main functionality of this codebase" --max-files 30
```

### Analyze Codebase

Get a general analysis of the codebase structure and functionality.

```bash
python -m src.main analyze [OPTIONS]
```

Options:
- `--repo-id`: ID of the repository in MongoDB (if not specified, uses the last fetched repository)
- `--owner`: Repository owner (alternative to repo-id)
- `--repo`: Repository name (alternative to repo-id)
- `--max-files`, `-m`: Maximum number of files to include in the context (default: 20)
- `--ignore`, `-i`: Patterns to ignore when collecting files
- `--model`: Claude model to use (default: claude-3-opus-20240229)
- `--max-tokens`: Maximum number of tokens in Claude's response (default: 4000)
- `--max-context`: Maximum number of tokens to include in the context (default: 100000)

Example:
```bash
python -m src.main analyze --owner username --repo repo
```

### List Files

List all files in the repository.

```bash
python -m src.main list [OPTIONS]
```

Options:
- `--repo-id`: ID of the repository in MongoDB (if not specified, uses the last fetched repository)
- `--owner`: Repository owner (alternative to repo-id)
- `--repo`: Repository name (alternative to repo-id)
- `--ignore`, `-i`: Patterns to ignore when listing files

Example:
```bash
python -m src.main list --ignore "*.md" "*.txt"
```

### Delete Repository

Delete a repository from the MongoDB database.

```bash
python -m src.main delete [OPTIONS]
```

Options:
- `--repo-id`: ID of the repository in MongoDB (if not specified, uses the last fetched repository)
- `--owner`: Repository owner (alternative to repo-id)
- `--repo`: Repository name (alternative to repo-id)
- `--force`, `-f`: Force deletion without confirmation (default: False)

Example:
```bash
python -m src.main delete --owner username --repo repo --force
```



## How It Works

### Chat Process and Data Retrieval

Git-Claude-Chat uses a sophisticated process to retrieve and analyze code from GitHub repositories:

1. **Repository Fetching**:
   - The tool uses the GitHub API to fetch repository data
   - Files are downloaded, processed, and stored in MongoDB
   - Binary files and files larger than 1MB are automatically excluded

2. **Relevant File Selection**:
   - When you ask a question, the tool analyzes your query to extract keywords
   - Files are scored based on relevance to your query using:
     - Filename matching
     - Content matching
     - File importance (e.g., configuration files, READMEs)
     - Technology-specific patterns

3. **Context Building**:
   - The most relevant files are selected (up to the specified limit)
   - File contents are retrieved from MongoDB
   - A context is built with all selected files, respecting token limits

4. **Claude AI Interaction**:
   - A system prompt is created with the repository context
   - Your query is sent to Claude AI along with the context
   - Claude analyzes the code and provides a detailed response
   - The response references specific files and code sections

5. **Performance Optimization**:
   - Files are cached in MongoDB for fast retrieval
   - Smart file selection reduces token usage
   - Configurable parameters allow fine-tuning for different repositories

This process ensures that Claude AI has the most relevant code context to answer your questions accurately, while managing token usage efficiently.

## License

MIT
