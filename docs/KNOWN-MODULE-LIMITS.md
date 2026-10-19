# KNOWN MODULE LIMITS — aero-fixer 负责范围

> 证据口径：MCP-first（`player.getState` / `world.getBlock` / `screenshot.take` / 日志 / `Missing model` 计数）。
> 状态：✅ 已实现且 probe 有证据｜⚠️ 降级（可放置/可见但无行为）｜❌ 未做/阻塞。

| 模块 | 已实现（有 MCP 证据） | 降级 / 无行为 | 待办 |
|---|---|---|---|
| **create_submarine** | 43 方块（3 ns：create_submarine 20 / create_high_seas 21 / create_abyss 2）+ 方块物品 + 单 tab；两域 Missing model=0；5/5 setblock→world.getBlock；SHA `e73e1421…`，base 109，staging 110 | ⚠️ 全部 blockstate/model 为 fallback cube_all；流体/BE/潜水控制/声呐/压载/氧气系统全无 | 行为分批；恢复原模型闭包；流体与 BE |
| **createpropulsion** | 33 方块 + 物品 + 单 tab；Missing model=0；5/5 读回；SHA `699f0373…`，base 111，staging 112 | ⚠️ 全部 fallback cube_all；推进器/引擎/线缆/铂系加工/流体全无 | 行为分批；推进与线缆 |
| **copycats** | 46 方块 + 物品 + tab；5/5 读回；copycats 域 Missing model=0；SHA `30d08a91…`，base 103，staging 104 | ⚠️ 平铺 cube_all；**copycat 模型/贴图/形状/动能/多重状态系统全无** | 真功能需移植 CopycatModelCore/渲染系统（大件） |
| **waystonessable** | Sable 组装/移动 waystone 数据保留 mixin；waystone 可放置/交互（`useWithoutItem=Success`）；SHA `cfd8caba…`，base 100，staging 101 | ⚠️ 仅 assembly mixin；原 mod 的网络/命令/35KB 兼容层（Create attached-check、子等级分类、传送守卫）未移植 | 实际组装移动手测；按需补 Create/Sable 兼容 |
| **sliceanddice** | 2 方块/4 物品；551 条 cutting 配方解析（`matched inputs=1`）；slicer 放入→真实配方→多份产出（`cutting produced 4 x experience_cake_slice`）；双入口 `useItemOn`/`useWithoutItem`；SHA `b92fad64…`，base 97，staging 97 | ⚠️ sprinkler/fertilizer 行为无；仅支持 `ingredient` 字符串/对象 + `results[{count,id}]` 最简配方格式 | 其余配方格式；sprinkler；产出动画/音效 |
| **aeroworks** | 8 方块 + 42 物品（8 方块物品 + 34 module）+ tab；control_desk/stand 右键只读面板；joystick 右键日志 `joystick input x/y`；SHA `22e8e4e1…`，base 94，staging 95 | ⚠️ 面板仅 Modules: 34 + Close；console 会话/模块配置/网络/servo/gyro 动力学/OBJ 模型全无 | console 真实会话；模块选择；OBJ→JSON/BER |
| **toolgun** | capture 11 / place 11 / 粒子预览 / printer GUI+打印+BER 静态桶；live `046A230D…` | ⚠️ printer BER 仅静态 barrel（无真实容器模型/动画）；blueprint 子系统未完成 | blueprint 批次；printer 容器模型与动画 |
| **quests sync** | S2C `QuestProgressPayload`；JOIN + complete/claim/reset 后发送；客户端 `ClientQuestProgress` + 显式回退；打开中 `refreshFromSync()`；两 UUID 隔离单测 `ISOLATION_OK`；probe 日志 `progress sync sent/received`、complete/claim ok；SHA `ecb9b802…`，base 98，staging 98 | ⚠️ **按钮实时刷新仅代码路径，probe 无法按键注入，待手验**；退出重进持久化未在单 run 自动验；跨章节依赖线（A①）未做 | Lead 手验 UI 刷新；relog 持久化；跨章节连线 |

## 通用降级模式

- **reduced 静态广度**：方块/物品/tab/资源可放置，但无 BE/动力学/流体/配方/自定义渲染；
- 所有 reduced 件打包前必须通过 **POST-JAR 递归模型断言**（blockstate variant/multipart → parent → jar/live/MC 三处），否则不交付；
- 语言：26.3 一次解析全部 mod lang，任一坏 JSON 全局失效；已加 `tools/lang_audit.py`。

## MCP 验证常用方法

`player.getState`、`world.getBlock`、`player.useBlock`（useItemOn + TryEmptyHand → useWithoutItem）、`player.interact`、`screenshot.take`、`chat.send {\"message\":\"...\"}`。