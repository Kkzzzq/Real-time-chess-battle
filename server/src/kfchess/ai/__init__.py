"""AI system.

第一版已冻结旧的西洋棋 AI，统一退化为 DummyAI。
"""

from kfchess.ai.dummy import DummyAI

KungFuAI = DummyAI

__all__ = ["DummyAI", "KungFuAI"]
