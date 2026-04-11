Q版国风战棋资源包

说明：
1. 该资源包按页面与系统模块分目录整理。
2. 核心风格为：简约国风、正常Q版、轻古风、非低幼。
3. 文件命名与之前整理的资源框架一一对应，便于直接替换到前端项目。

主要目录：
- common: 通用背景、纹理、装饰、logo
- ui: 按钮、面板、图标、徽章
- lobby: 大厅页面资源
- room: 房间页面资源
- game: 对局页面外框与面板
- board: 棋盘、格子、高亮、特效、阴影
- pieces: 棋子 token、头像、图标、状态
- system: 解锁、阶段、事件、连接、结果、提示
- optional: 预留目录

建议优先接入：
1. board/base + board/cells
2. pieces/tokens
3. ui/buttons + ui/panels
4. lobby/background + room/background + game/background
