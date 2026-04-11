# Real-time Chess Battle (Realtime Xiangqi API)

纯后端实时中国象棋服务（FastAPI + WebSocket），**不内置 demo 页面**。

## 快速开始

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 测试

```bash
pytest -q
```

> 集成测试必须使用 `with TestClient(app) as client:` 触发 lifespan，避免 `app.state.container` 未初始化。

## 示例入口（替代 demo）

- `examples/create_join_start_flow.sh`：完整 HTTP 流程（create/join/ready/start/state/move）。
- `examples/ws_client_example.py`：WebSocket 订阅 + ping + 命令回执示例。

## 项目定位

- 提供 HTTP API + WebSocket API。
- 适用于前端、自动化脚本、机器人客户端接入。
- 无前端页面；推荐通过 OpenAPI、curl、脚本和测试驱动联调。

## 身份模型（必须先理解）

- `player_id`：外部身份（HTTP/WS 命令与查询使用）。
- `seat`：对局内座位（1/2），用于规则归属与 `piece.owner`。
- `piece.owner` 使用 `seat`，不是 `player_id`。

关系：`player_id -> seat -> piece.owner`。

## Room / Player 生命周期

### Room
- `waiting`：可 `join/ready/start`。
- `running`：tick loop 推进；`leave` 将玩家标记为 `offline`。
- `ended`：允许查询，不允许重新 `join/start`。
- `deleted`：无玩家时删除房间并停止 loop。

### Player
- `joined` -> `ready` -> `running` -> (`offline` | `left`)。
- `offline` 当前版本不自动 reconnect（后续可扩展，以 `player_id` 为主键恢复）。

## API 概览

### Match
- `POST /matches`（支持房规参数）
- `GET /matches`
- `POST /matches/{match_id}/join`
- `POST /matches/{match_id}/ready`
- `POST /matches/{match_id}/start`
- `POST /matches/{match_id}/leave`

`POST /matches` 请求体示例：

```json
{
  "ruleset_name": "standard",
  "allow_draw": true,
  "tick_ms": 100,
  "custom_unlock_windows": null
}
```

### Command（统一 `player_id`）
- `POST /matches/{match_id}/commands/move`
- `POST /matches/{match_id}/commands/unlock`
- `POST /matches/{match_id}/commands/resign`

失败使用 HTTP 错误码：`400/403/404/409`。

### Query（只读）
- `GET /matches/{match_id}/state?player_id=...`
- `GET /matches/{match_id}/phase`
- `GET /matches/{match_id}/unlock-state`
- `GET /matches/{match_id}/events`
- `GET /matches/{match_id}/board`
- `GET /matches/{match_id}/pieces/{piece_id}/legal-moves?player_id=...`
- `GET /matches/{match_id}/players`

## Snapshot 字段语义

`/state` 返回 `MatchSnapshotResponse`，关键字段：

- `match_meta.ruleset`：当前房规（`ruleset_name/allow_draw/tick_ms/custom_unlock_windows`）。
- `players[seat]`：统一输出 `seat + player_id + online/ready/host`。
- `phase`：含 `next_phase_*` 和 `next_wave_*`。
- `unlock`：含窗口状态、波次、每方 `can_choose_now/waiting_for_timeout/choice_source`。
- `board`：逻辑棋盘（按 `piece.x/y`）。
- `runtime_board`：运行时占用棋盘（按 runtime occupancy）。
- `pieces[*].commandability`：
  - `owner_*` 永远可用（owner 视角）。
  - 传 `player_id` 查询 `/state` 时会补 `viewer_*`（viewer 视角）。

## board / runtime_board / display 坐标关系

- `board`：逻辑落点棋盘，稳定用于规则核对。
- `runtime_board`：运行时占用；每个 cell 是 `occupants` 列表 + `primary_occupant`。
- `pieces.display_x/display_y`：连续显示坐标（浮点）。

## legal-moves 语义

返回结构分层：
- `static.targets`：纯规则合法落点。
- `actionable`：viewer 上下文相关结果：
  - `viewer_seat`
  - `actionable_targets`
  - `executable`
  - `actionable_context`
  - `reason`

不传 `player_id` 时：
- 仍返回 `static.targets`。
- `actionable_targets` 为空。
- `actionable_context=provide_player_id_for_actionable_targets`。

## WebSocket 协议

- `WS /matches/{match_id}/ws`
- `WS /ws/matches/{match_id}`（兼容）

连接首帧：
1. `subscribed`
2. `snapshot`

命令帧：
- `move`: `{"type":"move","player_id":"...","piece_id":"...","target_x":4,"target_y":5}`
- `unlock`: `{"type":"unlock","player_id":"...","kind":"horse"}`
- `resign`: `{"type":"resign","player_id":"..."}`

回执策略（固定）：
- 命令直返：`command_result` + `events(delta)`。
- `snapshot/event` 主通道来自 tick loop 广播。
- 客户端需对 event/snapshot 做幂等处理。

## version 语义

`match_meta.version` 是 **event version**：
- 仅当 `state.add_event()` 发生时增长。
- 不是完整 snapshot version。
- 诸如 `display_x`、剩余冷却、phase remaining 的连续变化不保证触发 version 增长。

