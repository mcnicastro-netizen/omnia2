"""Compatibility shim — Emergent package removed from PyPI.

Prefer: `from shared.llm.chat import LlmChat, UserMessage, TextDelta`
This package remains only as a temporary re-export.
"""

from shared.llm.chat import LlmChat, UserMessage, TextDelta

__all__ = ["LlmChat", "UserMessage", "TextDelta"]
