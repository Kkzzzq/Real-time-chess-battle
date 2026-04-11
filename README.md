# Real-time Chess Battle

现在仓库包含：
- 后端（FastAPI + WebSocket）
- 正式前端（React + TypeScript + Vite，目录 `frontend/`）
- 示例脚本（`examples/`）

## 1) 启动方式

### 后端
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认联调地址：
- API: `http://127.0.0.1:8000`
- WS: `ws://127.0.0.1:8000`

## 2) 前端功能落地

`frontend/` 已提供：
- 页面流：大厅 -> 房间 -> 对局
- 棋盘组件：9x10 网格、棋子渲染、可行动作高亮
- API Client：`matchApi / commandApi / queryApi`
- WS Client：连接、心跳、断线重连、snapshot 消费
- 状态管理（Zustand）：session / room / match / ws / ui
- Session 持久化：本地保存 `player_id/player_token/match_id`
- 前端测试（Vitest）：store + board 组件基础测试

## 3) 身份与鉴权（已生效）

`join` 会返回：
- `player_id`
- `player_token`

之后：
- `ready/leave/commands/state(viewer)/legal-moves(viewer)/ws` 都需要 `player_token`
- 新增 `POST /matches/{match_id}/reconnect`，可恢复 `online=true`

## 4) 房规与规则

`POST /matches` 支持：
- `ruleset_name`（当前只允许 `standard`）
- `allow_draw`
- `tick_ms`
- `custom_unlock_windows`

`custom_unlock_windows` 现已真实驱动：
- phase wave 判定
- unlock window 判定
- auto unlock 判定
- snapshot 中 next wave 计算

## 5) API 语义更新

- `legal-moves`:
  - `static.targets` 始终返回
  - `actionable` 仅在提供 viewer 身份时返回；否则为 `null`
- `query_routes` 纯查询（不再隐式推进状态）
- `command_routes` 仅执行命令（不再额外 reconcile）
- running 状态推进由 `tick_loop` + `match_service.tick_once_with_events` 统一负责

## 6) runtime_board 消费规则

`runtime_board.cells[y][x]`：
- `occupants`: 当前格全部占用者（moving 优先）
- `primary_occupant`: 当前格主显示占用者（按 `moving` 优先 + `piece_id` 排序）

前端推荐：
- 交互合法性基于 API（`legal-moves`）
- 主展示优先 `runtime_board` + `pieces.display_x/display_y`
- 规则核对可查看 `board`

## 7) 测试

后端：
```bash
pytest -q
```

前端：
```bash
cd frontend
npm test
```

## 8) 示例脚本与前端关系

- `examples/` 仅用于后端调试/联调脚本
- 正式产品交互请使用 `frontend/`
