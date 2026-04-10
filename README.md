# Real-time-chess-battle 审计与改造方案（按你要求的顺序）

## 1. 先把玩法定义定死：`phase_standard_v1`

这版我建议**先只保留一个正式玩法预设**，不要再同时维护 `standard / lightning / four_player / campaign` 多种规则。第一版就做成：**双人、9×10、中国象棋、无回合制、阶段解锁、分棋种冷却**。

### 1.1 对局目标
- 红方在下（player=1），黑方在上（player=2），使用标准中国象棋初始布局。
- **胜利条件：直接吃掉对方将 / 帅。**
- **不采用传统回合制象棋的“必须应将 / 不能送将”整套复杂规则**；否则实时玩法会很难操作，也和当前后端骨架不一致。
- 但保留两条中国象棋核心禁手：
  - **将帅不能隔空照面**。
  - **飞将吃将** 合法。

### 1.2 实时操作总则
- 游戏**没有回合**，双方可同时下指令。
- 一个棋子只要满足以下条件，就可以被下达移动指令：
  - 该棋子所属**棋种已解锁**；
  - 该棋子**当前没有在移动中**；
  - 该棋子**当前不在冷却中**；
  - 目标点满足该棋子的中国象棋走法。
- 同一方可以同时操作多个不同棋子。
- 同一个棋子**不支持排队指令**，必须等当前移动与冷却都结束后再下下一次指令。

### 1.3 开局阶段解锁（核心玩法）
- **0s ~ 30s：封盘期**
  - 双方都不能移动任何棋子。
  - 只显示棋盘、阶段倒计时和即将解锁提示。
- **30s ~ 50s：兵线期**
  - 双方仅可移动 **兵 / 卒**。
- **从 50s 开始，每隔 20s 进入一次“解锁选择窗口”**。
  - 每一方都**独立选择**自己下一类要解锁的棋种。
  - 一旦解锁，该方该棋种的**全部棋子永久可用**。
  - 如果该时间窗内未选择，系统按默认优先级自动解锁。

我建议解锁池按下面的门槛控制，避免开局直接出将/帅或过早双车压死：

| 时间点 | 该次可选棋种 | 说明 |
|---|---|---|
| 50s | 马 / 炮 / 车 | 第一波先放主要外线棋，但不放士象将 |
| 70s | 马 / 炮 / 车 / 象 | 开始允许补机动或补象 |
| 90s | 马 / 炮 / 车 / 象 / 士 | 防守类开始进入 |
| 110s | 所有未解锁棋种（含将/帅） | 这时允许把将/帅纳入操作池 |
| 130s | 若还有未解锁棋种，全部自动解锁 | 防止有人一直拖着不选 |

默认自动解锁优先级我建议写死为：**炮 > 马 > 车 > 象 > 士 > 将/帅**。

### 1.4 棋子冷却（按棋种区分）
冷却在**该次移动完整结束后**开始计算，不是在发令时开始。

| 棋种 | 冷却 | 我给的平衡理由 |
|---|---:|---|
| 兵 / 卒 | 10s | 低价值、短步进、应该是开局主战力 |
| 士 | 8s | 活动范围最小，偏防守，冷却应偏短 |
| 象 | 15s | 两步斜走、不过河，机动有限 |
| 马 | 20s | 机动强、抓机会能力高 |
| 炮 | 20s | 远程威胁强，但需要炮架 |
| 车 | 30s | 线性压制最强，必须用高冷却限制 |
| 将 / 帅 | 3s | 允许高频微调站位，但仍受解锁阶段约束 |

### 1.5 移动时间
- 基础移动速度：**1 格 = 1 秒**。
- 直线多格棋子（车、炮）走几格就花几秒。
- 马、象按路径段计算：
  - 马：L 形拆成 2 段，总移动时间 2 秒；
  - 象：田字拆成 2 段，总移动时间 2 秒。
- 士、兵、将 / 帅均为单步 1 秒。

### 1.6 吃子与碰撞规则（必须写死）
- **移动中的棋子**接触到敌方棋子时发生吃子判定。
- **移动棋子撞静止棋子**：移动方获胜，静止棋子被吃。
- **移动棋子撞移动棋子**：
  - 若一方启动更早，**先启动者获胜**；
  - 若两者启动 tick 完全相同并发生正面碰撞，**同归于尽**。
- 这条规则和当前后端 `collision.py` 的骨架是接近的，适合继续沿用。

### 1.7 中国象棋走法边界
- 兵 / 卒：不过河只能前进；过河后可左右平移；永不后退。
- 马：蹩马腿。
- 象：塞象眼，不过河。
- 士：只在九宫内斜走一步。
- 将 / 帅：只在九宫内直走一步；允许飞将直接吃对方将/帅。
- 炮：平时走子不隔子，吃子必须隔一个炮架。
- 车：直线移动，中间不可有阻挡。

### 1.8 和棋与结束
- **150s 前不触发系统和棋**，保证完整经历解锁节奏。
- **150s 后**满足以下任一条件判和：
  - 连续 **60s** 双方都没有新的合法出手；
  - 连续 **90s** 没有发生吃子。
- 任一玩家投降，则对方胜。

### 1.9 首版裁剪建议
- **先只保留一个速度档：`phase_standard_v1`。**
- **先冻结 campaign。**
- **先冻结旧 KungFuAI，只保留 DummyAI / 或先仅做人机占位。**
- **先不做 ranked。** 先把玩法跑通，再谈匹配、积分和平衡。

## 2. 当前仓库的真实问题（我看完后的结论）

### 2.1 最大问题不是“某几个 bug”，而是“规则真源不存在”
- README 说已经切到中国象棋，但没有一份完整、唯一、可执行的玩法说明。
- 后端核心只完成了**棋盘尺寸 + 棋子走法 + 双人限制**，**没有实现你要的阶段解锁玩法**。

### 2.2 当前后端还只是“实时中国象棋骨架”，不是“阶段解锁版实时象棋”
直接能确认的点：
- `server/src/kfchess/game/state.py` 仍然是**全局速度 / 全局冷却**模型，没有“按棋种不同冷却”。
- `server/src/kfchess/game/engine.py` 在移动结束后统一写入 `config.cooldown_ticks`，说明**所有棋子冷却相同**。
- `server/src/kfchess/ws/handler.py` 只有**3 秒开局倒计时**，没有 30 秒封盘、没有 20 秒解锁窗口。
- `server/src/kfchess/ws/protocol.py` 与 `client/src/ws/types.ts` 都**没有 phase / unlock_choice / unlocked_piece_types / next_phase_tick** 之类字段。

### 2.3 文档层严重混杂旧国际象棋语义
- `docs/ARCHITECTURE.md` 仍写 8×8 / four_player / castling。
- `docs/MVP_IMPLEMENTATION.md` 仍写 8×8、4-player、升变、王车易位。
- `docs/CAMPAIGN_DESIGN.md` 与 `server/src/kfchess/campaign/levels.py` 基本还是完整的国际象棋关卡资产。
- `docs/AI_DESIGN.md` 仍然按旧 chess piece value、queen、promotion 逻辑在写。

### 2.4 campaign 目前不是“待适配”，而是“应先冻结”
- `server/src/kfchess/campaign/board_parser.py` 仍按 **8×8 国际象棋字符串**解析。
- `server/src/kfchess/campaign/levels.py` 的标题、描述、棋盘字符串、棋子字母都还是旧 chess。
- 这意味着如果继续让 campaign 出现在首版玩法里，会把整个规则口径重新拉歪。

### 2.5 AI 目录大部分仍是旧 chess 评估逻辑
- 虽然 `game_service.py` 里已经把实际对局 AI 退化成 `DummyAI`，这是对的。
- 但 `arrival_field.py / eval.py / move_gen.py / tactics.py` 这些文件仍大量使用旧的 rook / bishop / queen / king / pawn 估值与路径假设。
- 所以首版绝对不能让这些逻辑重新接管实战决策。

### 2.6 前端还没开始真正中国象棋化
- `client/src/assets/chess-sprites.png` 还是西洋棋贴图。
- `client/src/game/sprites.ts` 只是临时把 象→bishop、士→queen、将→king、炮→rook 做了占位映射。
- `client/src/pages/Game.tsx` 与 store 还只认识 3 秒倒计时，不认识阶段解锁。

### 2.7 仓库清洁度也有问题
- `client/App.tsx / analytics.ts / config.ts / main.tsx / vite-env.d.ts` 与 `client/src/` 下同名文件重复。
- 提交了 `coverage_report.txt`。
- 提交了大量 `__pycache__`。
- `CLAUDE.md`、`DEPLOYMENT.md`、部分脚本与文档仍带旧项目名 / 旧仓库名 / 旧部署口径。

## 3. 明确的修改顺序（你要求的顺序）

1. **先写死规则真源**：README + `docs/XIANGQI_BACKEND_REFACTOR.md` + `docs/ARCHITECTURE.md`。
2. **再冻结与首版无关的旧模块**：campaign、旧 AI、4-player 残留、旧测试。
3. **再改后端内核**：state / engine / game_service / api / ws / replay。
4. **最后才改前端**：协议类型、store、Game 页面、棋盘渲染、素材替换。
5. **最后补测试与部署文档**。

## 4. 后端实现应该怎么改（不是泛泛而谈，而是明确到结构）

### 4.1 `GameState` 需要新增的字段
至少新增这些：
- `ruleset_version: str` —— 例如 `phase_standard_v1`
- `phase_index: int` —— 当前处于第几个阶段
- `phase_started_tick: int`
- `next_phase_tick: int | None`
- `opening_freeze_end_tick: int`
- `player_unlocked_types: dict[int, set[str]]` —— 每个玩家已解锁棋种
- `pending_unlock_choices: dict[int, UnlockChoiceState]` —— 当前窗口内该玩家还能选什么
- `piece_type_cooldowns: dict[str, int]` —— 每种棋子的冷却 tick
- `phase_events: list[...]` —— 供 WS 广播和 replay 记录

### 4.2 REST / WS 至少要新增的字段
对局状态里至少要带：
- `ruleset_version`
- `phase_name`
- `phase_remaining_ticks`
- `player_unlocked_types`
- `available_unlock_choices`（仅当前玩家可见）
- `next_unlock_at_tick`
- `piece_base_cooldown_ticks`
- `cooldown_remaining_ticks`（单棋子现有字段可继续保留）

并且新增客户端动作：
- `select_unlock` / `choose_unlock_type`

### 4.3 replay 必须一起改
因为你的玩法核心不是单纯‘移动’，而是‘阶段 + 解锁 + 冷却’。
所以 replay 至少要记录：
- 阶段切换事件
- 玩家解锁选择事件
- 规则版本
- 每类棋子基础冷却配置

## 5. 文件级修改方案（全仓库）

说明：下面是**全文件级**处置建议。字段含义：
- **阶段**：P0 清理 / P1 文档 / P2 后端 / P4 前端 / P5 测试
- **动作**：删除 / 重写 / 局部重写 / 冻结 / 保留
- **说明**：我认为该文件这轮应该怎么处理

### 5.0 先清掉这些缓存目录
- `server/src/kfchess/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/ai/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/api/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/auth/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/campaign/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/db/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/db/repositories/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/game/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/lobby/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/redis/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/replay/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/services/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/utils/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/src/kfchess/ws/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。
- `server/tests/__pycache__` —— **删除**。提交缓存目录没有意义，会污染 diff。

### README.md
- `README.md` —— **P1 规则/文档 / 重写**：把玩法规则、阶段解锁、冷却、胜负、已实现范围写成唯一真源。

### CLAUDE.md
- `CLAUDE.md` —— **P1 文档清理 / 重写**：项目名、命令说明、规则描述仍带旧 Kung Fu Chess 语义。

### LICENSE
- `LICENSE` —— **保持 / 保留**：许可证无需因玩法改动而修改。

### docker-compose.yml
- `docker-compose.yml` —— **P2 支撑 / 局部重写**：如引入新环境变量/规则配置，需要补服务启动配置。

### docs
- `docs/AI_DESIGN.md` —— **P1/P2 冻结 / 冻结/重写**：AI 文档仍按旧棋理写，首版先只保留 DummyAI。
- `docs/ARCHITECTURE.md` —— **P1 文档清理 / 重写**：当前结构图、棋盘尺寸、协议、棋子类型全混旧语义。
- `docs/AUTHENTICATION_DESIGN.md` —— **P1 文档同步 / 局部重写**：核心功能可保留，但项目名/规则口径/引用路径要统一。
- `docs/CAMPAIGN_DESIGN.md` —— **P1 文档清理 / 冻结/重写**：整篇仍是国际象棋 campaign 设计。
- `docs/DEPLOYMENT.md` —— **P1 文档清理 / 局部重写**：项目名/仓库 URL/旧 kfchess 数据迁移表述需清理。
- `docs/ELO_RATING_DESIGN.md` —— **P1 文档同步 / 局部重写**：核心功能可保留，但项目名/规则口径/引用路径要统一。
- `docs/LOBBY_DESIGN.md` —— **P1/P2 文档同步 / 局部重写**：创建房间与开局流程要接入阶段规则，不是简单 3 秒倒计时。
- `docs/MULTI_SERVER_DESIGN.md` —— **P1 文档同步 / 局部重写**：核心功能可保留，但项目名/规则口径/引用路径要统一。
- `docs/MVP_IMPLEMENTATION.md` —— **P1 文档清理 / 重写**：8x8/4-player/升变/易位等旧设计必须全部收口。
- `docs/PROFILE_PICTURES_DESIGN.md` —— **P1 文档同步 / 局部重写**：核心功能可保留，但项目名/规则口径/引用路径要统一。
- `docs/REPLAY_DESIGN.md` —— **P1/P2 文档同步 / 局部重写**：回放协议要增加阶段与解锁事件。
- `docs/WEBSOCKET_STATE_OPTIMIZATION.md` —— **P1 文档同步 / 局部重写**：核心功能可保留，但项目名/规则口径/引用路径要统一。
- `docs/XIANGQI_BACKEND_REFACTOR.md` —— **P1 规则/文档 / 重写**：升级成正式《规则规格说明 + 后端改造计划》，不能只是薄说明。

### scripts
- `scripts/dev-servers.sh` —— **保持 / 保留**：玩法无关。
- `scripts/dev.sh` —— **保持 / 保留**：玩法无关。
- `scripts/migrate.sh` —— **保持 / 保留**：玩法无关。
- `scripts/restart-dev.sh` —— **P1 文档清理 / 局部重写**：命令说明仍带 kfchess 旧关键词，可顺手清理。

### deploy
- `deploy/Caddyfile` —— **保持 / 保留**：玩法不影响反向代理。
- `deploy/bootstrap.sh` —— **保持 / 保留**：除非新增环境变量模板。
- `deploy/config.sh` —— **P2 支撑 / 局部重写**：若增加规则配置 env，需要同步。
- `deploy/deploy.sh` —— **保持 / 保留**：部署流程本身不因玩法改。
- `deploy/docker-compose.prod.yml` —— **P2 支撑 / 局部重写**：若新增规则 env，需要同步。
- `deploy/e2e-deploy.sh` —— **保持 / 保留**：除非新增启动前健康检查。
- `deploy/generate-caddyfile.sh` —— **保持 / 保留**：不动。
- `deploy/migrate-legacy-data.sh` —— **P1 文档清理 / 局部重写**：说明仍是 legacy kfchess 迁移；需标明与新规则无关。
- `deploy/real-time-chess-battle-worker.sh` —— **保持 / 保留**：服务名已统一，可继续用。
- `deploy/sanity_check.py` —— **P2 支撑 / 局部重写**：可增加规则版本/phase 接口健康检查。
- `deploy/systemd/real-time-chess-battle@.service` —— **保持 / 保留**：仅当环境变量增改时调整。

### server
- `server/README.md` —— **P1 文档清理 / 局部重写**：补后端启动方式、规则版本、当前下线模块说明。
- `server/alembic/env.py` —— **P2 支撑 / 按模型变更决定**：迁移脚手架保持不动，除非数据库模型调整。
- `server/alembic/script.py.mako` —— **P2 支撑 / 按模型变更决定**：迁移脚手架保持不动，除非数据库模型调整。
- `server/alembic/versions/001_add_game_replays.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/002_add_users.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/003_add_lobbies.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/004_add_lobby_performance_indexes.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/005_add_elo_rating_system.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/006_add_legacy_replay_tables.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/007_update_leaderboard_indexes.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/008_add_replay_likes.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/009_add_replay_is_ranked.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/010_add_replay_top_index.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/011_add_campaign_progress.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/012_add_replay_campaign_level.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/013_add_replay_initial_board.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/014_add_active_games.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/015_replay_browse_indexes.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/177687c383a4_add_tick_rate_hz_to_game_replays.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic/versions/1832246a958d_merge_heads.py` —— **P2 支撑 / 按模型变更决定**：仅当新增/修改持久化字段时补迁移；否则不改。
- `server/alembic.ini` —— **P2 支撑 / 保留**：除非新增表字段，一般不动。
- `server/coverage_report.txt` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `server/pyproject.toml` —— **P2 支撑 / 局部重写**：若移除旧 AI/下线 campaign/补测试命令，需要同步脚本和依赖。
- `server/scripts/cleanup_active_games.py` —— **P2 支撑 / 局部重写**：如游戏状态字段变化，脚本序列化/清理逻辑要同步。
- `server/scripts/profile_4p_ai.py` —— **P2 支撑 / 局部重写**：如游戏状态字段变化，脚本序列化/清理逻辑要同步。
- `server/scripts/seed_dev_user.py` —— **P2 支撑 / 局部重写**：如游戏状态字段变化，脚本序列化/清理逻辑要同步。
- `server/src/kfchess/__init__.py` —— **P2 支撑 / 局部重写**：需要按新规则检查是否受影响。
- `server/src/kfchess/ai/__init__.py` —— **P2 后端服务 / 局部重写**：仅保留 DummyAI 主链路；其余 AI 能力先冻结。
- `server/src/kfchess/ai/arrival_field.py` —— **P1/P2 冻结 / 冻结**：旧西洋棋 AI 逻辑首版不参与对局。
- `server/src/kfchess/ai/base.py` —— **P2 后端服务 / 局部重写**：仅保留 DummyAI 主链路；其余 AI 能力先冻结。
- `server/src/kfchess/ai/controller.py` —— **P2 后端服务 / 局部重写**：仅保留 DummyAI 主链路；其余 AI 能力先冻结。
- `server/src/kfchess/ai/dummy.py` —— **P2 后端服务 / 局部重写**：仅保留 DummyAI 主链路；其余 AI 能力先冻结。
- `server/src/kfchess/ai/eval.py` —— **P1/P2 冻结 / 冻结**：旧西洋棋 AI 逻辑首版不参与对局。
- `server/src/kfchess/ai/kungfu_ai.py` —— **P2 后端服务 / 局部重写**：仅保留 DummyAI 主链路；其余 AI 能力先冻结。
- `server/src/kfchess/ai/move_gen.py` —— **P1/P2 冻结 / 冻结**：旧西洋棋 AI 逻辑首版不参与对局。
- `server/src/kfchess/ai/state_extractor.py` —— **P1/P2 冻结 / 冻结**：旧西洋棋 AI 逻辑首版不参与对局。
- `server/src/kfchess/ai/tactics.py` —— **P1/P2 冻结 / 冻结**：旧西洋棋 AI 逻辑首版不参与对局。
- `server/src/kfchess/api/__init__.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/campaign.py` —— **P1/P2 冻结 / 冻结/下线**：如果继续暴露 campaign 接口，会把旧规则带回系统。
- `server/src/kfchess/api/games.py` —— **P2 后端接口 / 重写**：REST 返回解锁状态、阶段时间、棋子冷却、可选解锁项；创建参数也要收口。
- `server/src/kfchess/api/leaderboard.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/lobbies.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/replays.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/router.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/users.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/api/webhooks.py` —— **P2 后端接口 / 局部重写**：REST/序列化层要与新规则/下线模块对齐。
- `server/src/kfchess/auth/__init__.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/backend.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/dependencies.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/email.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/lichess.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/rate_limit.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/router.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/schemas.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/auth/users.py` —— **保持 / 保留**：认证系统与玩法解耦，除命名清理外不应改。
- `server/src/kfchess/campaign/__init__.py` —— **P1/P2 冻结 / 冻结/下线**：campaign 模块当前不可信，首版先冻结。
- `server/src/kfchess/campaign/board_parser.py` —— **P1/P2 冻结 / 冻结/重做**：仍是 8x8 国际象棋解析器；当前版本应先禁用 campaign。
- `server/src/kfchess/campaign/levels.py` —— **P1/P2 冻结 / 冻结/重做**：关卡内容完全是旧国际象棋，先下线再重做。
- `server/src/kfchess/campaign/models.py` —— **P1/P2 冻结 / 冻结/下线**：campaign 模块当前不可信，首版先冻结。
- `server/src/kfchess/campaign/service.py` —— **P1/P2 冻结 / 冻结/下线**：依赖旧关卡模型，先不参与首版规则。
- `server/src/kfchess/db/__init__.py` —— **P2 支撑 / 按模型变更决定**：数据库模型仅在需持久化新规则元数据时调整。
- `server/src/kfchess/db/models.py` —— **P2 支撑 / 按模型变更决定**：数据库模型仅在需持久化新规则元数据时调整。
- `server/src/kfchess/db/repositories/__init__.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/active_games.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/campaign.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/lobbies.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/replay_likes.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/replays.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/user_game_history.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/repositories/users.py` —— **P2 支撑 / 按模型变更决定**：若 live game / replay 需要持久化新字段，则同步仓储层。
- `server/src/kfchess/db/session.py` —— **P2 支撑 / 按模型变更决定**：数据库模型仅在需持久化新规则元数据时调整。
- `server/src/kfchess/drain.py` —— **P2 支撑 / 局部重写**：需要按新规则检查是否受影响。
- `server/src/kfchess/game/__init__.py` —— **P2 后端核心 / 局部重写**：游戏内核目录；需按新规则逐文件核对。
- `server/src/kfchess/game/board.py` —— **P2 后端核心 / 局部重写**：游戏内核目录；需按新规则逐文件核对。
- `server/src/kfchess/game/collision.py` —— **P2 后端核心 / 局部重写**：把碰撞/同 tick 对撞写成明确规则，并与回放/事件保持一致。
- `server/src/kfchess/game/elo.py` —— **P2 后端核心 / 局部重写**：游戏内核目录；需按新规则逐文件核对。
- `server/src/kfchess/game/engine.py` —— **P2 后端核心 / 重写**：接入解锁阶段、分类型冷却、阶段推进、解锁选择、胜负/和棋规则。
- `server/src/kfchess/game/moves.py` —— **P2 后端核心 / 局部重写**：保留象棋走法骨架，补规则注释、禁手边界和实时规则判定接口。
- `server/src/kfchess/game/pieces.py` —— **P2 后端核心 / 局部重写**：补 piece class 元数据、基础冷却映射、可解锁类型语义。
- `server/src/kfchess/game/replay.py` —— **P2 后端核心 / 局部重写**：回放数据模型要记录规则版本、解锁事件、阶段选择。
- `server/src/kfchess/game/snapshot.py` —— **P2 后端核心 / 局部重写**：游戏内核目录；需按新规则逐文件核对。
- `server/src/kfchess/game/state.py` —— **P2 后端核心 / 重写**：新增规则预设、阶段解锁状态、每类棋子冷却、阶段事件/选择窗口。
- `server/src/kfchess/lobby/__init__.py` —— **P2 后端服务 / 局部重写**：房间设置与开局流程要接入规则预设。
- `server/src/kfchess/lobby/manager.py` —— **P2 后端服务 / 局部重写**：房间设置与开局流程要接入规则预设。
- `server/src/kfchess/lobby/models.py` —— **P2 后端服务 / 局部重写**：房间设置与开局流程要接入规则预设。
- `server/src/kfchess/main.py` —— **P2 支撑 / 局部重写**：需要按新规则检查是否受影响。
- `server/src/kfchess/redis/__init__.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/redis/client.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/redis/heartbeat.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/redis/lobby_store.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/redis/routing.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/redis/snapshot_store.py` —— **P2 支撑 / 局部重写**：若 snapshot/routing 载荷新增字段，要同步序列化。
- `server/src/kfchess/replay/__init__.py` —— **P2 后端服务 / 局部重写**：回放层要认识 phase/unlock 元数据。
- `server/src/kfchess/replay/session.py` —— **P2 后端接口 / 重写**：回放必须能复原阶段解锁、分类型冷却与阶段事件。
- `server/src/kfchess/services/__init__.py` —— **P2 后端服务 / 局部重写**：服务层需同步新规则流转、AI策略和持久化。
- `server/src/kfchess/services/game_registry.py` —— **P2 后端服务 / 局部重写**：服务层需同步新规则流转、AI策略和持久化。
- `server/src/kfchess/services/game_service.py` —— **P2 后端核心 / 重写**：游戏创建、选将阶段指令、AI 降级、ready/start 逻辑都要适配新规则。
- `server/src/kfchess/services/rating_service.py` —— **P2 后端服务 / 局部重写**：服务层需同步新规则流转、AI策略和持久化。
- `server/src/kfchess/services/s3.py` —— **P2 后端服务 / 局部重写**：服务层需同步新规则流转、AI策略和持久化。
- `server/src/kfchess/services/stats.py` —— **P2 后端服务 / 局部重写**：服务层需同步新规则流转、AI策略和持久化。
- `server/src/kfchess/settings.py` —— **P2 支撑 / 局部重写**：需要按新规则检查是否受影响。
- `server/src/kfchess/utils/__init__.py` —— **保持 / 保留**：除显示文案/命名清理外不动。
- `server/src/kfchess/utils/display_name.py` —— **保持 / 保留**：除显示文案/命名清理外不动。
- `server/src/kfchess/ws/__init__.py` —— **P2 后端接口 / 局部重写**：WebSocket 层要同步新状态字段与事件。
- `server/src/kfchess/ws/game_loop.py` —— **P2 后端接口 / 局部重写**：WebSocket 层要同步新状态字段与事件。
- `server/src/kfchess/ws/handler.py` —— **P2 后端接口 / 重写**：当前只有 3 秒 countdown；要改成阶段驱动广播与解锁选择处理。
- `server/src/kfchess/ws/lobby_handler.py` —— **P2 后端接口 / 局部重写**：WebSocket 层要同步新状态字段与事件。
- `server/src/kfchess/ws/protocol.py` —— **P2 后端接口 / 重写**：新增 phase/unlock_choice 消息与字段，3 秒 countdown 模型要改。
- `server/src/kfchess/ws/replay_handler.py` —— **P2 后端接口 / 局部重写**：WebSocket 层要同步新状态字段与事件。
- `server/tests/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/conftest.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/conftest.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/test_dev_mode.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/test_google_oauth.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/test_login_flow.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/auth/test_registration_flow.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/conftest.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_active_game_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_campaign_flow.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_campaign_replay.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_campaign_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_lobby_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_multi_server.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_rating_service.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_replay_likes_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_replay_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/integration/test_user_game_history_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/test_health.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_ai_harness.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_arrival_field.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_eval.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_kungfu_ai.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_move_gen.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_state_extractor.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ai/test_tactics.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/api/test_campaign.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/api/test_leaderboard.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/api/test_webhooks.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/conftest.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/test_dependencies.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/test_email.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/test_lichess.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/test_schemas.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/auth/test_users.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/campaign/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/campaign/test_board_parser.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/campaign/test_levels.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/campaign/test_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/campaign/test_service.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_elo.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_engine.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_pieces.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_replay.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_snapshot.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/game/test_xiangqi_backend.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/lobby/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_claim_routing.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_client.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_heartbeat.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_lobby_serialization.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_lobby_store.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_routing.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/redis/test_snapshot_store.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/replay/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/replay/test_session.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_api_games.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_api_lobbies.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_api_users.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_drain.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_drain_mode.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_drain_shutdown.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_game_restore.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_game_service.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_game_service_campaign.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_lobby_websocket.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_rating_service.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_replay_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_routing_registration.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_s3_service.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_startup_restore.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_upload_picture.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_user_game_history_repository.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/test_websocket.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/utils/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/utils/test_display_name.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/__init__.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_handler.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_handler_crash_recovery.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_handler_drain.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_handler_routing.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_handler_snapshot.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_lobby_handler_drain.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/tests/unit/ws/test_protocol.py` —— **P5 测试 / 重写/删改**：测试口径必须与新规则一致；旧国际象棋断言要清理。
- `server/uv.lock` —— **P2 支撑 / 随依赖变更更新**：仅在 pyproject 依赖变更后刷新锁文件。

### client
- `client/App.tsx` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/analytics.ts` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/config.ts` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/coverage_report.txt` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/eslint.config.js` —— **保持 / 保留**：规则无直接关系。
- `client/index.html` —— **P4 前端 / 局部重写**：如需阶段图标/SEO 文案更新，再改。
- `client/main.tsx` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/package-lock.json` —— **P4 前端 / 随 package.json 更新**：依赖变更后自动刷新。
- `client/package.json` —— **P4 前端 / 局部重写**：如加入新 UI 组件或去除无用脚本，需同步。
- `client/src/App.tsx` —— **P4 前端 / 局部重写**：前端源文件后期统一检查。
- `client/src/analytics.ts` —— **P4 前端 / 局部重写**：前端源文件后期统一检查。
- `client/src/api/client.ts` —— **P4 前端 / 局部重写**：REST 类型和客户端要对齐新后端。
- `client/src/api/index.ts` —— **P4 前端 / 局部重写**：REST 类型和客户端要对齐新后端。
- `client/src/api/types.ts` —— **P4 前端 / 重写**：REST 类型要加入规则版本、阶段状态、候选解锁项。
- `client/src/assets/chess-sprites.png` —— **P4 前端 / 替换**：旧西洋棋贴图；后期替换为中国象棋贴图。
- `client/src/components/AuthProvider.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/BeltIcon.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/Leaderboard.css` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/Leaderboard.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/PlayerBadge.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/ReplayCard.css` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/ReplayCard.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/campaign/BeltSelector.css` —— **P4 前端 / 冻结/下线**：campaign 前端应跟随后端一并冻结。
- `client/src/components/campaign/BeltSelector.tsx` —— **P4 前端 / 冻结/下线**：campaign 前端应跟随后端一并冻结。
- `client/src/components/campaign/LevelGrid.css` —— **P4 前端 / 冻结/下线**：campaign 前端应跟随后端一并冻结。
- `client/src/components/campaign/LevelGrid.tsx` —— **P4 前端 / 冻结/下线**：campaign 前端应跟随后端一并冻结。
- `client/src/components/campaign/index.ts` —— **P4 前端 / 冻结/下线**：campaign 前端应跟随后端一并冻结。
- `client/src/components/game/AudioControls.css` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/AudioControls.tsx` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/DrawOfferButton.tsx` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/GameBoard.tsx` —— **P4 前端 / 重写**：要显示阶段条、解锁状态、候选高亮、棋子冷却差异。
- `client/src/components/game/GameOverModal.tsx` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/GameStatus.tsx` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/ResignButton.tsx` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/game/index.ts` —— **P4 前端 / 局部重写**：对局 UI 必须等后端协议稳定后再改。
- `client/src/components/layout/Header.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/layout/Layout.tsx` —— **保持/后期局部改 / 保留**：排行榜、布局、认证等与玩法弱耦合。
- `client/src/components/replay/ReplayBoard.tsx` —— **P4 前端 / 局部重写**：回放 UI 要展示 phase/unlock。
- `client/src/components/replay/ReplayControls.css` —— **P4 前端 / 局部重写**：回放 UI 要展示 phase/unlock。
- `client/src/components/replay/ReplayControls.tsx` —— **P4 前端 / 局部重写**：回放 UI 要展示 phase/unlock。
- `client/src/components/replay/index.ts` —— **P4 前端 / 局部重写**：回放 UI 要展示 phase/unlock。
- `client/src/config.ts` —— **P4 前端 / 局部重写**：前端源文件后期统一检查。
- `client/src/game/constants.ts` —— **P4 前端 / 重写**：改为规则驱动常量，不再写死 standard/lightning 单一全局冷却。
- `client/src/game/index.ts` —— **P4 前端 / 局部重写**：棋盘渲染/交互核心，后期统一适配 phase 规则。
- `client/src/game/interpolation.ts` —— **P4 前端 / 局部重写**：棋盘渲染/交互核心，后期统一适配 phase 规则。
- `client/src/game/moves.ts` —— **P4 前端 / 局部重写**：前端判定需增加“是否已解锁”的门禁；走法骨架可保留。
- `client/src/game/renderer.ts` —— **P4 前端 / 局部重写**：棋盘渲染/交互核心，后期统一适配 phase 规则。
- `client/src/game/sprites.ts` —— **P4 前端 / 重写**：当前仍拿西洋棋贴图占位，后面必须替换中国象棋素材。
- `client/src/hooks/useAudio.ts` —— **保持/后期局部改 / 保留**：通用 hook 大多不用先动。
- `client/src/hooks/useSquareSize.ts` —— **保持/后期局部改 / 保留**：通用 hook 大多不用先动。
- `client/src/main.tsx` —— **P4 前端 / 局部重写**：前端源文件后期统一检查。
- `client/src/pages/About.css` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/About.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Campaign.css` —— **P4 前端 / 局部重写**：游戏/回放/战役页面需按新规则重做或冻结。
- `client/src/pages/Campaign.tsx` —— **P4 前端 / 局部重写**：游戏/回放/战役页面需按新规则重做或冻结。
- `client/src/pages/ForgotPassword.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Game.css` —— **P4 前端 / 局部重写**：游戏/回放/战役页面需按新规则重做或冻结。
- `client/src/pages/Game.tsx` —— **P4 前端 / 重写**：把 3 秒倒计时 UI 改为整局阶段流和解锁选择面板。
- `client/src/pages/GoogleCallback.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Home.css` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Home.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/LichessCallback.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Lobbies.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Lobby.css` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Lobby.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Login.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Privacy.css` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Privacy.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Profile.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Register.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Replay.css` —— **P4 前端 / 局部重写**：游戏/回放/战役页面需按新规则重做或冻结。
- `client/src/pages/Replay.tsx` —— **P4 前端 / 局部重写**：游戏/回放/战役页面需按新规则重做或冻结。
- `client/src/pages/ResetPassword.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Verify.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Watch.css` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/pages/Watch.tsx` —— **保持 / 保留**：登录、首页、隐私等与玩法弱耦合，暂不动。
- `client/src/stores/auth.ts` —— **P4 前端 / 局部重写**：状态管理要兼容 phase/unlock/cooldown。
- `client/src/stores/campaign.ts` —— **P4 前端 / 局部重写**：状态管理要兼容 phase/unlock/cooldown。
- `client/src/stores/game.ts` —— **P4 前端 / 重写**：当前只懂 playing/countdown/global cooldown，不懂阶段解锁。
- `client/src/stores/lobby.ts` —— **P4 前端 / 局部重写**：状态管理要兼容 phase/unlock/cooldown。
- `client/src/stores/replay.ts` —— **P4 前端 / 局部重写**：状态管理要兼容 phase/unlock/cooldown。
- `client/src/styles/index.css` —— **保持 / 保留**：全局样式无须先动。
- `client/src/utils/displayName.ts` —— **保持/后期局部改 / 局部重写**：只在对局文案或评分显示受影响时调整。
- `client/src/utils/format.ts` —— **保持/后期局部改 / 局部重写**：只在对局文案或评分显示受影响时调整。
- `client/src/utils/ratings.ts` —— **保持/后期局部改 / 局部重写**：只在对局文案或评分显示受影响时调整。
- `client/src/vite-env.d.ts` —— **P4 前端 / 局部重写**：前端源文件后期统一检查。
- `client/src/ws/client.ts` —— **P4 前端 / 局部重写**：协议层要认识新字段。
- `client/src/ws/index.ts` —— **P4 前端 / 局部重写**：协议层要认识新字段。
- `client/src/ws/types.ts` —— **P4 前端 / 重写**：协议字段要跟后端 phase/unlock 事件同步。
- `client/tests/components/Campaign.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/DrawOfferButton.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/GameOverModal.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/Home.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/LichessCallback.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/Lobbies.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/Lobby.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/Login.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/PlayerBadge.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/Register.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/components/ResignButton.test.tsx` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/game/constants.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/game/interpolation.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/game/moves.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/setup.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/stores/campaign.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/stores/game.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/stores/lobby.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/stores/replay.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/utils/ratings.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tests/ws/client.test.ts` —— **P5 测试 / 重写/删改**：前端测试需跟协议和规则同步。
- `client/tsconfig.json` —— **保持 / 保留**：除非路径/生成目录再调整。
- `client/tsconfig.node.json` —— **保持 / 保留**：暂不动。
- `client/vite-env.d.ts` —— **P0 清理 / 删除**：重复文件或测试产物，不应继续留在仓库。
- `client/vite.config.ts` —— **P4 前端 / 局部重写**：如静态资源路径或代理说明变化，再改。
