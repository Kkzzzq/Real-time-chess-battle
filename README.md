# Real-time-chess-battle 后端

本目录是 `Real-time-chess-battle` 的后端服务。当前版本以**双人实时中国象棋**为核心目标，优先保证规则层、实时对局、冷却、Replay、Snapshot 与 WebSocket 主链路可用。

## 当前设计取向

- 标准棋盘：9×10
- 玩家数量：仅支持 2 人
- 棋子类型：车、马、象、士、将 / 帅、炮、兵 / 卒
- 特性保留：实时移动、碰撞吃子、冷却、Replay、Snapshot
- 暂不保留：四人棋、王车易位、兵升变
- AI：统一退化为 `DummyAI`

## 本轮主要改动

1. `game/pieces.py`：棋子枚举改为中国象棋语义，并保留旧枚举别名做兼容。
2. `game/board.py`：默认棋盘改为 9×10，中国象棋标准初始布局。
3. `game/moves.py`：重写走法判定，支持兵 / 卒、马腿、象眼、士、将 / 帅、炮架、飞将。
4. `game/collision.py`：保留实时碰撞模型，去掉西洋棋里针对马 / 兵的特殊处理。
5. `game/engine.py`：改成只支持双人中国象棋，四人棋入口直接禁用。
6. `services/game_service.py`：AI 统一退化为 `DummyAI`，优先保证主链路稳定。
7. `lobby/models.py`：Lobby 只允许 2 人房间。

## 注意

本轮为了降低风险，**没有**同步重命名内部包目录 `src/kfchess`，否则会牵扯所有 import、脚本、部署命令与迁移文件的联动修改。对外项目名已经统一为 `Real-time-chess-battle`。
