# Real-time Chess Battle (Realtime Xiangqi Sample)

基于 FastAPI 的中国象棋实时玩法样本，已按分层结构实现：

- 无回合并发指令
- 分阶段解锁（30s 封盘、50/70/90/110 解锁窗口、130 全解锁）
- 棋种冷却与移动时长
- 中国象棋核心走法（含蹩马腿、塞象眼、炮架、飞将）
- 移动过程碰撞与吃子
- 150s 后和棋判定（60s 无出手 / 90s 无吃子）

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 调试入口

- `GET /demo`：后端联调面板

## HTTP API

- `POST /matches`
- `GET /matches`
- `POST /matches/{match_id}/join`
- `POST /matches/{match_id}/ready`
- `POST /matches/{match_id}/start`
- `POST /matches/{match_id}/leave`
- `POST /matches/{match_id}/commands/move`
- `POST /matches/{match_id}/commands/unlock`
- `POST /matches/{match_id}/commands/resign`
- `GET /matches/{match_id}/state`
- `GET /matches/{match_id}/snapshot/full`
- `GET /matches/{match_id}/phase`
- `GET /matches/{match_id}/unlock-state`
- `GET /matches/{match_id}/events`
- `GET /matches/{match_id}/board`
- `GET /matches/{match_id}/pieces/{piece_id}/legal-moves`
- `GET /matches/{match_id}/players`

## WebSocket

- `WS /matches/{match_id}/ws`
- `WS /ws/matches/{match_id}`（兼容旧路径）

## 测试

```bash
pytest -q
```
