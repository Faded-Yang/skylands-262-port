# 按住交互（hold interaction）真实鼠标输入失效 —— 26.3 mixin 选择器全部过期（task-29）

> 症状（用户实测，live R422/R423）：准星对着物理组装器没有任何 hold tip 文字，按住右键拖拽也不激活；
> 探针用合成 onUseItemOn 能激活（managerActive=true、进度到 1.0）⇒ 真实输入路径（mixin）死了。
> 结论：simulated 的 hold_interaction 四个 mixin 在 MC 26.3 下全部没注入（静默，因为
> injectors.defaultRequire=0），不是 manager 逻辑问题。修法 = 按 26.3 真实签名重编译 4 个 mixin 类。

## 1. 26.3 输入 API 实测（javap MC 26.3 jar）

| 旧（1.21.x / 26.2 源码里的选择器） | MC 26.3 实际 |
|---|---|
| MouseHandler.onPress(long,int,int,int) | onButton(long, MouseButtonInfo, int action) —— onPress 已删 |
| Minecraft.getOverlay()L.../screens/Overlay; | 已删；等价调用是 Gui.overlay()L.../screens/Overlay;（onButton/onScroll 都调它） |
| Minecraft.screen 字段（KeyboardHandler 注入点） | 字段已删；keyPress 里用 Gui.screen() |
| KeyboardHandler.keyPress(long,int,int,int,int) | keyPress(long, int action, KeyEvent) |
| ClientInput.shiftKeyDown 字段（LocalPlayer.tick WrapOperation） | 字段没了；输入在 ClientInput.keyPresses（net.minecraft.world.entity.player.Input record）；tick() 不再读 shift，crouch 读在 aiStep()（Input.shift()） |
| LocalPlayer.turn(DD)V（turnPlayer 注入） | 仍在（javap 实测 turnPlayer 内 invokevirtual LocalPlayer.turn(DD)V）✔ |
| Mth.clamp(FFF)F（GoggleOverlayRenderer.renderOverlay） | 仍在（create-fly 字节码 839 处）✔ |

另外 GoggleOverlayRendererMixin 的第一个 @Inject 处理器只声明了 CallbackInfo，而目标是
renderOverlay(Minecraft, GuiGraphicsExtractor, DeltaTracker) —— Mixin 要求处理器参数 = 目标参数 + CI，
所以这条也从未生效（它负责 steering wheel 激活时逐帧递减 hoverTicks）。

## 2. 修法（4 个类，javac 真编译，无手写字节码）

源码：work/run26/port/p4q/src/dev/simulated_team/simulated/mixin/hold_interaction/
（同一方案已同步到 work/aero-port/aeronautics-26/src/main/java/dev/simulated_team/simulated/mixin/hold_interaction/）

1. MouseHandlerMixin
   - turnPlayer：改为 @WrapOperation 包住 LocalPlayer.turn(DD)V 调用（旧 @Local(ordinal=0) int 在 26.3 已无此局部变量）；
   - onPress：改为 @Inject(method="onButton", at=INVOKE Gui.overlay() ordinal=0)，参数 (long, MouseButtonInfo, int action)，
     用 buttonInfo.button() / buttonInfo.modifiers() 调 onBeforeMouseInput(...)；
   - onScroll：注入点从 Minecraft.getOverlay 改为 Gui.overlay()；@Local(ordinal=3/4) 对应 26.3 的 scaledXOffset/scaledYOffset（LVT 已核对）。
2. KeyboardHandlerMixin：keyPress(long,int,KeyEvent)，注入点 Gui.screen() ordinal=0，用 event.key()/keycode()/modifiers()。
3. LocalPlayerMixin：@Inject isShiftKeyDown RETURN 不变；@WrapOperation 目标从 tick+FIELD 改为 aiStep + INVOKE Input.shift()Z。
4. GoggleOverlayRendererMixin：decrementRenderTicks 处理器补上目标参数 (Minecraft, GuiGraphicsExtractor, DeltaTracker, CallbackInfo)。
5. 所有可安全要求的关键注入改成 require = 1（onButton / onScroll / keyPress / renderOverlay），
   让下次签名变动在日志里显式报错而不是静默失效。

## 3. 静态验证闸（新增，构建脚本内强制）

g31/helper/src4/MixinTargetCheck.java：解析 mixin class 的 @Inject/@WrapOperation 的 method / @At target /
ordinal，到 MC 26.3 jar（GoggleOverlayRenderer 用 create-fly jar）里找目标方法并扫描指令，要求
「方法存在 + target 指令出现次数 > ordinal」。四个类全部 PASS 才允许出件（证据 p4q_targetcheck_*.txt）。
另加 -Xverify:all 类加载（LocalPlayerMixin 继承 AbstractClientPlayer，独立 init 会跑 MC 父类 clinit，
故该件记为 SKIP-init；javac 产物字节码有效性由编译器保证）。

## 4. 候选

| 项 | 值 |
|---|---|
| 候选 | work/run26/port/g31/out/aeronautics-fabric-0.1.0-port.26.3-holdinput.jar |
| size / SHA | 31,568,056 B / 27b9c8d72abf89b5c26e3265b910058e96c181497caf3ea7404a12ba0450f601 |
| 基线 | live aeronautics fb6a2a01…（31,568,543 B，entries=3,294；R423 之后重打，含 aero-fixer 的 batch1） |
| 变化 | 仅 4 个 entry：hold_interaction 的 MouseHandler/LocalPlayer/KeyboardHandler/GoggleOverlayRenderer mixin；其余 entry 逐字节相同 |
| 验证 | MixinTargetCheck 4/4 PASS；XVERIFY MouseHandler/KeyboardHandler/GoggleOverlayRenderer PASS，LocalPlayer SKIP-init；testzip 通过 |
| staging | work/run26/port/g31/stage/mods-p4q-holdinput（_stage_guard 硬闸；live 未被写） |

## 5. 待 A/B（真实输入只能用户/探针在真机上验）

1. 进世界 → 准星对准物理组装器：应出现「按住并拖拽以组装」hold tip（若仍无文字，见第 6 条：tip 渲染路径单独查）；
2. 按住右键拖拽：manager 应激活、进度条出现、组装完成；
3. 顺带：按住交互时不应下蹲（aiStep shift 包裹生效）；
4. 0 crash（若有 mixin 报错，日志会明确写 InjectionError 与选择器 —— 这是 require=1 的目的）。

## 6. 待查（若 press 修好后 tip 文字仍不出现）

hold tip 链路：HoldTipManager.tick()（postClientTick 内）→ CreateClient.VALUE_SETTINGS_HANDLER.showHoverTip(...)
→ create-fly 的 ValueSettingsHandler 渲染。若输入恢复正常但仍无文字，说明 tip 的渲染订阅在 26.3 也断了
（类似 R409 的 GUI 钩子问题），下一轮用同样的静态 + 探针反射方式查 ValueSettingsHandler 的 render 入口。


## 7. 诊断件：simulated$* 方法存在 ≠ 注入生效

probe 第一轮反馈「baseline 与候选的 MouseHandler/LocalPlayer 都能反射到 simulated$preOnPress 等」。
**这不是注入生效的证据**：Mixin 的执行顺序是「先把 mixin class 的 handler 方法合并进目标类，再按
@At 选择器给目标方法改线」；当选择器找不到（injectors.defaultRequire=0）时，handler 方法仍留在
目标类里变成**死代码**。所以两臂都能看到这些方法，恰好符合「旧注入已死、handler 只是被合并」。

本轮出两个诊断件（都基于 live aeronautics fb6a2a01，只改 4 个 mixin class，entry 数不变；
每个 handler 入口打 [sky262hold] 日志）：
- dbg-old：live 原选择器 + 日志 —— 31,568,413 B / 8bde78bc2f82b12cc0e8868bfdeabc056a9be30cf6f545cc3996c12b06b05fc8
- dbg-new：26.3 新选择器 + 日志 —— 31,568,623 B / 6d86f499f7956a14980edfed0f5be2e89075c0c32ea30568a7d00eaea6217d3b
staging：work/run26/port/g31/stage/mods-p4r-holdinput-dbg-{old,new}

判别依据（一次 run 即可）：
- dbg-old 中 MouseHandler press/scroll、KeyboardHandler、LocalPlayer.aiStep 的 handler 日志应为 0 条；
  LocalPlayer.isShiftKeyDown（RETURN 注入）与 GoggleOverlayRenderer 的 clamp WrapOperation 是真能注入的，
  会出日志 —— 用它们证明日志机制本身有效（阳性对照）。
- dbg-new 中上述 handler 在对应事件时应出现日志；若某条仍为 0，说明该选择器仍未对上，按该类再定点修。
旧最终候选（27b9c8d7）暂不 promote，等这轮日志对比后收敛。


## 8. dbg 结果 + dbg2（前置条件日志）：startHold 不在鼠标 mixin 里

probe 三臂对照（每臂 1 run）：
- dbg-old：simulated$preOnPress=0、preOnScroll=0 ⇒ 旧选择器确实是死代码（handler 被合并但注入点没接上）；
- dbg-new：preOnPress=4、preOnScroll=1、turnPlayer=593、shhhh=480 ⇒ 新选择器生效
  （注意：aiStep 的 handler 名是 simulated$shhhhDontTellTheServer，480 条说明 aiStep 也生效；probe 表里写的 aiStep=0 是名字看错）；
- 但三臂 V_HIT 已强制命中组装器、press 后 HoldInteractionManager.isActive=false、fraction=0；
  HoldTipBehaviour.getHoverTip 返回 simulated.gui.hold_tip.hold_to_assemble ⇒ tip 数据在。

**关键结构事实**：hold 的 startHold 不在鼠标 mixin 里。点击链是：
MouseHandler.onButton（我们的 mixin 只决定是否 cancel）→ vanilla 右键 → MultiPlayerGameMode.useItemOn
→ PhysicsAssemblerBlock.useWithoutItem（aeronautics 源码 line 90-95：clientSide && isLocalPlayer 时
调 SimClickInteractions.PHYSICS_ASSEMBLER_MANAGER.startHold(...)）→ BlockHoldInteraction.startHold →
HoldInteractionManager.start。
所以「press handler fired 但 manager 没启动」必然发生在上述链条的中间某一环。

**dbg2**（基于 live fb6a2a01，只加日志，9 个 entry 变化、entries 不变）：
- g31/out/aeronautics-fabric-0.1.0-port.26.3-holdinput-dbg2.jar
- 31,568,154 B / 7efb7767e150f3db808661998b45e578f7850562053cad0ac541f527bd07cd46
- staging：work/run26/port/g31/stage/mods-p4r2-holdinput-dbg2
- MixinTargetCheck 4/4 PASS
日志点：preOnPress 的 button/action/modifiers、screen、overlay、grabbed、player/spectator、hitType/pos/block、
onBeforeMouseInput 返回 cancelled、是否放行；SimulatedCommonClientEvents.onBeforeMouseInput 入口；
PhysicsAssemblerBlock.useWithoutItem 入口；BlockHoldInteraction.startHold/start/onUse；HoldInteractionManager.start/stop；
quiet_use.MultiPlayerGameModeMixin.quietUseIntercept 入口。

判读树：
- 放行（NOT cancelled）但 useWithoutItem 无日志 ⇒ vanilla onButton 未走到方块使用（mouse grabbed / screen / use key / startUseItem 条件）；
- useWithoutItem 有日志但 HoldInteractionManager.start 无 ⇒ onBlockEntityUse / BE 判定拒绝；
- quietUseIntercept 有日志 ⇒ QuietUse 短路；
- onBeforeMouseInput cancelled=true ⇒ 某 InteractCallback 取消（下一步打 per-entry 结果）。


## 9. dbg2 结果 + 关键结构认知 + dbg3

dbg2 实跑（phase V 合成 onButton，26 条 [sky262hold]）：
- press：button=1 action=1 screen=null overlay=null grabbed=true hit=BLOCK phys_assembler；onBeforeMouseInput
  cancelled=false；preOnPress NOT cancelled（放行）；
- 缺失：PhysicsAssemblerBlock.useWithoutItem / startHold / HoldInteractionManager.start / quietUseIntercept；
- release：hitType 已 MISS（mc.hitResult 被重算/丢失）。

**关键结构事实**：26.3 的 MouseHandler.onButton 只更新按键状态、分发 Screen 事件、处理 handleGlobalKeyPress，
**不调用 startUseItem/useItemOn**。真正的右键使用链是：
Minecraft.tick → handleKeybinds()（KeyMapping 驱动）→ startUseItem() → MultiPlayerGameMode.useItemOn(...)
→ PhysicsAssemblerBlock.useWithoutItem（clientSide&&isLocalPlayer 时 startHold）→ BlockHoldInteraction.startHold
→ HoldInteractionManager.start。
所以 probe 的合成 onButton 不可能走到 useWithoutItem —— 这是测试手段的局限，不是输入路径的证据。

**dbg3**（基于 live fb6a2a01，只加日志）：
| 项 | 值 |
|---|---|
| 候选 | work/run26/port/g31/out/aeronautics-fabric-0.1.0-port.26.3-holdinput-dbg3.jar |
| size / SHA | 31,572,965 B / e2f6f170936f3449f4ef71d59fb46a50793be6b068c549f362165bd701a0f232 |
| 变化 | 11 个 entry（4 hold mixin + SimulatedCommonClientEvents + PhysicsAssemblerBlock + BlockHoldInteraction + HoldInteractionManager + HoldTipManager + quiet_use mixin + simulated.mixins.json）+ **1 个新增 entry MinecraftDebugMixin**（entries 3294→3295） |
| 新 mixin | hold_interaction.MinecraftDebugMixin：@Inject Minecraft.handleKeybinds HEAD（screen/hit/keyUseDown/keyAttackDown/rightClickDelay/destroying/handsBusy）与 startUseItem HEAD（screen/hit） |
| 验证 | MixinTargetCheck 5/5 PASS；testzip 通过 |
| staging | work/run26/port/g31/stage/mods-p4r3-holdinput-dbg3 |

两个一次定位测试（probe 执行）：
A. 强制 hitResult=组装器，反射调用 Minecraft.startUseItem()（private）：应看到
   startUseItem ENTER → useWithoutItem ENTER → startHold ENTER → HoldInteractionManager.start ENTER。
   成功 ⇒ 链路 OK，问题在按键状态层（handleKeybinds/keyUse）；失败 ⇒ 看 startUseItem 日志的
   handsBusy/destroying/hitResult。
B. 反射 mc.options.keyUse.setDown(true) + 跑帧：看 handleKeybinds 日志 keyUseDown 与 startUseItem 是否触发。
C. HoldInteractionManager.stop 现在打印 caller（定位 ×17/run 的来源）。


## 10. dbg3 结论 + 26.3 真实鼠标路径的静态真相 + sublevel pick 假设

probe 用 dbg3 做 A/B：
- **A（直调 Minecraft.startUseItem()）**：isActive 立刻 true；日志 startUseItem=901 / useWithoutItem=1801 /
  startHold=901 / HoldInteractionManager.start=901 / quietUseIntercept=901 ⇒ **useWithoutItem→startHold→manager.start
  整条使用链是好的**；
- B（setDown）无效：26.3 每 tick 用 InputConstants.isKeyDown(int)（SDLKeyboard 状态）重算 KeyMapping，
  单次 setDown 会被覆盖 —— 测试方法问题，不是 bug；
- C：HoldInteractionManager.stop 的 caller = ClientTickEvents.lambda$static$3（aeronautics 自己在 client tick
  每帧 stop 未激活交互），正常。

**关键静态事实（javap MouseHandler.onButton 尾部 offset 529-555）**：
  InputConstants.Key k = InputConstants.Type.MOUSE.getOrCreate(button);
  KeyMapping.set(k, pressed);
  if (pressed) KeyMapping.click(k);
⇒ 真实鼠标右键会喂 KeyMapping（keyUse down + click）→ Minecraft.handleKeybinds 的 consumeClick →
startUseItem → useItemOn → PhysicsAssemblerBlock.useWithoutItem → startHold。**真实输入路径在 26.3 没有坏**。
（注意：KeyMapping.isDown 的轮询路径 InputConstants.isKeyDown(int) 只读 SDLKeyboard；鼠标键状态只来自
onButton 的 KeyMapping.set，这解释 setDown 测试为何被覆盖。）

因此用户「右键没反应 + 无 Jade 名称 + 无 hold tip」最可能不是 hold 输入问题，而是：
- **准星 pick 打不到方块**（若组装器位于 sable sublevel 内：R415 只补了 ≤64 块渲染，raycast/collision 映射可能仍缺）
  ⇒ hitResult=MISS ⇒ 无 Jade/无 tip/无 use；而探针的合成 onUseItemOn 绕过 pick 所以能激活；
- 或 **tip/进度条渲染订阅缺失**（renderOverlays 的调用者目前只有 SimulatedCommonClientEvents 自己，
  HoldTipManager → CreateClient.VALUE_SETTINGS_HANDLER.showHoverTip 的画线在 26.3 是否被调用待证）。

下一轮决定性测试（probe，用 dbg3 件）：
1. 普通世界 vs sable sublevel 各放一个组装器，不做任何强制，读 Minecraft.hitResult / mc.pick(1.0) 的 type/pos；
2. 用忠实模拟（复刻 onButton 尾部）：KeyMapping.set(MOUSE.getOrCreate(1), true) + KeyMapping.click(...)，
   等 1-2 tick 看 isActive 与 dbg3 的 handleKeybinds/startUseItem/useWithoutItem 日志；
3. 回传 HoldTipManager.tick / renderOverlays 日志，判断 tip 渲染链。
判读：普通世界激活成功 + sublevel MISS ⇒ 根因是 sublevel 选块（task-28 族），本族（hold 输入）无需再改；
普通世界也不激活 ⇒ 看 handleKeybinds 的 keyUseDown/startUseItem 日志继续。
