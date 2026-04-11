# Real-time Chess Battle

后端（FastAPI + WS）+ 前端（React + Vite）的一体化仓库。

## 架构

- `app/`: 后端 API、引擎、服务、仓储
- `frontend/`: 前端页面、状态、WS 客户端
- `tests/`: 后端测试

状态推进模型：
- `running` 状态由 `tick_loop` 驱动
- API 路由不负责额外推进时钟

## 快速启动

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

前端路由：
- `/`
- `/room/:matchId`
- `/game/:matchId`

## 身份模型（重要）

当前使用**对局级凭证**，不是账号系统：
- `player_id`
- `player_token`（有过期时间，默认 24h）

### token 生命周期
- `PLAYER_TOKEN_TTL_SECONDS` 可配置
- token 过期后，`state/query/command/reconnect/ws` 会失败

## 安全与权限边界

当前版本**不支持匿名观战**：
- `state/phase/unlock-state/events/board/players/legal-moves` 全部要求 `player_id + player_token`
- WS 连接必须带 `player_id + player_token`

WS 命令授权策略：
- 握手时校验 token
- 命令帧只带 `player_id`
- 服务端要求帧内 `player_id` 与连接身份一致

## 房间流程

1. Lobby: create/join
2. Room: reconnect -> waiting -> ready/start
3. Game: reconnect -> ws 持续更新 -> ended 结算

start 权限：
- `POST /matches/{id}/start` 现在必须带 `player_id/player_token`
- 且仅 host 可调用

## 核心 API

- `POST /matches`
- `POST /matches/{id}/join`
- `POST /matches/{id}/reconnect`
- `POST /matches/{id}/ready`
- `POST /matches/{id}/start`
- `POST /matches/{id}/leave`
- `POST /matches/{id}/commands/move|unlock|resign`
- `GET /matches/{id}/state|phase|unlock-state|events|board|players`

### 系统运维接口
- `GET /health`
- `GET /ready`
- `GET /metrics`（占位）

## 房规说明

`POST /matches` 参数：
- `ruleset_name`（当前仅 `standard`）
- `allow_draw`
- `tick_ms`
- `custom_unlock_windows`

`custom_unlock_windows` 约束：
- 当前仅允许 `[50, 129]`
- 以保证不与 sealed/soldier_only 固定阶段冲突

## 前端实现要点

- RoomPage：WS + reconnect + 状态同步
- GamePage：WS 为主，HTTP 仅初始化
- Board：
  - 背景使用 `runtime_board`
  - 棋子 overlay 使用 `display_x/display_y`
  - 已修复“选中后点击敌子应走吃子逻辑”
- Unlock：独立 `UnlockPanel` 组件
- Events：WS `event/events` + snapshot 合并去重

## CORS

通过 `ALLOWED_ORIGINS` 配置（逗号分隔），默认仅本地开发域名。

## 仓储与持久化

- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`（本地样本持久化）
  - `MATCH_REPO_PICKLE_PATH` 可配置

> PickleRepo 仅适合单机开发/样本，非生产级分布式持久化方案。

## 日志与异常

- HTTP 请求日志：路径、方法、状态、耗时
- WS 连接/断开日志
- 全局异常处理返回统一 500

## 工程脚本

根目录：
- `dev:backend`
- `dev:frontend`
- `dev:all`
- `test:backend`
- `test:frontend`
- `test:all`
- `lint:backend`
- `lint:frontend`
- `build:all`

## CI

`.github/workflows/ci.yml`：
- backend: py_compile + pytest
- frontend: typecheck + test + build

## 已知限制

- 当前认证为对局级凭证，不是账号系统
- PickleRepo 非生产级持久化
- `metrics` 当前为占位，未接入 Prometheus 指标
- E2E 任务脚本已预留，待接入 Playwright/Cypress


## Host 定义

- `MatchState.host_seat` 是房间级唯一 host 来源。
- `players[*].is_host` 为投影视图，由 `host_seat` 计算得出。

## 前端 WS 连接策略

- 当前前端是**单 active match 连接**策略（单例 ws client）。
- 页面切换会主动断开旧连接再连接新 match。
- 多标签同时打开同一账号不保证连接一致性。

## 合同同步

- 可执行 `npm run contracts:export` 生成 `docs/contracts/openapi.json`。
- 当前前端仍是手工类型为主，后续可基于该 OpenAPI 做代码生成。

## 部署

- 后端镜像：`Dockerfile.backend`
- 前端镜像：`Dockerfile.frontend`
- 本地一体化：`docker-compose.dev.yml`
