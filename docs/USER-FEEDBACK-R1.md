# 用户反馈 R1（2026-10-20 手测）—— 问题清单与修复状态

> 来源：用户实测截图 + 描述。状态：✅ 已修并验证｜🔄 进行中｜⏳ 待做

| # | 问题 | 归属 | 状态 | 证据/说明 |
|---|---|---|---|---|
| 1 | 设置→辅助功能设置 偶发崩溃（1 次，未复现） | lead+probe | ⏳ | 待复现抓 crasherror |
| 2 | 任务书 UI 不可用：仅蓝框可点、章节列表不可点、底部按钮不可用 | ponder | ✅ | v2 已合并：章节列表可见可翻页（`<-`/`->`+方向键）、当前章 `> `、任务格高亮、四按钮可见、锁定提示中文；鼠标点击注入待手测 |
| 3 | 「一碰就崩」实为 createframed 滑动门放置崩溃 | crashfix | ✅ | 根因 BE 类型校验失败；修后放置 0 崩溃、门可开关（crashfix 1.0.1） |
| 4 | Create 机械冲压机不工作（C-2） | crashfix | ✅✅ | 根因配方为 0（已补 1607 条）；**mcpfabric 真实链路实测 PASS**：motor+shaft+press 网络 Speed=-16、Running=1、Finished=1，4 铜锭→2 铜板（depot 读回 copper_sheet）；注意 `create:copper_ingot` 不存在，用 `minecraft:copper_ingot` |
| 5 | 机械动力相关模组方块大量显示错误/破碎 | aero | ✅（已修项） | 已修并验：create_connected 紫黑 23、dndecor 165（按颜色）、createdeco 32（catwalk/decal）、slice 半透明、TFMG 火把、aeroworks 34 图标、corndelight/culturaldelights 缺模型；`model problems=0`（copycats 平铺为已知降级） |
| 6 | 大量物品名显示 raw key | aero | ✅ | L1+L2 共 28 件已合并（createdeco/aeroworks/CEI/DP/createframed/NS/tfmg/ends_delight 等）；实测「黑色边框玻璃门/紫颂曲奇/安山岩门/黑色牌匾」全中文 |
| 7 | 装饰门：半扇空心/极端视角消失 | crashfix | ✅ | port.21 已合并：放置出双半、右击 `open=true`、敲上半两半全 air |
| 8 | 装饰牌匾：只能朝上放 | crashfix | ✅ | port.21：贴墙 `face=wall,facing=east` 通过（右键文本交互仍降级） |
| 9 | 思索界面英文未汉化 + 渲染异常 | ponder | ✅ | CEI 汉化已合并；**live 原样实测 R421 场景可见**（白平台+齿轮 3D、中文）；黑屏是 fix7–fix11 实验件破坏所致，已全部丢弃（LEDGER 死路 R660） |
| 10 | culturaldelights 食物不能吃 | aero | ✅✅ | 40 项 FoodProperties；**mcpfabric 真实进食 PASS**：survival+降 hunger 后 `control.startUsing` 3.5s，avocado_toast food 13→17/sat 0→1.4 且物品被消耗；apple 对照 14→20 |
| 11 | 装饰类只有栏杆符合要求，其余多数未测/不合格 | 持续 | 🔄 | 按用户后续反馈逐项修 |
| 12 | 机械搅拌器（mixer）放置即崩 | crashfix | ✅ | 根因：`SmartBlockEntity.initialize()` 首 tick 才注册客户端行为；1.0.3 在 setLevel 时补注册，mixer/whistle/cuckoo 均 0 崩溃 |
| - | C-1（Create 基础）正常；C-4 扳手可旋转动力轴承 | — | ✅ | 用户确认 |

## 已确认正常的项
- C-1 Create 基础方块可放置/可视；
- C-4 扳手对动力轴承可旋转。

## 用户明确提出的修复原则
- 门类：「直接把门改回被敲掉一格所有门都消失的效果」→ 双半联动，不允许半扇幽灵；
- 若有同类物品（活板门/栅栏门）一并修。