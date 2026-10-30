# 按住交互「重复触发 / 进度清零 / 手部动画反复」与真实鼠标输入（task-37/38）

## 1. 症状与复现

用户：按住组装器时手部反复播放交互动画、进度条以恒定频率被清空、手快拉满也等不到生效；
目标：所有长按交互部件都对（以油门杆为基准，油门杆本来正常）。

probe 复现方法：每 3 tick 重复调用 MultiPlayerGameMode.useItemOn（模拟 26.3 按住时 rightClickDelay 的重复 use），共 60 tick，每 5 tick 读 fraction：
- live C78D059D：fraction 在 0.004–0.012 间周期重置，永远拉不满；
- holdfix3 cc3fc28e：fraction 0.012 -> 0.971 单调上升，无回退；release 后 active=false。

## 2. 根因

26.3 按住右键时 startUseItem 会按 rightClickDelay 周期性重复调用；port 里 PhysicsAssemblerBlock.useWithoutItem
每次都用 startHold + InteractionResult.SUCCESS，而 ThrottleLeverBlock.useWithoutItem 的写法是：

    if (!MANAGER.isActive()) { MANAGER.startHold(...); return InteractionResult.SUCCESS; }
    return InteractionResult.FAIL;

重复 startHold -> HoldInteractionManager.start 里 active.stop(); active.start() 会重置交互进度；
重复 SUCCESS 还会让 26.3 反复播放手部 swing。

## 3. 修法（holdfix3，aeronautics，base live C78D059D）

1) PhysicsAssemblerBlock.useWithoutItem：manager 已 active 时直接返回 FAIL（不 startHold/不 SUCCESS），否则 startHold+SUCCESS；
2) HoldInteractionManager.start：active == 传入实例 -> 直接 return（不 stop/start 重置）；
3) BlockHoldInteraction.startHold：isActive() 且同 blockPos -> 直接 return。

候选：work/run26/port/g51/out/aeronautics-fabric-0.1.0-port.26.3-holdfix3.jar
- 31,566,676 B / sha256 cc3fc28efc58b1c2f3b70a3c4a9e4e15cf85fdaad947024ee81f6ad4f52f3b42
- 只改 3 个 entry；entries 3294 不变、testzip 通过；-Xverify:all 两 class PASS，
  PhysicsAssemblerBlock 因 Block 子类 clinit 与夹具旧 Guava 冲突改为 SKIP-init（非代码问题）
- staging：work/run26/port/g51/stage/mods-aero-holdfix3（硬闸；live 未写）

注：最终件里没有 sky262hold 日志（holdfix2 才带日志，holdfix3 为交付干净去掉了日志）；
probe 看到 jar 内 0 个 class 含 sky262hold 属预期，行为证据（fraction 单调）已足够。

## 4. A/B 结果（probe）

| tick | live C78D059D | 候选 cc3fc28e |
|---|---|---|
| 10 | 0.008 | 0.039 |
| 20 | 0.012 | 0.134 |
| 30 | 0.004 | 0.329 |
| 40 | 0.008 | 0.673 |
| 50 | 0.012 | 0.877 |
| 60 | 0.004 | 0.971 |
| release | active=false | active=false |

结论：核心症状（进度周期性清零/拉不满）已消除，release 正常；手部动画判据（player.swinging/getAttackAnim 在 26.3 反射不可读）
需实机或人工对比截图（g33/evidence/R-*-shot-*）。

## 5. 真实鼠标输入（R428，holdinput C78D059D）

另一个同族 bug：live 的 4 个 hold_interaction mixin 仍是 1.21 选择器，26.3 全部静默失效：
onPress(->onButton)、Minecraft.getOverlay(->Gui.overlay)、Minecraft.screen 字段(->Gui.screen)、
tick+ClientInput.shiftKeyDown(->aiStep+Input.shift())、turnPlayer 的 @Local(ordinal=0) int（26.3 无此局部变量）。
后果：松开不触发 onUse(RELEASE)（条只在远离时消失）、鼠标移动不触发 onMouseMove（拖动不改进度）；
单击能启动是因为 vanilla useWithoutItem 直接 startHold。
R428 已 promote 该修复（4 个 mixin 换 26.3 选择器），用户实机验 release/drag。
