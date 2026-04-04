"""Frozen KungFuAI shim.

旧版 KungFuAI 深度依赖西洋棋规则。
第一版中国象棋改造阶段统一降级为 DummyAI，避免错误评估逻辑继续参与对局。
"""

from kfchess.ai.dummy import DummyAI


class KungFuAI(DummyAI):
    """兼容旧导入路径的占位 AI。"""

    pass
