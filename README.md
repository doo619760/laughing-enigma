# AI Assistant

A super helpful CLI assistant powered by Claude, with built-in tools for everyday tasks.

## Features

- **Conversational AI** - Natural language chat powered by Claude (Opus, Sonnet, or Haiku)
- **Tool Integration** - The assistant automatically uses tools when helpful:
  - **Calculator** - Safe math evaluation with functions (sqrt, sin, log, etc.)
  - **File Reader** - Read and browse local files and directories
  - **Web Search** - Search the web and fetch webpage content
  - **Task Manager** - Persistent to-do list with priorities and statuses
  - **Code Helper** - Analyze Python code structure, count lines, find patterns, run snippets
  - **Date/Time** - Current time, date math, timezone conversions, calendars
- **Conversation History** - Automatically saves and loads past conversations
- **Streaming Responses** - Real-time token streaming for a responsive feel
- **Rich CLI** - Colorful terminal interface with formatted output

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or run the setup wizard:

```bash
ai-assistant --setup
```

### 3. Start chatting

```bash
ai-assistant
```

## Usage

### Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/new` | Start a new conversation |
| `/history` | List past conversations |
| `/load <id>` | Resume a saved conversation |
| `/tools` | List available tools |
| `/config` | Show current settings |
| `/model <name>` | Switch AI model |
| `/system <msg>` | Update system prompt |
| `/clear` | Clear the screen |
| `/quit` | Exit |

### Example Conversations

**Math:**
> "What's the square root of 144 plus 3 squared?"
> → Uses calculator tool: `sqrt(144) + 3**2` = 21

**Files:**
> "Show me what's in my project directory"
> → Uses file_reader to list and read files

**Tasks:**
> "Add a task to review the PR by Friday, high priority"
> → Creates a persistent task with priority and due date

**Code:**
> "Analyze this Python file for me: /path/to/script.py"
> → Reads the file, analyzes structure, reports classes/functions

**Web:**
> "Search for Python async best practices"
> → Searches the web and summarizes findings

**Dates:**
> "What day is 90 days from today?"
> → Calculates and returns the future date

## Configuration

Config is stored at `~/.ai_assistant/config.json`:

```json
{
  "api_key": "sk-ant-...",
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "temperature": 0.7,
  "stream_responses": true,
  "save_conversations": true
}
```

## CLI Options

```bash
ai-assistant              # Start interactive chat
ai-assistant --setup      # Run setup wizard
ai-assistant --model claude-opus-4-6  # Use Opus model
ai-assistant --no-stream  # Disable streaming
```

## Architecture

```
ai_assistant/
├── __init__.py          # Package init
├── __main__.py          # CLI entry point
├── cli.py               # Rich terminal interface
├── core/
│   ├── config.py        # Configuration management
│   ├── client.py        # Claude API client + tool orchestration
│   └── conversation.py  # Conversation history persistence
└── tools/
    ├── calculator.py    # Safe math evaluation
    ├── code_helper.py   # Code analysis and execution
    ├── datetime_tool.py # Date/time utilities
    ├── file_reader.py   # File and directory reading
    ├── task_manager.py  # Persistent task management
    └── web_search.py    # Web search and URL fetching
```

## Requirements

- Python 3.9+
- An [Anthropic API key](https://console.anthropic.com/)
