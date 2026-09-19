"""Compatibility shim — prefer `from shared.llm.chat import ...`.

Kept temporarily so any leftover import of emergentintegrations still boots.
Will be removed in a later cleanup commit.
"""

from shared.llm.chat import LlmChat, UserMessage, TextDelta

__all__ = ["LlmChat", "UserMessage", "TextDelta"]
