# Real-time-chess-battle 后端改造说明

## 已落地

- 标准棋盘切到 9×10 中国象棋布局
- 规则层改成中国象棋走法
- 双人房间固定化
- AI 统一降级为 DummyAI
- 新增新的 worker / systemd 文件名

## 建议删除或重写

- `docs/FOUR_PLAYER_DESIGN.md`
- `docs/KFCHESS_ORIGINAL_IMPLEMENTATION.md`
- `server/tests/unit/game/test_4player.py`
- `server/tests/unit/game/test_moves.py`
- `server/tests/unit/game/test_board.py`
- 所有依赖国际象棋升变 / 易位 / 四人棋假设的测试
