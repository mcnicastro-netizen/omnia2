"""Temporary bridge: Emergent package removed from PyPI.

M0: allow imports so the app boots.
M1: replace call sites with shared.llm (Gemini). This stub will be deleted.
"""

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta

__all__ = ["LlmChat", "UserMessage", "TextDelta"]
