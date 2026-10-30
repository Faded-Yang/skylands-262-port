# hold tip 不显示（task-34）：CreateClient 垫片的 showHoverTip 是空实现

> 用户症状：准星对着物理组装器没有任何文字提示，按住右键也没有 hold tip；
> 探针实测 hold 逻辑与激活都正常（useItemOn 前后 isActive false 到 true、fraction 增长），
> 唯一缺失的就是 UI 文字，与 shim 没有转发的静态结论一致。

## 1. 根因（javap 静态确凿）

- aeronautics jar 里的 dev.simulated_team.simulated.util.hold_interaction.HoldTipManager.tick() 每 client tick
  调 com.zurrtum.create.CreateClient.VALUE_SETTINGS_HANDLER.showHoverTip(list)；
- 但 aeronautics jar 自带的 com/zurrtum/create/CreateClient$ValueSettingsHandler.class 是 Fabric spike 垫片，
  其 showHoverTip(List of Component) 字节码函数体只有 return（javap 实测），数据永远丢弃；
- Create Fly 的真实链路是 com/zurrtum/create/client/Create.VALUE_SETTINGS_HANDLER
  （类型 com.zurrtum.create.client.foundation.blockEntity.ValueSettingsClient），
  由 create-fly 的 client/mixin/HudMixin 每帧调 ValueSettingsClient.render(Minecraft, GuiGraphicsExtractor) 绘制；
  真实方法签名：showHoverTip(Minecraft, List of MutableComponent)。
- 另外 ValueSettingsClient.render 有前置 ValueSettingsInputHandler.canInteract(player)
  （非旁观、非潜行、mayBuild），正常悬停满足。
- 同类垫片 ZapperRenderHandler.shoot(InteractionHand, Vec3) 也是空实现（目前无 UI 影响，未动）。

## 2. 修法（aeronautics，只改 2 个 entry）

CreateClient.showHoverTip 转发到 create 真实 handler：
    try {
        com.zurrtum.create.client.Create.VALUE_SETTINGS_HANDLER.showHoverTip(
                Minecraft.getInstance(), (List<MutableComponent>) (List<?>) tip);
    } catch (final Throwable ignored) {
        // UI hint must never break the client tick
    }
源码：work/run26/port/g51/src/com/zurrtum/create/CreateClient.java
构建：work/run26/port/g31/_build_tipfix.py

## 3. 候选与验证

| 项 | 值 |
|---|---|
| 候选 | work/run26/port/g51/out/aeronautics-fabric-0.1.0-port.26.3-tipfix.jar |
| size / SHA | 31,568,641 B / 21132cc5e24707c981aebc7120fff0b4fdbc9558db6a058b2e0e40f4ab788105 |
| 基线 | live aeronautics FB6A2A01...（31,568,543 B） |
| 变化 | 只改 com/zurrtum/create/CreateClient.class 与 CreateClient$ValueSettingsHandler.class；entries 3294 不变、testzip 通过 |
| 验证 | -Xverify:all 两个 class 均 PASS |
| staging | work/run26/port/g51/stage/mods-aero-tipfix（_stage_guard 硬闸；live 未写） |

## 4. A/B（probe，2 run，1280x720，全新存档，0 crash）

| 臂 | 按住右键 10 tick 同机位截图 |
|---|---|
| 基线 FB6A2A01 | g33/evidence/tip-base-s2.png：只有组装器 + 红色建筑高度上限提示，无 hold 提示文字 |
| 候选 21132cc5 | g33/evidence/tip-cand-s2.png：同机位出现「按住并拖拽以组装」（屏幕中下方白色文字）|

两臂 isActive=true、fraction 0.053/0.162/0.388 增长、release 到 1.000，交互链一致；差异只在 UI 文字。
我本人复核过 tip-cand-s2.png（1280x720），确认「按住并拖拽以组装」可见。

## 5. 结论与剩余

- 候选 21132cc5 可 promote（Lead 执行；建议备份 aeronautics 为 .bak-r426，promote 用临时文件 + os.replace，
  promote 后复跑标题 + 进世界 + 组装器 hold）。
- 剩余小项（不阻塞）：
  1) 进度条（HoldInteractionManager.renderOverlay）位置不明显，probe 可裁剪截图确认是否被文字遮挡；
  2) hover（未按键）截图相机未落稳，可补拍一张确认 hover tip 也显示；
  3) task-32（sublevel pick）已按 baseline A/B 撤销，不 promote，详见 docs/fix-sublevel-pick.md。
## 6. R426 promote 后剩余两个小项（2026-10-19）

R426（21132CC5）已 promote，按住时提示文字 OK。probe 补充验证发现：

### 6.1 进度条（HoldInteractionManager.renderOverlay / PhysicsAssemblerGUIHandler.renderOverlay）未出现
- 裁剪图 tip-cand-hold-crop.png（fraction 0.053）与 tip-cand-hold50-crop.png（fraction 0.902）里只有文字，
  屏幕中下/文字下方没有进度条（与 fraction 大小无关）。
- 可疑点：
  1) 我们的 HUD 挂点是否真的每帧调用 renderOverlays —— 文字来自 Create HudMixin，即使我们的 HudElement 没跑，
     文字也会出现；所以「有文字」不能证明 renderOverlays 被调用；
  2) 若 renderOverlays 被调用但 HoldInteractionManager.renderOverlay 抛异常，fabric HUD 会吞掉并记日志；
  3) 26.3 的 GuiGraphicsExtractor.blit/pose API 语义变化（SimGUITextures 的 location 可能是图集标识而非 GUI 纹理）。
- 下一步：先 grep latest.log 里 HudElement/渲染异常；再出 dbg 件在 renderOverlays / HoldInteractionManager.renderOverlay /
  PhysicsAssemblerGUIHandler.renderOverlay 入口打日志（active、width/height、异常捕获）。

### 6.2 hover（不按键）提示未出现
- probe 已修正相机时序（aim 后等 8 tick），准星正对组装器，但无文字；
- 可疑点：ValueSettingsClient.render 有 hoverWarmup/hoverTicks 前置（需要持续 aim 若干 tick），8 tick 可能不足；
  也可能 HoldTipBehaviour.getHoverTip 在 hover 时返回 null（只有按住路径有数据）。
- 下一步：probe 持续 aim 20-30 tick 再截图；同时我用探针反射读 HoldTipBehaviour.getHoverTip 的返回值确认数据是否存在。

结论：R426 本身正确（用户投诉的「没文字」已解决）；以上两项是 UI 完整度问题，不阻塞当前 promote。
## 7. tipfix2 dbg（定位进度条与 hover tip 两条链）

候选：work/run26/port/g51/out/aeronautics-fabric-0.1.0-port.26.3-tipfix2-dbg.jar
- 31,568,483 B / sha256 7f9847e16cc139f6951961a49181f715bafcb444bddcf77ec66747732fdf63a0
- 基线 live aeronautics 21132CC5（R426 已 promote）；只改 3 个 entry（entries 3294 不变，testzip 通过）：
  CreateClient$ValueSettingsHandler（日志：shim showHoverTip list/first）、
  SimulatedCommonClientEvents（日志：renderOverlays ENTER active）、
  HoldInteractionManager（日志：renderOverlay ENTER active）；logger=sky262ui
- -Xverify:all 三 class PASS；staging：work/run26/port/g51/stage/mods-aero-tipfix2-dbg

javap 已确认的 create 端口径：
- ValueSettingsClient.showHoverTip：hoverWarmup<6 时每次 +2 并 return（前 3 次丢弃），之后才设 hoverTicks/lastHoverTip；
- ValueSettingsClient.render：要求 canInteract(player)（非旁观/非潜行/mayBuild）+ hoverTicks!=0 + lastHoverTip!=null，
  位置在屏幕水平居中、(guiHeight-75-len*12) 处。

判读树（probe 1 run 后）：
- shim 行有但没有文字 => create 端 warmup/render 门槛（hover）或绘制 API（进度条）；
- shim 行没有 => HoldTipManager 没喂数据（hover 分支没走到）；
- renderOverlays 行没有 => 我们的 HUD 挂点未生效（进度条永不画）；
- renderOverlays 有、HoldInteractionManager.renderOverlay ENTER active=true 但没有条 => PhysicsAssemblerGUIHandler.renderOverlay 绘制本身问题。
## 8. 进度条（tipfix3）：26.3 的裸 blit 画不出来，改 fill() 版

javap（live 21132CC5）确认：HoldInteractionManager.renderOverlay 不是空壳（转发到 active.renderOverlay），
PhysicsAssemblerGUIHandler.renderOverlay 也有真实绘制（graphics.pose() + translate + blit(Identifier,...)，
纹理为 SimGUITextures.ASSEMBLER_TRACK_{START,MIDDLE,END}，同一张 textures/gui/assembler.png 的 UV 区域）。
但 26.3 GUI 纹理已迁到 sprite/atlas 管线：裸 textures 路径的 GuiGraphicsExtractor.blit(Identifier,...) 调用存在、
运行时不产生像素，于是出现「renderOverlay 每帧被调（active=true 245 次）但画面无条」。

候选（只改 1 个 class：PhysicsAssemblerGUIHandler）：
- work/run26/port/g51/out/aeronautics-fabric-0.1.0-port.26.3-tipfix3.jar
- 31,568,066 B / sha256 df934ad6bc7962eeeb4ee4f10afed6e8fcbb4a4eea435a016d1b945a65a3cbc6
- 基线 live aeronautics 21132CC5（R426）；entries 3294 不变、changed 恰好 1 个 class、testzip 通过；-Xverify:all PASS
- staging：work/run26/port/g51/stage/mods-aero-tipfix3（硬闸；live 未写）

新绘制：准星右侧竖条 14x72，深色底 + 1px 边框 + 绿色填充（高度 = fraction*68），无纹理依赖；
位置沿用原版（guiWidth/2+10, guiHeight/2-36）。

A/B：按住 fraction≈0.2 与 ≈0.8 各截一张并裁剪准星右侧，确认竖条高度随进度变化；文字不回归；0 crash。
后续可选：把 assembler.png 注册成 GuiSprite 并用 blitSprite 恢复原版轨道美术（独立小任务）。
## 9. tipfix3 A/B PASS（进度条恢复）

probe 1 run（1280x720，全新存档，0 crash）：
- tip3-hold10-bar.png（fraction 约 0.16）：深色竖直轨道 + 底部一小段绿色填充（约 1/6 高）；
- tip3-hold50-bar.png（fraction 约 0.902）：绿色填充几乎充满整条（约 9/10 高）；
- 两张里「按住并拖拽以组装」文字都在（无回归）；位置在准星右侧、竖直，无遮挡。

=> tipfix3 可 promote（Lead 执行：备份 aeronautics 为 .bak-r427，临时文件 + os.replace，promote 后复跑标题+进世界+组装器 hold）。
当前 fill 版是功能降级（原版轨道美术未恢复），进度反馈已可见；可选后续：assembler.png 注册 GuiSprite + blitSprite 恢复美术。
