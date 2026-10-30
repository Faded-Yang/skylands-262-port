# 任务进度 S2C 同步（quests A②）

## 问题
`QuestScreen.updateButtons()` 直接读服务端静态 `QuestProgress`/`QuestLogic`；单人集成服同 JVM 正常，专用服务器客户端静态表为空 ⇒ 按钮锁定/领取状态错误。

## 实现
- `QuestProgressPayload`（S2C，`sky262quests:progress`）：手写 VarInt/UTF 流，条目格式与 SavedData 相同（`c:<questId>` / `r:<questId>`）；
- `QuestProgress.snapshot(UUID)`：只导出该玩家的 COMPLETED/CLAIMED；
- `QuestProgressSync.send(ServerPlayer)`：`ServerPlayConnectionEvents.JOIN` + complete/claim/reset 命令成功后调用；
- 客户端 `ClientQuestProgress` 缓存；`QuestScreen` **显式回退**：`hasData()` 为真用客户端缓存，否则用本地 `QuestProgress`（单人行为不变）；
- payload 到达时若 QuestScreen 打开，调用 `refreshFromSync()` 刷新按钮状态。

## 自检
- javac 全量编译通过；`-Xverify:all` 加载 6 个关键类；
- 两 UUID 单元测试 `ISOLATION_OK`（u1 不泄漏 u2、claim 正确）；
- probe：`progress sync sent/received` 成对，complete/claim 后发送；J 书中文按钮/锁定提示正常；0 crash。

## 产物
- `g94/out/sky262-quests-1.6.0.jar`，SHA `ecb9b8025c9289b5ccfb797cb605da57a11179e294e47ec0a3e952d659dfe297`，base 98；staging `g94/stage-final2/mods-candidate`（98/98）；
- 前置 PASS 件 `680bd016`（无打开中刷新），本件为含 UI refresh 的定稿。
