"""Entry point for running as: python -m ai_assistant"""

import argparse
import sys

from .cli import main


def entry():
    parser = argparse.ArgumentParser(
        description="AI Assistant - A super helpful CLI assistant powered by Claude",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-assistant              Start interactive chat
  ai-assistant --setup      Configure API key and settings
  ai-assistant --model claude-opus-4-6  Use a specific model

Environment:
  ANTHROPIC_API_KEY         Your Anthropic API key
""",
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="Run the setup wizard to configure API key and settings",
    )
    parser.add_argument(
        "--model", type=str,
        help="Override the model for this session",
    )
    parser.add_argument(
        "--no-stream", action="store_true",
        help="Disable response streaming",
    )

    args = parser.parse_args()

    if args.setup:
        main(setup=True)
        return

    # Apply overrides before starting
    if args.model or args.no_stream:
        from .core.config import Config
        config = Config.load()
        if args.model:
            config.model = args.model
        if args.no_stream:
            config.stream_responses = False
        config.save()

    main()


if __name__ == "__main__":
    entry()
