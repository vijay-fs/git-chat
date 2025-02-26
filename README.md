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

## License

MIT
