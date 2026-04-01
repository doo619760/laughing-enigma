"""Claude API client with tool integration."""

import json
from typing import Generator

import anthropic

from .config import Config
from .conversation import Conversation
from ..tools import calculator, file_reader, task_manager, code_helper, web_search, datetime_tool


# Registry of all available tools
TOOLS = {
    "calculator": calculator,
    "file_reader": file_reader,
    "task_manager": task_manager,
    "code_helper": code_helper,
    "web_search": web_search,
    "datetime_tool": datetime_tool,
}

TOOL_DEFINITIONS = [module.TOOL_DEFINITION for module in TOOLS.values()]


class AssistantClient:
    """Claude-powered AI assistant with tool use."""

    def __init__(self, config: Config):
        self.config = config
        self.client = anthropic.Anthropic(api_key=config.api_key)
        self.conversation = Conversation()

    def load_conversation(self, conversation_id: str):
        """Load an existing conversation."""
        self.conversation = Conversation.load(conversation_id)

    def new_conversation(self):
        """Start a fresh conversation."""
        self.conversation = Conversation()

    def _execute_tool(self, tool_name: str, tool_input: dict) -> str:
        """Execute a tool and return the result."""
        if tool_name in TOOLS:
            try:
                return TOOLS[tool_name].handle(tool_input)
            except Exception as e:
                return f"Tool error ({tool_name}): {e}"
        return f"Unknown tool: {tool_name}"

    def chat(self, user_message: str) -> Generator[dict, None, None]:
        """Send a message and yield response events.

        Yields dicts with keys:
          - {"type": "text", "content": "..."} for text chunks
          - {"type": "tool_use", "name": "...", "input": {...}} when a tool is called
          - {"type": "tool_result", "name": "...", "result": "..."} with tool output
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
        if self.config.stream_responses:
            yield from self._run_streamed(messages)
        else:
            yield from self._run_sync(messages)

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
            # Build the assistant message with all content blocks
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
                yield {"type": "tool_result", "name": tool["name"], "result": result}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": result,
                })

            # Continue the conversation with tool results
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

            # Recursive call for follow-up
            yield from self._run_turn(messages)
        else:
            # No tool use - we're done
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
                yield {"type": "tool_result", "name": block.name, "result": result}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})
            yield from self._run_turn(messages)
        else:
            self.conversation.add_message("assistant", full_text)
            if self.config.save_conversations:
                self.conversation.save()
            yield {"type": "done", "full_response": full_text}
