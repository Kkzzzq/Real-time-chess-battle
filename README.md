# Real-time Chess Battle

后端（FastAPI + WebSocket）+ 前端（React + Vite）的单仓项目。

## 1) 当前成熟度与真实状态（2026-04-11）

- Backend 测试：可在仓库内执行并作为当前质量基线。
- Frontend：需要在可访问 npm registry 的 Node 环境执行 `npm install && npm run typecheck && npm run test && npm run build` 进行真实验证。
- Browser E2E：当前仓库尚未接入 Playwright/Cypress 级别的浏览器端到端测试。

> 结论：当前版本后端闭环较完整，前端与全链路闭环仍需继续补强。

## 2) 当前项目边界

- 当前仅支持 **2 名玩家对局**。
- `query` / `commands` / `ws` 均要求 `player_id + player_token`，**不支持匿名 spectator**。
- 前端 WebSocket 采用 **single active-match client** 策略：同一前端实例一次只维护一个房间连接。
- `host` 的单一来源是房间级字段：`host_seat` + `host_player_id`（`is_host` 为投影视图）。

## 3) 快速启动

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

## 4) 身份与会话

- `POST /matches/{id}/join` 返回 `player_id + player_token + player_token_expires_at`。
- `POST /matches/{id}/reconnect` 使用同一凭证恢复。
- token TTL 由 `PLAYER_TOKEN_TTL_SECONDS` 控制（默认 86400 秒）。
- 前端 `sessionStore` 会在 hydrate 时清理本地过期 token；`useSessionBootstrap` 会将 reconnect 返回的完整玩家信息回写 session。

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

## 7) 观测与运维

- `GET /health`
- `GET /ready`
- `GET /metrics`：当前为 JSON 简易指标（`matches_total` / `matches_running` / `ws_active_matches` / `ws_active_connections`），**不是 Prometheus 格式**。

## 8) 正式存储方案（目标）：MySQL + Redis

当前 `MemoryRepo / PickleRepo` 仅适合开发样本阶段，正式化目标明确为：

> **MySQL 负责持久化主数据，Redis 负责维护实时对局状态。**

### MySQL 负责

- 房间基础信息（`match_id`、规则、状态、时间戳、winner/reason 等）。
- 玩家信息（`player_id`、seat、host 标记、join/leave 记录）。
- 对局结果与历史记录（结果、统计、规则快照）。
- 关键事件归档（join/ready/start/unlock/resign/game_over）。

### Redis 负责

- 当前对局实时状态（棋盘、运行时坐标、phase/wave、cooldown）。
- WebSocket 在线/重连状态（连接、心跳、reconnect 窗口）。
- 对局级短期 token 与 session 映射。
- 最近事件流与命令日志缓存。

### 代码演进方向

- 保留 `MemoryRepo / PickleRepo` 作为开发后备实现。
- 增加 `MySQLRepository` 与 `RedisRepository`（或等价命名）并接入 service 层抽象。
- 在 `create/start/game_over/join/reconnect` 等关键路径明确 MySQL 写入、Redis 写入与双写策略。

## 9) 现有 Repo 后端（开发模式）

- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`
  - `MATCH_REPO_PICKLE_PATH` 控制文件路径

> PickleRepo 仅适合单机开发，不是生产级并发存储方案。

## 10) 部署

- `Dockerfile.backend`
- `Dockerfile.frontend`
- `docker-compose.dev.yml`：本地开发
- `docker-compose.prod.yml`：生产示例（当前未内建 MySQL/Redis 服务编排）

## 11) 环境变量

### Backend
- `ALLOWED_ORIGINS`：逗号分隔 CORS 白名单。
- `MATCH_REPO_BACKEND`：`memory` / `pickle`。
- `MATCH_REPO_PICKLE_PATH`：pickle 文件路径。
- `PLAYER_TOKEN_TTL_SECONDS`：对局 token TTL。

### Frontend
- `VITE_API_BASE_URL`
- `VITE_WS_BASE_URL`

## 12) 工程脚本

根目录：
- `npm run test:backend`
- `npm run contracts:export`
- `npm run dev:all`

前端：
- `npm --prefix frontend run typecheck`
- `npm --prefix frontend run test`
- `npm --prefix frontend run build`

## 13) 合同同步

- `python scripts/export_openapi.py` 导出 `docs/contracts/openapi.json`。
- 当前 `frontend/src/types/contracts.ts` 仍有手工类型；后续建议切换为 OpenAPI 生成 TS types/client，仅保留少量 UI 派生类型。

## 14) 近期重点改造清单（按优先级）

1. 前端依赖与构建验证纳入 CI（typecheck/test/build）。
2. 接入浏览器级 E2E（Playwright/Cypress），覆盖 create/join/ready/start/move/unlock/resign/reconnect。
3. RoomPage 状态机化（loading/reconnecting/denied/deleted/ended）。
4. GamePage 继续减重（controller/bootstrap/panel 进一步拆分）。
5. Board/UnlockPanel/EventsPanel/ResultPanel 产品化。
6. 错误体系统一（ErrorBoundary + toast + fatal/recoverable 映射）。
7. token 生命周期说明与刷新策略边界补充。
8. metrics/logging/audit 字段标准化。
9. 部署文档补全（env/volume/拓扑，含 MySQL+Redis 正式化说明）。

## 15) 已知限制

- 无账号系统（仅对局级 token）。
- 无 spectator。
- WS 前端单活动连接策略不保证多标签一致性。
- `/metrics` 仍是轻量 JSON，不是完整监控体系。
- 当前仓库尚未具备浏览器 E2E 级自动化闭环证明。
