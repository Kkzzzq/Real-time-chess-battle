# Real-time Chess Battle (Realtime Xiangqi API)

基于 FastAPI 的实时中国象棋后端服务（无前端 demo 页面）。

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 测试

```bash
pytest -q
```

> 集成测试使用 `TestClient` 时必须写成 `with TestClient(app) as client:`，以确保 lifespan 初始化 container。

## Room 生命周期

- `waiting`: 可 `join/ready/start`。
- `running`: 对局进行中；`leave` 会将玩家标记为 offline。
- `ended`: 对局结束；允许查询，不允许重新 `join/start`。

玩家状态字段在 `players[seat]` 中：
- `id`（player_id）
- `ready`
- `online`
- `is_host`

## API 概览

### Match
- `POST /matches` 创建房间
- `GET /matches` 房间列表
- `POST /matches/{match_id}/join`
- `POST /matches/{match_id}/ready`
- `POST /matches/{match_id}/start`
- `POST /matches/{match_id}/leave`

### Command（统一使用 `player_id`）
- `POST /matches/{match_id}/commands/move`
- `POST /matches/{match_id}/commands/unlock`
- `POST /matches/{match_id}/commands/resign`

命令失败使用 HTTP 错误码（400/403/404/409），成功返回：
- `ok`
- `message`
- `snapshot`

### Query
- `GET /matches/{match_id}/state`
- `GET /matches/{match_id}/phase`
- `GET /matches/{match_id}/unlock-state`
- `GET /matches/{match_id}/events`
- `GET /matches/{match_id}/board`
- `GET /matches/{match_id}/pieces/{piece_id}/legal-moves?player_id=...`
- `GET /matches/{match_id}/players`

## Snapshot 语义

`/state` 返回：
- `board`: 逻辑棋盘（基于 piece.x/y）
- `runtime_board`: 运行时占用棋盘（基于 runtime occupancy）
- `pieces[*].can_command`: owner 视角可操作性
- `pieces[*].disabled_reason`: owner 视角原因

即 `can_command` 不是 viewer 权限判断字段；viewer 权限请结合 `player_id` 与 `piece.owner` 判定。

## legal-moves 语义

`GET /pieces/{piece_id}/legal-moves`：
- `static_targets`: 纯走法合法落点
- `actionable_targets`: 当前请求者可立即下达命令的落点（需要传 `player_id` 且归属该棋子 owner）
- `executable`: 是否有 actionable target
- `reason`: 原因码

## WebSocket

- `WS /matches/{match_id}/ws`
- `WS /ws/matches/{match_id}`（兼容）

连接后首帧：
1. `subscribed`（含 `match_id/status/phase/version/started_at/winner/reason`）
2. `snapshot`

命令帧（JSON）统一使用 `player_id`：
- `{"type":"move","player_id":"...","piece_id":"...","target_x":4,"target_y":5}`
- `{"type":"unlock","player_id":"...","kind":"horse"}`
- `{"type":"resign","player_id":"..."}`
- `{"type":"ping"}`

命令响应时序：
1. `command_result`
2. `events`（本次新增事件）
3. `snapshot`
