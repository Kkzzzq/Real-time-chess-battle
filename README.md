# Real-time Chess Battle (Realtime Xiangqi Sample)

基于 FastAPI 的中国象棋实时玩法样本，按你给出的规则实现核心框架：

- 无回合并发下指令
- 分阶段解锁（30s 兵线、50/70/90/110 选择、130 全解锁）
- 棋种冷却与移动时长
- 中国象棋核心走法（含蹩马腿、塞象眼、炮架、飞将）
- 将帅不能隔空照面
- 实时碰撞（移动吃静止、移动撞移动按先后）
- 150s 后和棋判定（60s 无出手 / 90s 无吃子）

## 启动

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

访问：

- `GET /demo`：最小调试页面
- `POST /matches`：创建对局
- `GET /matches/{match_id}`：获取状态
- `POST /matches/{match_id}/move`
- `POST /matches/{match_id}/unlock`
- `POST /matches/{match_id}/resign`
- `WS /matches/{match_id}/ws`

## 测试

```bash
pytest -q
```
