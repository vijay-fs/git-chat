# Git-Claude-Chat

A Python tool that allows you to fetch a Git repository and chat with the codebase using Claude AI.

## Features

- Clone Git repositories
- Analyze codebase structure
- Chat with Claude AI about the code
- Ask questions about code functionality and architecture

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
python -m src.main clone https://github.com/username/repo.git
python -m src.main chat "Explain the main functionality of this codebase"
```

Or use the CLI interface:

```bash
python -m src.main --help
```

## License

MIT
