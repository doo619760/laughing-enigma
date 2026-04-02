"""Claude API client with tool integration and computer use support."""

import json
from typing import Generator

import anthropic

from .config import Config
from .conversation import Conversation
from ..tools import calculator, file_reader, task_manager, code_helper, web_search, datetime_tool
from ..tools import computer_use


# Registry of all standard tools
TOOLS = {
    "calculator": calculator,
    "file_reader": file_reader,
    "task_manager": task_manager,
    "code_helper": code_helper,
    "web_search": web_search,
    "datetime_tool": datetime_tool,
}

TOOL_DEFINITIONS = [module.TOOL_DEFINITION for module in TOOLS.values()]

# Computer use beta configuration
COMPUTER_USE_BETA = "computer-use-2025-01-24"
COMPUTER_USE_TOOL_TYPE = "computer_20250124"


class AssistantClient:
    """Claude-powered AI assistant with tool use and computer control."""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.conversation = Conversation()
        self.computer_use_enabled = False
        self._screen_size = (1024, 768)

    def load_conversation(self, conversation_id: str):
        """Load an existing conversation."""
        self.conversation = Conversation.load(conversation_id)

    def new_conversation(self):
        """Start a fresh conversation."""
        self.conversation = Conversation()

    def enable_computer_use(self):
        """Enable computer use mode."""
        self.computer_use_enabled = True
        self._screen_size = computer_use._get_screen_size()

    def disable_computer_use(self):
        """Disable computer use mode."""
        self.computer_use_enabled = False

    def _get_tools(self) -> list:
        """Get the tool definitions for the current mode."""
        tools = list(TOOL_DEFINITIONS)
        if self.computer_use_enabled:
            tools.append({
                "type": COMPUTER_USE_TOOL_TYPE,
                "name": "computer",
                "display_width_px": self._screen_size[0],
                "display_height_px": self._screen_size[1],
            })
        return tools

    def _get_betas(self) -> list:
        """Get beta flags if needed."""
        if self.computer_use_enabled:
            return [COMPUTER_USE_BETA]
        return []

    def _execute_tool(self, tool_name: str, tool_input: dict) -> dict:
        """Execute a tool and return the result.

        Returns either a string or a list of content blocks (for screenshots).
        """
        if tool_name == "computer":
            return self._execute_computer_action(tool_input)

        if tool_name in TOOLS:
            try:
                return {"text": TOOLS[tool_name].handle(tool_input)}
            except Exception as e:
                return {"text": f"Tool error ({tool_name}): {e}", "is_error": True}

        return {"text": f"Unknown tool: {tool_name}", "is_error": True}

    def _execute_computer_action(self, tool_input: dict) -> dict:
        """Execute a computer use action and return result with optional screenshot."""
        action = tool_input.get("action", "screenshot")
        result = computer_use.handle_computer_action(action, tool_input)

        response = {
            "text": result["text"],
            "is_error": result.get("is_error", False),
        }

        # Include screenshot data if available
        if result.get("screenshot") and result["screenshot"].get("success"):
            response["screenshot"] = result["screenshot"]

        return response

    def _build_tool_result_content(self, tool_name: str, result: dict) -> list:
        """Build the content blocks for a tool result message."""
        content = []

        # Add screenshot image if present
        if "screenshot" in result and result["screenshot"]:
            ss = result["screenshot"]
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": ss["data"],
                },
            })

        # Add text
        if result.get("text"):
            content.append({"type": "text", "text": result["text"]})

        # If no content blocks, return just the text
        if not content:
            return result.get("text", "No result")

        return content

    def chat(self, user_message: str) -> Generator[dict, None, None]:
        """Send a message and yield response events.

        Yields dicts with keys:
          - {"type": "text", "content": "..."} for text chunks
          - {"type": "tool_use", "name": "...", "input": {...}} when a tool is called
          - {"type": "tool_result", "name": "...", "result": "...", "screenshot": ...}
          - {"type": "done", "full_response": "..."} when complete
          - {"type": "error", "message": "..."} on errors
        """
        self.conversation.add_message("user", user_message)

        messages = self.conversation.get_api_messages(self.config.max_history_messages)

        try:
            yield from self._run_turn(messages)
        except anthropic.APIError as e:
            error_msg = f"API Error: {e.message}"
            yield {"type": "error", "message": error_msg}
        except anthropic.AuthenticationError:
            yield {"type": "error", "message": "Invalid API key. Run 'ai-assistant --setup' to configure."}

    def _run_turn(self, messages: list) -> Generator[dict, None, None]:
        """Run a single API turn, handling tool use recursively."""
        # Computer use requires the beta API without streaming
        if self.computer_use_enabled:
            yield from self._run_computer_use(messages)
        elif self.config.stream_responses:
            yield from self._run_streamed(messages)
        else:
            yield from self._run_sync(messages)

    def _run_computer_use(self, messages: list) -> Generator[dict, None, None]:
        """Run with computer use beta API (no streaming for beta)."""
        tools = self._get_tools()
        betas = self._get_betas()

        response = self.client.beta.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=messages,
            tools=tools,
            betas=betas,
            temperature=self.config.temperature,
        )

        full_text = ""
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                full_text += block.text
                yield {"type": "text", "content": block.text}
            elif block.type == "tool_use":
                tool_uses.append(block)

        if tool_uses:
            # Build assistant response content
            assistant_content = []
            if full_text:
                assistant_content.append({"type": "text", "text": full_text})

            tool_results = []
            for block in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

                yield {"type": "tool_use", "name": block.name, "input": block.input}

                # Execute the tool
                result = self._execute_tool(block.name, block.input)
                content = self._build_tool_result_content(block.name, result)

                yield {
                    "type": "tool_result",
                    "name": block.name,
                    "result": result.get("text", ""),
                    "screenshot": result.get("screenshot"),
                }

                tool_result_msg = {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": content,
                }
                if result.get("is_error"):
                    tool_result_msg["is_error"] = True

                tool_results.append(tool_result_msg)

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Continue the loop
            yield from self._run_turn(messages)
        else:
            self.conversation.add_message("assistant", full_text)
            if self.config.save_conversations:
                self.conversation.save()
            yield {"type": "done", "full_response": full_text}

    def _run_streamed(self, messages: list) -> Generator[dict, None, None]:
        """Run with streaming enabled."""
        full_text = ""
        tool_uses = []

        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=self.config.temperature,
        ) as stream:
            for event in stream:
                if event.type == "content_block_start":
                    if hasattr(event.content_block, "text"):
                        pass  # Text block starting
                    elif hasattr(event.content_block, "name"):
                        tool_uses.append({
                            "id": event.content_block.id,
                            "name": event.content_block.name,
                            "input_json": "",
                        })
                elif event.type == "content_block_delta":
                    if hasattr(event.delta, "text"):
                        full_text += event.delta.text
                        yield {"type": "text", "content": event.delta.text}
                    elif hasattr(event.delta, "partial_json"):
                        if tool_uses:
                            tool_uses[-1]["input_json"] += event.delta.partial_json

        # Handle tool use if any
        if tool_uses:
            assistant_content = []
            if full_text:
                assistant_content.append({"type": "text", "text": full_text})

            tool_results = []
            for tool in tool_uses:
                try:
                    tool_input = json.loads(tool["input_json"]) if tool["input_json"] else {}
                except json.JSONDecodeError:
                    tool_input = {}

                assistant_content.append({
                    "type": "tool_use",
                    "id": tool["id"],
                    "name": tool["name"],
                    "input": tool_input,
                })

                yield {"type": "tool_use", "name": tool["name"], "input": tool_input}

                result = self._execute_tool(tool["name"], tool_input)
                yield {
                    "type": "tool_result",
                    "name": tool["name"],
                    "result": result.get("text", str(result)),
                }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": result.get("text", str(result)),
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            yield from self._run_turn(messages)
        else:
            self.conversation.add_message("assistant", full_text)
            if self.config.save_conversations:
                self.conversation.save()
            yield {"type": "done", "full_response": full_text}

    def _run_sync(self, messages: list) -> Generator[dict, None, None]:
        """Run without streaming."""
        response = self.client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            system=self.config.system_prompt,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=self.config.temperature,
        )

        full_text = ""
        tool_uses = []

        for block in response.content:
            if block.type == "text":
                full_text += block.text
                yield {"type": "text", "content": block.text}
            elif block.type == "tool_use":
                tool_uses.append(block)

        if tool_uses:
            assistant_content = []
            if full_text:
                assistant_content.append({"type": "text", "text": full_text})

            tool_results = []
            for block in tool_uses:
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })

                yield {"type": "tool_use", "name": block.name, "input": block.input}

                result = self._execute_tool(block.name, block.input)
                yield {
                    "type": "tool_result",
                    "name": block.name,
                    "result": result.get("text", str(result)),
                }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result.get("text", str(result)),
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            yield from self._run_turn(messages)
        else:
            self.conversation.add_message("assistant", full_text)
            if self.config.save_conversations:
                self.conversation.save()
            yield {"type": "done", "full_response": full_text}
