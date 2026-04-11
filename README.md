# Real-time Chess Battle

后端（FastAPI + WebSocket）+ 前端（React + Vite）单仓。

<<<<<<< HEAD
## 当前状态（2026-04-11）

- Backend 测试：`pytest` 全绿。
- Frontend：本仓库已完成 `npm install`、`typecheck`、`vitest`、`build`。
- Frontend lockfile：`frontend/package-lock.json` 已提交，CI/本地可统一 `npm ci`。
- Browser E2E：已接入 Playwright 配置与真实 spec 文件；当前环境未安装 playwright 二进制。

## 正式存储架构（已落地代码路径）
=======
## 1) 当前成熟度与真实状态（2026-04-11）

- Backend 测试：仓库内可运行并作为当前质量基线。
- Frontend：本仓库已补齐 session/notification/generated-contract/e2e scaffold，但仍需在可访问 npm registry 的环境执行 `npm install && npm run typecheck && npm run test && npm run build` 做真实验证。
- Browser E2E：已补 `e2e/*.spec.ts` 脚手架，尚未接入 Playwright 执行链。

## 2) 当前项目边界

- 当前仅支持 **2 名玩家对局**。
- `query` / `commands` / `ws` 均要求 `player_id + player_token`，不支持匿名 spectator。
- 前端 WebSocket 采用 single active-match client 策略。
- `host` 的单一来源是 `host_seat + host_player_id`。

## 3) 快速启动
>>>>>>> origin/main

> **MySQL 存主数据，Redis 存实时状态。**

### MySQL 层

- `app/db/base.py`：SQLAlchemy Base/metadata。
- `app/db/session.py`：MySQL engine + SessionLocal。
- `app/repository/mysql/models.py`：`MatchRecord/PlayerRecord/MatchEventRecord/PlayerSessionRecord` ORM 表。
- `app/repository/mysql/*_repo_mysql.py`：真实 CRUD/upsert（非 dataclass 占位）。
- `migrations/`：alembic env + 首版建表 migration。

### Redis 层

- `app/repository/redis/runtime_repo_redis.py`：runtime snapshot 读写。
- `app/repository/redis/presence_repo_redis.py`：online/offline/heartbeat。
- `app/repository/redis/session_cache_repo_redis.py`：session token cache + TTL。
- `app/repository/redis/cache_keys.py`：统一 key 约定。

### 协调层

- `app/services/persistence_service.py`：
  - 持久化 match/player/session
  - runtime/presence/cache 同步
  - 增量事件归档入口

## 关键服务改造

- `RoomService`：接入 `PlayerSessionService + PersistenceService + StateMachine`。
- `MatchService`：tick 后通过 `PersistenceService` 刷 runtime，并在 ended 时可接 `MatchArchiveService`。
- `CommandService`：move/unlock/resign 统一走 `PersistenceService`。
- `PlayerSessionService`：支持 issue/validate/rotate/revoke，并可落 MySQL+Redis。

## 前端改造

- `frontend/src/session/*`：bootstrap/guards/sessionService。
- `frontend/src/store/notificationStore.ts` + `components/feedback/*`：统一反馈层入口。
- Board 拆层：`BoardGrid/PieceLayer/BoardCellOverlay/BoardDebugOverlay`。
- `scripts/generate_frontend_types.sh`：从 OpenAPI 生成 `frontend/src/generated/contracts.ts`（真实生成，不再 placeholder）。

## E2E

- `playwright.config.ts`
- `e2e/room-flow.spec.ts`
- `e2e/game-flow.spec.ts`
- `e2e/reconnect.spec.ts`

执行：
```bash
npm run e2e
```

## 环境变量（新增）

<<<<<<< HEAD
- `MYSQL_ENABLED=1|0`
- `MYSQL_DSN`
- `MYSQL_POOL_SIZE`
- `MYSQL_MAX_OVERFLOW`
- `REDIS_ENABLED=1|0`
- `REDIS_DSN`
- `PLAYER_TOKEN_TTL_SECONDS`

## 现有开发后端
=======
## 4) 正式存储架构目标：MySQL + Redis

当前默认运行仍是 `memory/pickle`，但代码结构已新增 MySQL/Redis 模块骨架，目标架构固定为：

> **MySQL 持久化主数据，Redis 维护实时对局状态。**

### MySQL（持久化主数据）

- 房间主记录、玩家元数据、结果、关键事件归档。
- 新增目录：`app/db/*`、`app/repository/mysql/*`、`migrations/*`（脚手架）。

### Redis（实时状态）

- runtime board/phase/unlock、presence、session cache、短期事件缓存。
- 新增目录：`app/repository/redis/*`、`app/runtime/presence_service.py`。

### 协调层

- 新增 `app/services/persistence_service.py`，用于定义 MySQL+Redis 写入协调边界。

## 5) 已落地的模块级改造（本次）

### 后端

- `app/repository/base.py` 拆分出 `MatchMetaRepo/RuntimeStateRepo/EventRepo/PlayerRepo` 协议，同时保留 legacy `MatchRepo` 兼容当前实现。
- 新增 `app/services/player_session_service.py`，统一 token 颁发/校验。
- `RoomService` 已接入 `PlayerSessionService`，并接入 `room_state_machine/player_state_machine` 做核心状态迁移校验。
- 新增 `app/services/match_archive_service.py`（归档服务骨架）。
- 新增 `app/repository/mysql/*` 与 `app/repository/redis/*` 脚手架（当前为可替换实现，未接 DB/Redis 客户端）。

### 前端

- 新增 `frontend/src/session/{bootstrap,guards,sessionService}.ts`。
- 新增 `frontend/src/store/notificationStore.ts` 统一通知状态入口。
- 新增 `frontend/src/generated/contracts.ts`（由脚本生成的占位产物）。
- 新增 `e2e/*.spec.ts`（Playwright 场景骨架）。

### 脚本

- 新增 `scripts/generate_frontend_types.sh`。
- 根 `package.json` 新增：`contracts:generate`、`e2e`、`e2e:headed`。

## 6) 现有 Repo 后端（开发模式）
>>>>>>> origin/main

- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`

<<<<<<< HEAD
> 当 `MYSQL_ENABLED/REDIS_ENABLED` 关闭时，系统保持现有 memory/pickle 路径可运行。
=======
> `PickleRepo` 仅适合开发，不是生产级并发存储。

## 7) 观测与运维

- `GET /health`
- `GET /ready`
- `GET /metrics`：当前仍是简易 JSON 指标，非 Prometheus。

## 8) 下一步优先级（按完整项目）

1. 接入真实 MySQL/Redis client + migrations。
2. 将 `PersistenceService` 接入 room/match/command 全流程。
3. RoomPage/GamePage 按状态机进一步拆 controller。
4. Board/Unlock/Events/Result 组件产品化。
5. 错误反馈层（Toast/NotificationCenter/ErrorBoundary）完整接入。
6. 生成式契约替换手工 `contracts.ts`。
7. Playwright E2E 真正可运行并接入 CI。
8. metrics/audit/deploy 文档与实现继续完善。
>>>>>>> origin/main
