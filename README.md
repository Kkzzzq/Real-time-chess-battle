# Realtime Xiangqi Demo

这是一个**第一版可运行的核心项目骨架**，目标不是做完整商业成品，而是把你定义的关键玩法先落成一个干净、可扩展、能直接继续迭代的 Python 项目：

- 双人
- 9×10 中国象棋标准开局
- 无回合制实时指令
- 阶段解锁
- 按棋种冷却
- 基础连续移动与碰撞结算
- WebSocket 实时状态广播
- 最小调试前端 `/demo`

## 已实现的核心规则

### 1. 对局目标
- 红方在下（P1）
- 黑方在上（P2）
- 直接吃掉对方将/帅即胜
- 支持飞将吃将
- 禁止将帅隔空照面

### 2. 实时总则
- 无回合，双方可同时下达指令
- 同一方可以同时操作多个不同棋子
- 同一个棋子不能排队指令
- 棋子必须满足：已解锁、未移动、未冷却、走法合法

### 3. 阶段解锁
- 0s ~ 30s：封盘期，不能移动
- 30s ~ 50s：仅兵/卒可动
- 50s / 70s / 90s / 110s：进入解锁窗口
- 130s：全部自动解锁
- 自动优先级：炮 > 马 > 车 > 象 > 士 > 将/帅
- 每一方独立选择，不互相绑定

### 4. 冷却
- 兵/卒：10s
- 士：8s
- 象：15s
- 马：20s
- 炮：20s
- 车：30s
- 将/帅：3s

### 5. 移动时间
- 直线棋：1 格 = 1 秒
- 马：2 秒
- 象：2 秒
- 士 / 兵 / 将帅普通单步：1 秒
- 飞将：按直线格数计算

### 6. 碰撞规则
- 移动 vs 静止：移动方获胜
- 移动 vs 移动：先启动者获胜；同 tick 正面相撞同归于尽

### 7. 和棋
- 150s 前不判和
- 150s 后：
  - 连续 60s 无新合法出手，判和
  - 或连续 90s 无吃子，判和
- 任一玩家投降则负

## 项目结构

```text
realtime_xiangqi_demo/
├─ app/
│  ├─ api/
│  │  ├─ routes.py          # HTTP / WebSocket 接口
│  │  └─ schemas.py         # 请求模型
│  ├─ domain/
│  │  ├─ enums.py           # 枚举、冷却、棋子显示字
│  │  └─ models.py          # 核心数据模型
│  ├─ engine/
│  │  ├─ board_setup.py     # 标准开局
│  │  ├─ collision.py       # 实时碰撞结算
│  │  ├─ game.py            # 对局状态机 / tick 驱动
│  │  ├─ manager.py         # 多对局管理与广播
│  │  ├─ rules.py           # 中国象棋走法校验
│  │  └─ unlock.py          # 阶段解锁逻辑
│  ├─ static/
│  │  └─ index.html         # 最小调试页
│  └─ main.py               # FastAPI 入口
├─ tests/
│  └─ test_unlock_and_rules.py
├─ requirements.txt
└─ README.md
```

## 运行方式

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload
```

### 3. 打开页面

浏览器访问：

```text
http://127.0.0.1:8000/demo
```

## 接口说明

### 创建对局
```http
POST /matches
```

### 获取状态
```http
GET /matches/{match_id}
```

### 下达移动指令
```http
POST /matches/{match_id}/move
Content-Type: application/json

{
  "player": 1,
  "piece_id": "p1_soldier_1",
  "target_x": 0,
  "target_y": 5
}
```

### 手动解锁
```http
POST /matches/{match_id}/unlock
Content-Type: application/json

{
  "player": 1,
  "piece_type": "cannon"
}
```

### 投降
```http
POST /matches/{match_id}/resign
Content-Type: application/json

{
  "player": 1
}
```

### WebSocket
```text
/ws 路径：/matches/{match_id}/ws
```

WebSocket 指令格式：

```json
{ "type": "move", "player": 1, "piece_id": "p1_soldier_1", "target_x": 0, "target_y": 5 }
{ "type": "unlock", "player": 1, "piece_type": "cannon" }
{ "type": "resign", "player": 1 }
```

## 当前版本的刻意简化

这是第一版核心框架，已经能跑，但不是最终规则终稿。下面这些点我保留成后续迭代项：

1. **碰撞仍是近似实时模型**
   - 已有连续坐标、tick 更新、移动 vs 移动 / 静止判定。
   - 但还不是严格物理引擎。

2. **移动中的棋子不参与传统路径阻挡**
   - 当前走法校验主要基于“静止棋子”。
   - 这样更适合先把实时主循环跑通。

3. **前端只是调试页**
   - 目的是让你现在就能点着玩、看状态流转。
   - 不是正式 UI。

4. **没有房间权限和登录体系**
   - Demo 阶段直接用 `player=1/2` 操作。

## 下一步建议

你把现有内容删掉以后，可以直接按这个项目骨架接着往下迭代。后续建议顺序：

1. 先把你现有仓库替换成这套目录结构
2. 先跑通 `/demo`
3. 再补更严格的实时碰撞与路径占用
4. 再补正式前端
5. 最后做观战、重连、房间匹配、录像回放
