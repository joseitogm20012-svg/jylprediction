"""Simple OpenAI client wrapper for Nvidia's hosted model.

This module demonstrates how to call the `z-ai/glm-5.2` model via the
Nvidia API endpoint. It reads the API key from the environment variable
`NVIDIA_API_KEY`. The code streams the completion to stdout, preserving any
ANSI colour codes when the terminal supports them.
"""

from openai import OpenAI
import os
import sys

# Detect colour support – avoid raw ANSI codes on non‑TTYs.
_USE_COLOR = sys.stdout.isatty() and os.getenv("NO_COLOR") is None
_REASONING_COLOR = "\033[90m" if _USE_COLOR else ""
_RESET_COLOR = "\033[0m" if _USE_COLOR else ""

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key=os.getenv("NVIDIA_API_KEY"),
)

# Example usage – replace the empty user message with your prompt.
completion = client.chat.completions.create(
    model="z-ai/glm-5.2",
    messages=[{"role": "user", "content": ""}],
    temperature=1,
    top_p=1,
    max_tokens=16384,
    seed=42,
    stream=True,
)

for chunk in completion:
    if not getattr(chunk, "choices", None):
        continue
    if len(chunk.choices) == 0 or getattr(chunk.choices[0], "delta", None) is None:
        continue
    delta = chunk.choices[0].delta
    if getattr(delta, "content", None) is not None:
        # Optionally prepend a colour for reasoning content.
        sys.stdout.write(delta.content)
        sys.stdout.flush()
