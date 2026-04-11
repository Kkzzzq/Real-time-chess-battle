# Real-time Chess Battle

后端（FastAPI + WebSocket）+ 前端（React + Vite）的单仓项目。

## 1) 当前项目边界（先看）

- 当前仅支持 **2 名玩家对局**。
- `query` / `commands` / `ws` 均要求 `player_id + player_token`，**不支持匿名 spectator**。
- 前端 WebSocket 采用 **single active-match client** 策略：同一前端实例一次只维护一个房间连接。
- `host` 的单一来源是房间级字段：`host_seat` + `host_player_id`（`is_host` 为投影视图）。

## 2) 快速启动

### Backend
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

前端路由：
- `/` Lobby
- `/room/:matchId` 房间等待页
- `/game/:matchId` 对局页

## 3) 身份与会话

- `POST /matches/{id}/join` 返回 `player_id + player_token + player_token_expires_at`。
- `POST /matches/{id}/reconnect` 使用同一凭证恢复。
- token TTL 由 `PLAYER_TOKEN_TTL_SECONDS` 控制（默认 86400 秒）。
- 前端 `sessionStore` 会在 hydrate 时清理本地过期 token；`useSessionBootstrap` 会将 reconnect 返回的完整玩家信息回写 session。

## 4) 房间与 host 规则

- 首位入房玩家成为 host。
- 只有 host 可以 start。
- host 离开 waiting 房间时，host 自动转移给当前最小 seat，并同步 `host_player_id`。
- `players[*].is_host` 总是由房间级 host 字段计算。

## 5) WebSocket 协议职责

- `subscribed`: 订阅成功元信息。
- `snapshot`: 全量状态快照。
- `events`: 增量事件批量。
- `event`: 增量事件单条。
- `command_result`: 命令执行结果。
- `pong`: 心跳响应。

前端 store 约定：
- `snapshot` 负责全量覆盖。
- `events/event` 负责增量事件流；和 snapshot 内事件做去重合并。

## 6) 棋盘显示策略

前端消费三层信息：
- `board`：逻辑占位棋盘（落子格）。
- `runtime_board`：运行时占位棋盘（移动中的路径占位）。
- `pieces.display_x/display_y`：棋子动画 overlay。

多占用格：
- 主显示 `primary_occupant`。
- 若 `occupants.length > 1`，格子会显示额外 `+N` 标识。

## 7) 运维接口与成熟度

- `GET /health`
- `GET /ready`
- `GET /metrics`：当前为 JSON 简易指标（`matches_total` / `matches_running` / `ws_active_matches` / `ws_active_connections`），**不是 Prometheus 格式**。

## 8) Repo 与持久化

- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`
  - `MATCH_REPO_PICKLE_PATH` 控制文件路径

> PickleRepo 仅适合单机开发，不是生产级并发存储方案。

## 9) 部署

- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker-compose.dev.yml`：本地开发
- `docker-compose.prod.yml`：生产示例（包含后端数据卷与基础环境变量）

## 10) 环境变量

### Backend
- `ALLOWED_ORIGINS`：逗号分隔 CORS 白名单。
- `MATCH_REPO_BACKEND`：`memory` / `pickle`。
- `MATCH_REPO_PICKLE_PATH`：pickle 文件路径。
- `PLAYER_TOKEN_TTL_SECONDS`：对局 token TTL。

### Frontend
- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`

## 11) 工程脚本

根目录：
- `npm run test:backend`
- `npm run contracts:export`
- `npm run dev:all`

前端：
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run test`
- `npm --prefix frontend run build`

## 12) 合同同步

- `python scripts/export_openapi.py` 导出 `docs/contracts/openapi.json`。
- 当前 `frontend/src/types/contracts.ts` 仍有手工类型；后续可切换为 OpenAPI 生成。

## 13) 已知限制

- 无账号系统（仅对局级 token）。
- 无 spectator。
- WS 前端单活动连接策略不保证多标签一致性。
- `/metrics` 仍是轻量 JSON，不是完整监控体系。
