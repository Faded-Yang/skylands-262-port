# 机械族修复报告：`Level.random` 访问控制（protected）清零

> 日期：2026-10-17 ｜ 工程：`work\aero-port\aeronautics-26\src`
> 日志：`notes\aero26-compile-1.log` ｜ 错误原文：`random 在 Level 中是 protected 访问控制`

## 1. 根因与 26.3 API 事实（javap 实测）

| 类 | 26.3 实测 |
|---|---|
| `net.minecraft.world.level.Level` | `protected final RandomSource random;`（1.21.x 为 public）+ **`public RandomSource getRandom();`** ✅ |
| `net.minecraft.server.level.ServerLevel` | **未**把 `random` 重新暴露为 public（只继承 protected） |
| `net.minecraft.client.multiplayer.ClientLevel` | 同上，**未**重新暴露 |
| `net.minecraft.world.entity.Entity` | `random` 同为 `protected final`（子类内 `this.random` 合法） |

⇒ 唯一修法：**`level.random` → `level.getRandom()`**。子类暴露路线（优先级 2）经 javap 排除。

## 2. 处理结果

| 项 | 数 |
|---|---|
| 日志报错条目 | 100（javac 正文 + 末尾汇总两段重复输出，实际 **46 个唯一 (文件,行) 站点**） |
| 涉及文件 | **28** |
| **已改文件** | **27**（改前均备份 `<文件>.bak-random`） |
| **已修复站点** | **45 / 46** |
| 跳过 | 1 文件 / 1 站点（见 §3） |
| 校验 | `verify_level_random.py` 逐站点复读：45/46 行内已无 `.random` 残留 ✅ |
| 编译 | 按要求**未编译** |

修法全部为首选项：`<expr>.random` → `<expr>.getRandom()`，逐行按日志行号定位，不做全项目盲替。
同一行多个 `.random`（如 `AbsorberBlockEntity.java:122` 一行 2 处）一并替换。
脚本：`work\fix_level_random.py`（替换）/ `work\verify_level_random.py`（校验）。

## 3. 跳过 1 处（Veil 冲突回避，需后续补）

- `src\main\java\dev\simulated_team\simulated\content\physics_staff\PhysicsStaffClientHandler.java:526`
  含 `import foundry.veil.api.network.VeilPacketManager;`（第 19 行）——按纪律跳过，避免与 Veil 子代理写冲突。
  待改内容（机械、可直接套用）：
  ```java
  // 现: final RandomSource random = Minecraft.getInstance().level.random;
  // 改: final RandomSource random = Minecraft.getInstance().level.getRandom();
  ```
  ⚠ **改完前该文件仍报 1 个本族错误**，Veil 族收工后请补这一行。

## 4. 残留检查（全工程 `\.random\b`）

排除 `.bak-random` 备份后，活体源码中剩余 `.random` 全部合法或不在编译集内：

| 残留 | 结论 |
|---|---|
| `GustEntity.java` 102–125 共 10 处 `this.random` | `GustEntity extends Entity`，protected 成员在**子类内部经 `this` 访问合法**；日志未报 ✅ |
| `HotAirEmberParticle.java`、`LaunchedPlungerEntity.java:73` 的 `Math.random()` | JDK 静态方法，无关 ✅ |
| `GustParticle.java:128`、`AirPoofParticle.java:13`、`MagnetFieldParticle2.java:24`（`worldIn/level.random`，接收者均为 `ClientLevel`） | 这三个文件在 `build.gradle` 第 111/112/116 行被 **`exclude`**，不在编译集内，日志未报；**若日后解除排除需同步改成 `getRandom()`** |
| `PhysicsStaffClientHandler.java:526` | 见 §3，唯一**待补**点 |

落在 Level 类型变量上且参与编译的 `.random` 残留 = **1 处**（即 §3 的 Veil 跳过文件）。

## 5. 已改 27 文件清单（46 站点中已修的 45 处）

**main（17 文件 / 24 站点）**
`api\levitite_blend_crystallization\CrystalPropagationContext.java`(69,74)、`LevititeBlendHelper.java`(67)、
`content\blocks\hot_air\envelope\EnvelopeBlock.java`(143)、`EnvelopeEncasedShaftBlock.java`(54)、
`content\blocks\hot_air\gust\GustEntity.java`(93)、
`content\blocks\propeller\behaviour\PropellerActorBehaviour.java`(352)、
`content\particle\LevititeSparkleParticle.java`(17,21,43)、`PropellerAirParticle.java`(25)、
`content\ponder\instructions\PropellerParticleSpawningInstruction.java`(72,99,100)、
`mixin\levitite\ItemEntityMixin.java`(44)、
`simulated\content\blocks\absorber\AbsorberBlock.java`(78,79)、`nav_table\NavTableBlock.java`(118)、
`portable_engine\PortableEngineBlock.java`(112)、`symmetric_sail\SymmetricSailBlock.java`(134)、
`simulated\content\entities\launched_plunger\LaunchedPlungerEntity.java`(361)、
`simulated\content\items\rope\RopeItem\ClientRopeItemHandler.java`(116)、
`simulated\content\particle\MagnetFieldParticle.java`(17)、
`simulated\ponder\instructions\AirflowAABBInstruction.java`(43)

**excluded-wip（10 文件 / 21 站点，该目录经 `srcDir` 参与编译）**
`HotAirBurnerBlockEntity.java`(109×2,112×2)、`SteamVentBlockEntity.java`(211,214)、
`MountedPotatoCannonBlockEntity.java`(183,195,208)、`GimbalSensorBlockEntity.java`(132,134,153,561,569)、
`SwivelBearingBlockEntity.java`(270)、`AbsorberBlockEntity.java`(122×2)、
`PortableEngineBlockEntity.java`(266×2)、`RedstoneMagnetBlockEntity.java`(118,119,130,155)、
`RopeWinchBlockEntity.java`(109,110)

## 6. 回滚

每个已改文件旁有 `.bak-random` 备份；回滚 = 删除活体文件、去掉备份后缀。
