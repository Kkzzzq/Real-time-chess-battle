# Real-time-chess-battle

一个以**双人实时中国象棋**为目标形态的对战项目。当前这轮改造重点放在**后端规则层、实时链路和项目命名统一**，优先把原本偏向国际象棋 / Real-time-chess-battle 的核心逻辑切换到中国象棋语义。

## 本轮改造重点

- 项目对外名称统一为 `Real-time-chess-battle`
- 核心棋盘改为 **9×10 中国象棋标准棋盘**
- 后端棋子类型改为：车、马、象、士、将 / 帅、炮、兵 / 卒
- 去掉王车易位、兵升变、四人棋等旧规则入口
- 保留实时移动、冷却、Replay、Snapshot、WebSocket 等主链路
- AI 先退化为 `DummyAI`，优先保证后端跑通

## 当前后端范围

本次实际落地的改动主要集中在：

- `server/src/kfchess/game/`：棋盘、棋子、走法、碰撞、引擎
- `server/src/kfchess/services/game_service.py`：双人房间与 AI 降级
- `server/src/kfchess/lobby/models.py` / `server/src/kfchess/ws/lobby_handler.py`：限制为 2 人房间
- `server/README.md` / `server/pyproject.toml`：项目说明统一
- 部署脚本新增 `real-time-chess-battle-worker.sh` 与新的 systemd service 名称

## 说明

这是一轮**后端优先**的重构，不是对原仓库全部功能的完整重写。因此：

- 前端素材和展示层没有做同等深度的中国象棋重绘
- 内部 Python 包名 `kfchess` 仍暂时保留，避免 import 链路全部打断
- 部分旧的西洋棋测试文件建议删除或重写，详见本次补丁包里的删除清单
