# Real-time Chess Battle

后端（FastAPI + WebSocket）+ 前端（React + Vite）单仓。

## 当前状态（2026-04-11）

- Backend 测试：`pytest` 全绿。
- Frontend：本仓库已完成 `npm install`、`typecheck`、`vitest`、`build`。
- Frontend lockfile：`frontend/package-lock.json` 已提交，CI/本地可统一 `npm ci`。
- Browser E2E：已接入 Playwright 配置与真实 spec 文件；当前环境未安装 playwright 二进制。

## 正式存储架构（已落地代码路径）

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

- `MYSQL_ENABLED=1|0`
- `MYSQL_DSN`
- `MYSQL_POOL_SIZE`
- `MYSQL_MAX_OVERFLOW`
- `REDIS_ENABLED=1|0`
- `REDIS_DSN`
- `PLAYER_TOKEN_TTL_SECONDS`

## 现有开发后端

- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`

> 当 `MYSQL_ENABLED/REDIS_ENABLED` 关闭时，系统保持现有 memory/pickle 路径可运行。
