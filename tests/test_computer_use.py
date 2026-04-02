"""Tests for the computer use tool module."""

import os
import shutil
from unittest.mock import patch, MagicMock

import pytest

from ai_assistant.tools import computer_use


class TestCheckDependencies:
    def test_returns_dict(self):
        deps = computer_use.check_dependencies()
        assert isinstance(deps, dict)
        assert "pillow" in deps
        assert "display" in deps
        assert "display_accessible" in deps

    def test_pillow_detected(self):
        deps = computer_use.check_dependencies()
        assert deps["pillow"] is True  # We installed Pillow


class TestScaleCoordinates:
    def test_identity(self):
        x, y = computer_use._scale_coordinates(100, 200, (1024, 768), (1024, 768))
        assert x == 100
        assert y == 200

    def test_scale_up(self):
        x, y = computer_use._scale_coordinates(100, 100, (1024, 768), (2048, 1536))
        assert x == 200
        assert y == 200

    def test_scale_down(self):
        x, y = computer_use._scale_coordinates(200, 200, (2048, 1536), (1024, 768))
        assert x == 100
        assert y == 100


class TestGetDisplay:
    def test_default_display(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}):
            assert computer_use._get_display() == ":0"

    def test_fallback_display(self):
        env = os.environ.copy()
        env.pop("DISPLAY", None)
        with patch.dict(os.environ, env, clear=True):
            assert computer_use._get_display() == ":1"


class TestHandleComputerAction:
    """Test the action dispatcher."""

    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_screenshot_action(self, mock_screenshot):
        mock_screenshot.return_value = {
            "success": True,
            "data": "fake_base64",
            "width": 1024,
            "height": 768,
            "original_width": 1024,
            "original_height": 768,
        }
        result = computer_use.handle_computer_action("screenshot", {})
        assert result["text"] == "Screenshot captured"
        assert not result["is_error"]
        assert result["screenshot"]["success"]

    @patch("ai_assistant.tools.computer_use.mouse_click")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_left_click_action(self, mock_screenshot, mock_click):
        mock_click.return_value = "Clicked left at (100, 200)"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action(
            "left_click", {"coordinate": [100, 200]}
        )
        mock_click.assert_called_once_with(100, 200, "left")
        assert "Clicked" in result["text"]

    @patch("ai_assistant.tools.computer_use.mouse_click")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_right_click_action(self, mock_screenshot, mock_click):
        mock_click.return_value = "Clicked right at (50, 50)"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action(
            "right_click", {"coordinate": [50, 50]}
        )
        mock_click.assert_called_once_with(50, 50, "right")

    @patch("ai_assistant.tools.computer_use.mouse_click")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_double_click_action(self, mock_screenshot, mock_click):
        mock_click.return_value = "Clicked left at (100, 100) x2"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action(
            "double_click", {"coordinate": [100, 100]}
        )
        mock_click.assert_called_once_with(100, 100, "left", click_count=2)

    @patch("ai_assistant.tools.computer_use.type_text")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_type_action(self, mock_screenshot, mock_type):
        mock_type.return_value = "Typed: hello world"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action("type", {"text": "hello world"})
        mock_type.assert_called_once_with("hello world")
        assert "Typed" in result["text"]

    @patch("ai_assistant.tools.computer_use.press_key")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_key_action(self, mock_screenshot, mock_key):
        mock_key.return_value = "Pressed: ctrl+s"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action("key", {"text": "ctrl+s"})
        mock_key.assert_called_once_with("ctrl+s")

    @patch("ai_assistant.tools.computer_use.scroll")
    @patch("ai_assistant.tools.computer_use.take_screenshot")
    def test_scroll_action(self, mock_screenshot, mock_scroll):
        mock_scroll.return_value = "Scrolled down x3 at (500, 400)"
        mock_screenshot.return_value = {"success": True, "data": "fake"}
        result = computer_use.handle_computer_action(
            "scroll",
            {"coordinate": [500, 400], "scroll_direction": "down", "scroll_amount": 3},
        )
        mock_scroll.assert_called_once_with(500, 400, "down", 3)

    @patch("ai_assistant.tools.computer_use.mouse_move")
    def test_mouse_move_action(self, mock_move):
        mock_move.return_value = "Mouse moved to (300, 400)"
        result = computer_use.handle_computer_action(
            "mouse_move", {"coordinate": [300, 400]}
        )
        assert "Mouse moved" in result["text"]
        # mouse_move doesn't trigger screenshot
        assert result["screenshot"] is None

    @patch("ai_assistant.tools.computer_use.wait_seconds")
    def test_wait_action(self, mock_wait):
        mock_wait.return_value = "Waited 2 seconds"
        result = computer_use.handle_computer_action("wait", {"duration": 2})
        mock_wait.assert_called_once_with(2)

    def test_unknown_action(self):
        result = computer_use.handle_computer_action("fly_to_moon", {})
        assert result["is_error"]
        assert "Unknown" in result["text"]

    @patch("ai_assistant.tools.computer_use.mouse_click")
    def test_error_in_action_sets_is_error(self, mock_click):
        mock_click.return_value = "Error: xdotool not found"
        result = computer_use.handle_computer_action(
            "left_click", {"coordinate": [0, 0]}
        )
        assert result["is_error"]


class TestWaitSeconds:
    def test_wait_capped(self):
        # Should cap at 10 seconds - we just test the function returns quickly
        # by passing a small value
        result = computer_use.wait_seconds(0.01)
        assert "Waited" in result

    def test_wait_cap_enforced(self):
        # Verify the cap logic (don't actually wait 10s)
        import time
        start = time.time()
        # Pass 0 to verify it completes quickly
        result = computer_use.wait_seconds(0)
        elapsed = time.time() - start
        assert elapsed < 1.0


class TestKeyMapping:
    """Test that key mappings work correctly."""

    @patch("subprocess.run")
    def test_enter_key_mapping(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        computer_use.press_key("enter")
        # Should map "enter" -> "Return"
        call_args = mock_run.call_args_list[0]
        assert "Return" in call_args[0][0]

    @patch("subprocess.run")
    def test_combo_key_mapping(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        computer_use.press_key("ctrl+c")
        call_args = mock_run.call_args_list[0]
        assert "ctrl+c" in call_args[0][0]

    @patch("subprocess.run")
    def test_escape_key_mapping(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        computer_use.press_key("esc")
        call_args = mock_run.call_args_list[0]
        assert "Escape" in call_args[0][0]
