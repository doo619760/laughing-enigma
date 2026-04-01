"""Rich CLI interface for the AI Assistant."""

import os
import sys
import shutil
from typing import Optional

from .core.config import Config
from .core.client import AssistantClient
from .core.conversation import Conversation


# ANSI color codes (no external dependency needed)
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Foreground
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Background
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"


def _colored(text: str, *codes: str) -> str:
    """Apply ANSI color codes to text."""
    if not sys.stdout.isatty():
        return text
    return "".join(codes) + text + Colors.RESET


def _get_terminal_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


BANNER = r"""
   _    ___   _            _     _              _
  /_\  |_ _| /_\   ___ ___(_)___| |_ __ _ _ __ | |_
 / _ \  | | / _ \ / __/ __| / __| __/ _` | '_ \| __|
/ ___ \ | |/ ___ \\__ \__ \ \__ \ || (_| | | | | |_
\_/ \_\___/_/   \_\___/___/_|___/\__\__,_|_| |_|\__|
"""

HELP_TEXT = """
Commands:
  /help          Show this help message
  /new           Start a new conversation
  /history       List past conversations
  /load <id>     Load a conversation by ID
  /tools         List available tools
  /config        Show current configuration
  /model <name>  Switch the AI model
  /system <msg>  Update the system prompt
  /clear         Clear the screen
  /quit          Exit the assistant

Tips:
  - The assistant can use tools automatically (calculator, file reader, etc.)
  - Conversations are saved automatically
  - Set ANTHROPIC_API_KEY env var or run with --setup
"""


def print_banner():
    """Print the welcome banner."""
    width = _get_terminal_width()
    print(_colored(BANNER, Colors.CYAN, Colors.BOLD))
    print(_colored("  Your super helpful AI assistant, powered by Claude", Colors.DIM))
    print(_colored("  Type /help for commands, /quit to exit\n", Colors.DIM))
    print(_colored("─" * min(width, 60), Colors.DIM))
    print()


def print_tool_event(event_type: str, name: str, detail: str = ""):
    """Print a tool use event with formatting."""
    if event_type == "use":
        print(f"\n  {_colored('⚡ Using tool:', Colors.YELLOW, Colors.BOLD)} {_colored(name, Colors.CYAN)}")
        if detail:
            # Truncate long tool inputs
            if len(detail) > 200:
                detail = detail[:200] + "..."
            print(f"  {_colored('  Input:', Colors.DIM)} {detail}")
    elif event_type == "result":
        # Truncate long results for display
        lines = detail.split("\n")
        if len(lines) > 8:
            detail = "\n".join(lines[:8]) + f"\n  ... ({len(lines) - 8} more lines)"
        print(f"  {_colored('  Result:', Colors.GREEN)} {detail}")
        print()


def run_setup(config: Config):
    """Interactive setup wizard."""
    print(_colored("\n╔══════════════════════════════════════╗", Colors.CYAN))
    print(_colored("║     AI Assistant Setup Wizard        ║", Colors.CYAN))
    print(_colored("╚══════════════════════════════════════╝\n", Colors.CYAN))

    # API Key
    current = config.api_key[:8] + "..." if config.api_key else "(not set)"
    print(f"Current API key: {_colored(current, Colors.DIM)}")
    key = input("Enter Anthropic API key (or press Enter to keep current): ").strip()
    if key:
        config.api_key = key

    # Model
    print(f"\nCurrent model: {_colored(config.model, Colors.CYAN)}")
    print("Available: claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5-20251001")
    model = input("Enter model name (or press Enter to keep current): ").strip()
    if model:
        config.model = model

    # Temperature
    print(f"\nCurrent temperature: {_colored(str(config.temperature), Colors.CYAN)}")
    temp = input("Enter temperature 0.0-1.0 (or press Enter to keep current): ").strip()
    if temp:
        try:
            config.temperature = max(0.0, min(1.0, float(temp)))
        except ValueError:
            print(_colored("Invalid number, keeping current value.", Colors.RED))

    # Streaming
    stream_str = "on" if config.stream_responses else "off"
    print(f"\nStreaming: {_colored(stream_str, Colors.CYAN)}")
    stream = input("Enable streaming? (y/n/Enter to keep): ").strip().lower()
    if stream in ("y", "yes"):
        config.stream_responses = True
    elif stream in ("n", "no"):
        config.stream_responses = False

    config.save()
    print(_colored("\n✓ Configuration saved!\n", Colors.GREEN, Colors.BOLD))


def show_tools():
    """Display available tools."""
    from .core.client import TOOL_DEFINITIONS

    print(_colored("\nAvailable Tools:\n", Colors.BOLD))
    for tool in TOOL_DEFINITIONS:
        print(f"  {_colored(tool['name'], Colors.CYAN, Colors.BOLD)}")
        print(f"    {tool['description']}\n")


def show_history():
    """Display conversation history."""
    conversations = Conversation.list_all()
    if not conversations:
        print(_colored("  No saved conversations yet.\n", Colors.DIM))
        return

    print(_colored("\nSaved Conversations:\n", Colors.BOLD))
    for conv in conversations[:20]:
        msg_count = conv["message_count"]
        print(
            f"  {_colored(conv['id'], Colors.CYAN)} "
            f"{conv['title'][:50]} "
            f"{_colored(f'({msg_count} msgs)', Colors.DIM)}"
        )
    print()


def show_config(config: Config):
    """Display current configuration."""
    print(_colored("\nCurrent Configuration:\n", Colors.BOLD))
    print(f"  Model:       {_colored(config.model, Colors.CYAN)}")
    print(f"  Temperature: {_colored(str(config.temperature), Colors.CYAN)}")
    print(f"  Max tokens:  {_colored(str(config.max_tokens), Colors.CYAN)}")
    print(f"  Streaming:   {_colored(str(config.stream_responses), Colors.CYAN)}")
    api_display = config.api_key[:12] + "..." if config.api_key else "(not set)"
    print(f"  API key:     {_colored(api_display, Colors.DIM)}")
    print()


def handle_command(command: str, config: Config, client: AssistantClient) -> bool:
    """Handle a slash command. Returns True if the app should continue."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        print(_colored("\nGoodbye! 👋\n", Colors.CYAN))
        return False
    elif cmd == "/help":
        print(HELP_TEXT)
    elif cmd == "/new":
        client.new_conversation()
        print(_colored("  Started new conversation.\n", Colors.GREEN))
    elif cmd == "/history":
        show_history()
    elif cmd == "/load":
        if not arg:
            print(_colored("  Usage: /load <conversation_id>\n", Colors.RED))
        else:
            try:
                client.load_conversation(arg.strip())
                print(_colored(f"  Loaded conversation: {client.conversation.title}\n", Colors.GREEN))
            except FileNotFoundError:
                print(_colored(f"  Conversation '{arg}' not found.\n", Colors.RED))
    elif cmd == "/tools":
        show_tools()
    elif cmd == "/config":
        show_config(config)
    elif cmd == "/model":
        if not arg:
            print(_colored(f"  Current model: {config.model}\n", Colors.CYAN))
        else:
            config.model = arg.strip()
            config.save()
            print(_colored(f"  Model set to: {config.model}\n", Colors.GREEN))
    elif cmd == "/system":
        if not arg:
            print(_colored(f"  Current system prompt:\n  {config.system_prompt}\n", Colors.DIM))
        else:
            config.system_prompt = arg.strip()
            config.save()
            print(_colored("  System prompt updated.\n", Colors.GREEN))
    elif cmd == "/clear":
        os.system("clear" if os.name != "nt" else "cls")
        print_banner()
    else:
        print(_colored(f"  Unknown command: {cmd}. Type /help for commands.\n", Colors.RED))

    return True


def main(setup: bool = False):
    """Main CLI entry point."""
    config = Config.load()

    if setup:
        run_setup(config)
        return

    # Check for API key
    if not config.api_key:
        env_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if env_key:
            config.api_key = env_key
            config.save()
        else:
            print(_colored("\n⚠  No API key configured!", Colors.RED, Colors.BOLD))
            print("Set the ANTHROPIC_API_KEY environment variable, or run:")
            print(_colored("  ai-assistant --setup\n", Colors.CYAN))
            run_setup(config)
            if not config.api_key:
                print(_colored("Cannot proceed without an API key.\n", Colors.RED))
                sys.exit(1)

    client = AssistantClient(config)

    print_banner()

    while True:
        try:
            # Prompt
            user_input = input(_colored("You: ", Colors.GREEN, Colors.BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print(_colored("\n\nGoodbye! 👋\n", Colors.CYAN))
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            if not handle_command(user_input, config, client):
                break
            continue

        # Send to Claude
        print()
        sys.stdout.write(_colored("Assistant: ", Colors.BLUE, Colors.BOLD))
        sys.stdout.flush()

        full_response = ""
        for event in client.chat(user_input):
            if event["type"] == "text":
                sys.stdout.write(event["content"])
                sys.stdout.flush()
                full_response += event["content"]
            elif event["type"] == "tool_use":
                import json
                input_str = json.dumps(event["input"], indent=None)
                print_tool_event("use", event["name"], input_str)
            elif event["type"] == "tool_result":
                print_tool_event("result", event["name"], event["result"])
                sys.stdout.write(_colored("Assistant: ", Colors.BLUE, Colors.BOLD))
                sys.stdout.flush()
            elif event["type"] == "error":
                print(_colored(f"\n  Error: {event['message']}\n", Colors.RED))
            elif event["type"] == "done":
                pass

        print("\n")
