# Git-Claude-Chat

A Python tool that allows you to fetch a Git repository and chat with the codebase using Claude AI.

## Features

- Clone Git repositories
- Analyze codebase structure
- Chat with Claude AI about the code
- Ask questions about code functionality and architecture
- List files in the repository
- Clear repository from memory

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

3. Set up your Claude API key:
   Create a `.env` file in the project root with:
   ```
   CLAUDE_API_KEY=your_api_key_here
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

### Clone Repository

Clone a Git repository to your local machine.

```bash
python -m src.main clone [REPO_URL] [OPTIONS]
```

Options:
- `--output`, `-o`: Local path to store the repository

Example:
```bash
python -m src.main clone https://github.com/username/repo.git --output ./my-repo
```

### Chat with Codebase

Ask questions about the codebase and get responses from Claude AI.

```bash
python -m src.main chat [MESSAGE] [OPTIONS]
```

Options:
- `--repo`, `-r`: Path to the Git repository (if not specified, uses the last cloned repository)
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
- `--repo`, `-r`: Path to the Git repository (if not specified, uses the last cloned repository)
- `--max-files`, `-m`: Maximum number of files to include in the context (default: 20)
- `--ignore`, `-i`: Patterns to ignore when collecting files
- `--model`: Claude model to use (default: claude-3-opus-20240229)
- `--max-tokens`: Maximum number of tokens in Claude's response (default: 4000)
- `--max-context`: Maximum number of tokens to include in the context (default: 100000)

Example:
```bash
python -m src.main analyze --repo ./my-repo
```

### List Files

List all files in the repository.

```bash
python -m src.main list [OPTIONS]
```

Options:
- `--repo`, `-r`: Path to the Git repository (if not specified, uses the last cloned repository)
- `--ignore`, `-i`: Patterns to ignore when listing files

Example:
```bash
python -m src.main list --ignore "*.md" "*.txt"
```

### Clear Repository

Clear a cloned repository from memory and optionally delete the files from disk.

```bash
python -m src.main clear [OPTIONS]
```

Options:
- `--repo`, `-r`: Path to the Git repository (if not specified, uses the last cloned repository)
- `--delete`, `-d`: Whether to delete the repository files from disk (default: False)

Example:
```bash
python -m src.main clear --delete
```

## License

MIT
