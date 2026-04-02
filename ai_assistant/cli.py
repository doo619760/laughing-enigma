"""Rich CLI interface for the AI Assistant with computer use support."""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .core.config import Config, APP_DIR
from .core.client import AssistantClient
from .core.conversation import Conversation
from .tools.computer_use import check_dependencies


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
  /computer      Toggle computer use mode (screen control)
  /computer deps Check computer use dependencies
  /config        Show current configuration
  /model <name>  Switch the AI model
  /system <msg>  Update the system prompt
  /clear         Clear the screen
  /quit          Exit the assistant

Computer Use Mode:
  When enabled, the assistant can see your screen, click, type,
  scroll, and interact with applications. Screenshots are saved
  to ~/.ai_assistant/screenshots/

Tips:
  - The assistant can use tools automatically (calculator, file reader, etc.)
  - Conversations are saved automatically
  - Set ANTHROPIC_API_KEY env var or run with --setup
"""


# Screenshot saving
SCREENSHOT_DIR = APP_DIR / "screenshots"


def _save_screenshot(screenshot_data: dict, label: str = "") -> Optional[str]:
    """Save a screenshot to disk and return the path."""
    if not screenshot_data or not screenshot_data.get("data"):
        return None

    try:
        import base64
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = f"_{label}" if label else ""
        filename = f"screenshot_{timestamp}{suffix}.png"
        filepath = SCREENSHOT_DIR / filename

        img_data = base64.b64decode(screenshot_data["data"])
        with open(filepath, "wb") as f:
            f.write(img_data)

        return str(filepath)
    except Exception:
        return None


def print_banner():
    """Print the welcome banner."""
    width = _get_terminal_width()
    print(_colored(BANNER, Colors.CYAN, Colors.BOLD))
    print(_colored("  Your super helpful AI assistant, powered by Claude", Colors.DIM))
    print(_colored("  Type /help for commands, /quit to exit\n", Colors.DIM))
    print(_colored("-" * min(width, 60), Colors.DIM))
    print()


def print_tool_event(event_type: str, name: str, detail: str = "",
                     screenshot: dict = None):
    """Print a tool use event with formatting."""
    if event_type == "use":
        if name == "computer":
            action = ""
            try:
                parsed = json.loads(detail) if isinstance(detail, str) else detail
                action = parsed.get("action", "")
            except (json.JSONDecodeError, AttributeError):
                action = detail

            icon = _get_computer_action_icon(action if isinstance(action, str) else "")
            print(f"\n  {_colored(f'{icon} Computer:', Colors.MAGENTA, Colors.BOLD)} "
                  f"{_colored(str(action), Colors.CYAN)}")

            # Show relevant details
            try:
                parsed = json.loads(detail) if isinstance(detail, str) else detail
                if isinstance(parsed, dict):
                    coord = parsed.get("coordinate")
                    text = parsed.get("text", "")
                    if coord:
                        print(f"  {_colored('  Position:', Colors.DIM)} ({coord[0]}, {coord[1]})")
                    if text and action in ("type", "key"):
                        preview = text[:60] + "..." if len(text) > 60 else text
                        print(f"  {_colored('  Text:', Colors.DIM)} {preview}")
            except (json.JSONDecodeError, AttributeError):
                pass
        else:
            print(f"\n  {_colored('>> Using tool:', Colors.YELLOW, Colors.BOLD)} "
                  f"{_colored(name, Colors.CYAN)}")
            if detail:
                if len(detail) > 200:
                    detail = detail[:200] + "..."
                print(f"  {_colored('  Input:', Colors.DIM)} {detail}")

    elif event_type == "result":
        if screenshot:
            saved_path = _save_screenshot(screenshot, name)
            dims = f"{screenshot.get('width', '?')}x{screenshot.get('height', '?')}"
            print(f"  {_colored('  Screenshot:', Colors.GREEN)} {dims}")
            if saved_path:
                print(f"  {_colored('  Saved:', Colors.DIM)} {saved_path}")
        elif detail:
            lines = detail.split("\n")
            if len(lines) > 8:
                detail = "\n".join(lines[:8]) + f"\n  ... ({len(lines) - 8} more lines)"
            print(f"  {_colored('  Result:', Colors.GREEN)} {detail}")
        print()


def _get_computer_action_icon(action: str) -> str:
    """Get an icon for a computer use action."""
    icons = {
        "screenshot": "[]",
        "left_click": "->",
        "right_click": "=>",
        "double_click": ">>",
        "triple_click": ">>>",
        "middle_click": "-=>",
        "mouse_move": "~~",
        "left_click_drag": "<->",
        "type": "abc",
        "key": "[K]",
        "scroll": "^v",
        "wait": "...",
        "cursor_position": "(x)",
    }
    return icons.get(action, "**")


def show_computer_deps():
    """Check and display computer use dependencies."""
    deps = check_dependencies()

    print(_colored("\nComputer Use Dependencies:\n", Colors.BOLD))

    required = [
        ("xdotool", "Mouse/keyboard control", True),
        ("pillow", "Screenshot processing", True),
    ]
    screenshot_tools = [
        ("scrot", "Screenshot capture (preferred)", False),
        ("import", "Screenshot capture (ImageMagick)", False),
        ("gnome-screenshot", "Screenshot capture (GNOME)", False),
    ]
    optional = [
        ("xdpyinfo", "Display info", False),
        ("xrandr", "Screen resolution", False),
    ]

    print(_colored("  Required:", Colors.BOLD))
    for name, desc, is_req in required:
        available = deps.get(name, False)
        status = _colored("[OK]", Colors.GREEN) if available else _colored("[MISSING]", Colors.RED)
        print(f"    {status} {name:20s} {desc}")

    has_screenshot_tool = any(deps.get(name, False) for name, _, _ in screenshot_tools)
    print(_colored("\n  Screenshot Tools (need at least one):", Colors.BOLD))
    for name, desc, _ in screenshot_tools:
        available = deps.get(name, False)
        status = _colored("[OK]", Colors.GREEN) if available else _colored("[  ]", Colors.DIM)
        print(f"    {status} {name:20s} {desc}")

    if not has_screenshot_tool:
        print(_colored("    [!] No screenshot tool found! Install scrot: apt install scrot", Colors.RED))

    print(_colored("\n  Optional:", Colors.BOLD))
    for name, desc, _ in optional:
        available = deps.get(name, False)
        status = _colored("[OK]", Colors.GREEN) if available else _colored("[  ]", Colors.DIM)
        print(f"    {status} {name:20s} {desc}")

    display = deps.get("display", ":1")
    accessible = deps.get("display_accessible", False)
    d_status = _colored("[OK]", Colors.GREEN) if accessible else _colored("[NO]", Colors.RED)
    print(f"\n  Display: {display} {d_status}")

    if not accessible:
        print(_colored("  [!] Cannot access display. Is X11 running?", Colors.RED))
        print(_colored("      Try: export DISPLAY=:0", Colors.DIM))

    print()


def run_setup(config: Config):
    """Interactive setup wizard."""
    print(_colored("\n+======================================+", Colors.CYAN))
    print(_colored("|     AI Assistant Setup Wizard        |", Colors.CYAN))
    print(_colored("+======================================+\n", Colors.CYAN))

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
    print(_colored("\n[OK] Configuration saved!\n", Colors.GREEN, Colors.BOLD))


def show_tools(computer_use_enabled: bool = False):
    """Display available tools."""
    from .core.client import TOOL_DEFINITIONS

    print(_colored("\nAvailable Tools:\n", Colors.BOLD))
    for tool in TOOL_DEFINITIONS:
        print(f"  {_colored(tool['name'], Colors.CYAN, Colors.BOLD)}")
        print(f"    {tool['description']}\n")

    # Show computer use status
    status = _colored("ENABLED", Colors.GREEN, Colors.BOLD) if computer_use_enabled \
        else _colored("disabled", Colors.DIM)
    print(f"  {_colored('computer', Colors.MAGENTA, Colors.BOLD)} [{status}]")
    print(f"    Control the screen: take screenshots, click, type, scroll,")
    print(f"    and interact with desktop applications.\n")


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


def show_config(config: Config, computer_use_enabled: bool = False):
    """Display current configuration."""
    print(_colored("\nCurrent Configuration:\n", Colors.BOLD))
    print(f"  Model:         {_colored(config.model, Colors.CYAN)}")
    print(f"  Temperature:   {_colored(str(config.temperature), Colors.CYAN)}")
    print(f"  Max tokens:    {_colored(str(config.max_tokens), Colors.CYAN)}")
    print(f"  Streaming:     {_colored(str(config.stream_responses), Colors.CYAN)}")
    cu_status = _colored("ENABLED", Colors.GREEN) if computer_use_enabled \
        else _colored("disabled", Colors.DIM)
    print(f"  Computer use:  {cu_status}")
    api_display = config.api_key[:12] + "..." if config.api_key else "(not set)"
    print(f"  API key:       {_colored(api_display, Colors.DIM)}")
    print()


def handle_command(command: str, config: Config, client: AssistantClient) -> bool:
    """Handle a slash command. Returns True if the app should continue."""
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if cmd in ("/quit", "/exit", "/q"):
        print(_colored("\nGoodbye!\n", Colors.CYAN))
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
        show_tools(client.computer_use_enabled)
    elif cmd == "/computer":
        if arg.strip().lower() == "deps":
            show_computer_deps()
        else:
            if client.computer_use_enabled:
                client.disable_computer_use()
                print(_colored("  Computer use: DISABLED\n", Colors.YELLOW))
            else:
                client.enable_computer_use()
                print(_colored("  Computer use: ENABLED", Colors.GREEN, Colors.BOLD))
                print(_colored("  The assistant can now see and control your screen.", Colors.DIM))
                print(_colored("  Screenshots saved to: ~/.ai_assistant/screenshots/", Colors.DIM))
                print(_colored("  Use /computer again to disable.\n", Colors.DIM))
    elif cmd == "/config":
        show_config(config, client.computer_use_enabled)
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
            print(_colored("\n[!] No API key configured!", Colors.RED, Colors.BOLD))
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
            # Show mode indicator in prompt
            if client.computer_use_enabled:
                mode = _colored("[SCREEN] ", Colors.MAGENTA, Colors.BOLD)
                user_input = input(mode + _colored("You: ", Colors.GREEN, Colors.BOLD)).strip()
            else:
                user_input = input(_colored("You: ", Colors.GREEN, Colors.BOLD)).strip()
        except (KeyboardInterrupt, EOFError):
            print(_colored("\n\nGoodbye!\n", Colors.CYAN))
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
                input_str = json.dumps(event["input"], indent=None)
                print_tool_event("use", event["name"], input_str)
            elif event["type"] == "tool_result":
                screenshot = event.get("screenshot")
                print_tool_event("result", event["name"], event.get("result", ""),
                                 screenshot=screenshot)
                sys.stdout.write(_colored("Assistant: ", Colors.BLUE, Colors.BOLD))
                sys.stdout.flush()
            elif event["type"] == "error":
                print(_colored(f"\n  Error: {event['message']}\n", Colors.RED))
            elif event["type"] == "done":
                pass

        print("\n")
