"""Computer use tool - screen interaction via screenshots, mouse, and keyboard.

Uses xdotool for mouse/keyboard control and scrot/import for screenshots.
Works on Linux with X11. Falls back gracefully with clear error messages.
"""

import base64
import io
import os
import shutil
import subprocess
import time
from typing import Optional, Tuple

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


# Display configuration
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 768
MAX_SCREENSHOT_DIMENSION = 1568  # Anthropic's recommended max

# Typing delay to appear more natural and let UIs react
TYPING_DELAY_MS = 12
ACTION_DELAY_S = 0.5


def _get_display() -> str:
    """Get the DISPLAY environment variable."""
    return os.environ.get("DISPLAY", ":1")


def _get_screen_size() -> Tuple[int, int]:
    """Get the current screen resolution."""
    try:
        result = subprocess.run(
            ["xdpyinfo"],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, "DISPLAY": _get_display()},
        )
        for line in result.stdout.splitlines():
            if "dimensions:" in line:
                # e.g., "  dimensions:    1024x768 pixels"
                parts = line.split()
                idx = parts.index("dimensions:")
                dims = parts[idx + 1].split("x")
                return int(dims[0]), int(dims[1])
    except Exception:
        pass

    # Try xrandr as fallback
    try:
        result = subprocess.run(
            ["xrandr", "--query"],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, "DISPLAY": _get_display()},
        )
        for line in result.stdout.splitlines():
            if "*" in line:
                # e.g., "   1024x768      60.00*+"
                parts = line.strip().split()
                dims = parts[0].split("x")
                return int(dims[0]), int(dims[1])
    except Exception:
        pass

    return DEFAULT_WIDTH, DEFAULT_HEIGHT


def _scale_coordinates(x: int, y: int, from_size: Tuple[int, int],
                       to_size: Tuple[int, int]) -> Tuple[int, int]:
    """Scale coordinates from one resolution to another."""
    scale_x = to_size[0] / from_size[0]
    scale_y = to_size[1] / from_size[1]
    return int(x * scale_x), int(y * scale_y)


def take_screenshot() -> dict:
    """Capture a screenshot and return as base64 PNG.

    Returns dict with keys: success, data (base64), width, height, error
    """
    if not HAS_PILLOW:
        return {"success": False, "error": "Pillow is required for screenshots. Install with: pip install Pillow"}

    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    # Try multiple screenshot methods
    screenshot_data = None

    # Method 1: scrot
    if shutil.which("scrot"):
        try:
            result = subprocess.run(
                ["scrot", "-o", "/tmp/ai_screenshot.png"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result.returncode == 0:
                screenshot_data = "/tmp/ai_screenshot.png"
        except Exception:
            pass

    # Method 2: ImageMagick import
    if not screenshot_data and shutil.which("import"):
        try:
            result = subprocess.run(
                ["import", "-window", "root", "/tmp/ai_screenshot.png"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result.returncode == 0:
                screenshot_data = "/tmp/ai_screenshot.png"
        except Exception:
            pass

    # Method 3: xwd + convert
    if not screenshot_data and shutil.which("xwd"):
        try:
            result = subprocess.run(
                ["xwd", "-root", "-out", "/tmp/ai_screenshot.xwd"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result.returncode == 0 and shutil.which("convert"):
                subprocess.run(
                    ["convert", "/tmp/ai_screenshot.xwd", "/tmp/ai_screenshot.png"],
                    capture_output=True, timeout=10,
                )
                screenshot_data = "/tmp/ai_screenshot.png"
        except Exception:
            pass

    # Method 4: gnome-screenshot
    if not screenshot_data and shutil.which("gnome-screenshot"):
        try:
            result = subprocess.run(
                ["gnome-screenshot", "-f", "/tmp/ai_screenshot.png"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if result.returncode == 0:
                screenshot_data = "/tmp/ai_screenshot.png"
        except Exception:
            pass

    if not screenshot_data:
        return {
            "success": False,
            "error": "No screenshot tool available. Install scrot: apt install scrot",
        }

    try:
        img = Image.open(screenshot_data)
        orig_w, orig_h = img.size

        # Scale down if needed (keep aspect ratio, max dimension 1568px)
        if max(orig_w, orig_h) > MAX_SCREENSHOT_DIMENSION:
            scale = MAX_SCREENSHOT_DIMENSION / max(orig_w, orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)

        # Convert to base64 PNG
        buffer = io.BytesIO()
        img.save(buffer, format="PNG", optimize=True)
        b64_data = base64.standard_b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "success": True,
            "data": b64_data,
            "width": img.size[0],
            "height": img.size[1],
            "original_width": orig_w,
            "original_height": orig_h,
        }
    except Exception as e:
        return {"success": False, "error": f"Failed to process screenshot: {e}"}


def mouse_click(x: int, y: int, button: str = "left", click_count: int = 1) -> str:
    """Click at the given screen coordinates."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    button_map = {"left": "1", "middle": "2", "right": "3"}
    btn = button_map.get(button, "1")

    try:
        # Move mouse first
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(x), str(y)],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(0.1)

        # Click
        repeat = ["--repeat", str(click_count)] if click_count > 1 else []
        subprocess.run(
            ["xdotool", "click", "--clearmodifiers"] + repeat + [btn],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(ACTION_DELAY_S)
        return f"Clicked {button} at ({x}, {y})" + (f" x{click_count}" if click_count > 1 else "")
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error clicking: {e}"


def mouse_move(x: int, y: int) -> str:
    """Move the mouse cursor to coordinates."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    try:
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(x), str(y)],
            capture_output=True, timeout=5, env=env,
        )
        return f"Mouse moved to ({x}, {y})"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error moving mouse: {e}"


def mouse_drag(start_x: int, start_y: int, end_x: int, end_y: int) -> str:
    """Click and drag from start to end coordinates."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    try:
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(start_x), str(start_y)],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(0.1)
        subprocess.run(
            ["xdotool", "mousedown", "1"],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(0.1)
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(end_x), str(end_y)],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(0.1)
        subprocess.run(
            ["xdotool", "mouseup", "1"],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(ACTION_DELAY_S)
        return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error dragging: {e}"


def type_text(text: str) -> str:
    """Type text using the keyboard."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    try:
        subprocess.run(
            ["xdotool", "type", "--clearmodifiers", "--delay", str(TYPING_DELAY_MS), text],
            capture_output=True, timeout=30, env=env,
        )
        time.sleep(ACTION_DELAY_S)
        preview = text[:50] + "..." if len(text) > 50 else text
        return f"Typed: {preview}"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except subprocess.TimeoutExpired:
        return "Error: Typing timed out (text too long?)"
    except Exception as e:
        return f"Error typing: {e}"


def press_key(key_combo: str) -> str:
    """Press a key or key combination (e.g., 'ctrl+s', 'Return', 'alt+F4')."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    # Map common key names to xdotool names
    key_map = {
        "enter": "Return",
        "return": "Return",
        "tab": "Tab",
        "escape": "Escape",
        "esc": "Escape",
        "backspace": "BackSpace",
        "delete": "Delete",
        "space": "space",
        "up": "Up",
        "down": "Down",
        "left": "Left",
        "right": "Right",
        "home": "Home",
        "end": "End",
        "pageup": "Prior",
        "pagedown": "Next",
        "ctrl": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "super": "super",
    }

    # Process the key combo
    parts = key_combo.replace("+", " ").split()
    mapped_parts = [key_map.get(p.lower(), p) for p in parts]
    xdotool_combo = "+".join(mapped_parts)

    try:
        subprocess.run(
            ["xdotool", "key", "--clearmodifiers", xdotool_combo],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(ACTION_DELAY_S)
        return f"Pressed: {key_combo}"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error pressing key: {e}"


def scroll(x: int, y: int, direction: str = "down", amount: int = 3) -> str:
    """Scroll at the given coordinates."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    # xdotool scroll buttons: 4=up, 5=down, 6=left, 7=right
    button_map = {"up": "4", "down": "5", "left": "6", "right": "7"}
    btn = button_map.get(direction, "5")

    try:
        # Move to position first
        subprocess.run(
            ["xdotool", "mousemove", "--sync", str(x), str(y)],
            capture_output=True, timeout=5, env=env,
        )
        time.sleep(0.1)

        # Scroll
        for _ in range(amount):
            subprocess.run(
                ["xdotool", "click", btn],
                capture_output=True, timeout=5, env=env,
            )
            time.sleep(0.05)

        time.sleep(ACTION_DELAY_S)
        return f"Scrolled {direction} x{amount} at ({x}, {y})"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error scrolling: {e}"


def wait_seconds(seconds: float) -> str:
    """Wait for a specified number of seconds."""
    seconds = min(seconds, 10)  # Cap at 10 seconds
    time.sleep(seconds)
    return f"Waited {seconds} seconds"


def get_cursor_position() -> str:
    """Get the current mouse cursor position."""
    display = _get_display()
    env = {**os.environ, "DISPLAY": display}

    try:
        result = subprocess.run(
            ["xdotool", "getmouselocation"],
            capture_output=True, text=True, timeout=5, env=env,
        )
        return f"Cursor position: {result.stdout.strip()}"
    except FileNotFoundError:
        return "Error: xdotool not found. Install with: apt install xdotool"
    except Exception as e:
        return f"Error: {e}"


def check_dependencies() -> dict:
    """Check which computer use dependencies are available."""
    deps = {}
    for tool in ["xdotool", "scrot", "import", "xwd", "convert",
                  "xdpyinfo", "xrandr", "gnome-screenshot"]:
        deps[tool] = shutil.which(tool) is not None

    deps["pillow"] = HAS_PILLOW
    deps["display"] = _get_display()

    # Check if display is actually accessible
    try:
        result = subprocess.run(
            ["xdpyinfo"],
            capture_output=True, text=True, timeout=5,
            env={**os.environ, "DISPLAY": _get_display()},
        )
        deps["display_accessible"] = result.returncode == 0
    except Exception:
        deps["display_accessible"] = False

    return deps


def handle_computer_action(action: str, input_data: dict) -> dict:
    """Handle a computer use action from the API.

    Returns dict with:
      - text: str (human-readable result)
      - screenshot: optional base64 screenshot data
      - is_error: bool
    """
    result_text = ""
    should_screenshot = False
    is_error = False

    if action == "screenshot":
        should_screenshot = True
        result_text = "Screenshot captured"

    elif action == "left_click":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_click(coord[0], coord[1], "left")
        should_screenshot = True

    elif action == "right_click":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_click(coord[0], coord[1], "right")
        should_screenshot = True

    elif action == "middle_click":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_click(coord[0], coord[1], "middle")
        should_screenshot = True

    elif action == "double_click":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_click(coord[0], coord[1], "left", click_count=2)
        should_screenshot = True

    elif action == "triple_click":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_click(coord[0], coord[1], "left", click_count=3)
        should_screenshot = True

    elif action == "mouse_move":
        coord = input_data.get("coordinate", [0, 0])
        result_text = mouse_move(coord[0], coord[1])

    elif action == "left_click_drag":
        coord = input_data.get("coordinate", [0, 0])
        start = input_data.get("start_coordinate", [0, 0])
        result_text = mouse_drag(start[0], start[1], coord[0], coord[1])
        should_screenshot = True

    elif action == "type":
        text = input_data.get("text", "")
        result_text = type_text(text)
        should_screenshot = True

    elif action == "key":
        key = input_data.get("text", "")
        result_text = press_key(key)
        should_screenshot = True

    elif action == "scroll":
        coord = input_data.get("coordinate", [512, 384])
        direction = input_data.get("scroll_direction", "down")
        amount = input_data.get("scroll_amount", 3)
        result_text = scroll(coord[0], coord[1], direction, amount)
        should_screenshot = True

    elif action == "wait":
        seconds = input_data.get("duration", 1)
        result_text = wait_seconds(seconds)

    elif action == "cursor_position":
        result_text = get_cursor_position()

    else:
        result_text = f"Unknown action: {action}"
        is_error = True

    if "Error" in result_text:
        is_error = True

    # Capture a screenshot after most actions
    screenshot_result = None
    if should_screenshot and not is_error:
        time.sleep(0.3)  # Let UI update
        screenshot_result = take_screenshot()

    return {
        "text": result_text,
        "screenshot": screenshot_result,
        "is_error": is_error,
    }
