# Real-time Chess Battle

仓库现在包含后端 + 正式前端 + 基础 CI。

## 运行

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

## 鉴权模型（对局级）

`join` 返回 `player_id + player_token`。后续：
- HTTP 命令/查询 viewer 需要 `player_token`
- WS 连接通过 query string 做 token 校验

WS 命令帧策略：
- 连接时校验 token
- 后续命令帧只带 `player_id`（服务端校验与连接身份一致）

当前 `player_token` 带过期时间（默认 24h，可用 `PLAYER_TOKEN_TTL_SECONDS` 配置）。

## 房规

`POST /matches` 支持：
- `ruleset_name`（当前只支持 `standard`）
- `allow_draw`
- `tick_ms`
- `custom_unlock_windows`

`custom_unlock_windows` 已真实驱动 phase/unlock/snapshot next wave。

## 前端功能

- 正式路由 + URL 可分享
- Lobby 明确 join 流程
- Room 实时轮询状态（含 running 自动跳转 game）
- Game 展示 phase/unlock/events/piece commandability/cooldown
- Unlock 面板可直接调用 unlock 命令
- 结算态 UI（winner/reason + 返回大厅/房间）
- Board 消费 `runtime_board`，并用 `display_x/display_y` 渲染浮动棋子层
- reconnect 业务流（页面进入先 `reconnect`，失败清 session 回大厅）

## 持久化

支持两种 repo 装配：
- `MATCH_REPO_BACKEND=memory`（默认）
- `MATCH_REPO_BACKEND=pickle`（磁盘持久化，路径 `MATCH_REPO_PICKLE_PATH`）

## 工程脚本

根目录 `package.json`：
- `dev:backend`
- `dev:frontend`
- `test:backend`
- `test:frontend`
- `test:all`
- `build:frontend`
- `build:all`

## CI

`.github/workflows/ci.yml` 已包含：
- backend: pytest
- frontend: typecheck + test + build
