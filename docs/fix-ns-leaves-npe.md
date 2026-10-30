# fix-ns-leaves-npe —— natures_spirit 自定义树叶客户端 NPE（26.3 LeavesBlock 构造签名）

> 日期：2026-10-21 ｜ 目标：MC **26.3** + Fabric Loader 0.19.5 + Java 25
> 结论：**已修，出 staging 候选，待 probe 实机验收**。只改 3 个 class，其余 7984 个 entry 逐字节不变。
> 参考：`docs/port-delight.md` §2.5（26.3 `LeavesBlock` 构造器多一个 `AmbientLeavesBlockSoundPlayer` 的旧记录）、`docs/port-natures-spirit.md`（g70 源码/构建基线）、`docs/KNOWN-LIMITATIONS.md` §natures_spirit（树形降级清单）。

---

## 1. 崩溃（已确诊，26.3 客户端 tick）

- 证据：`work/run26/port/g33/game-matrix/crash-reports/crash-2026-10-21_02.41.31-client.txt`

```
java.lang.NullPointerException: Cannot invoke "net.minecraft.world.level.block.sounds.AmbientLeavesBlockSoundPlayer.playAmbientLeavesSounds(...)"
  because "this.ambientLeavesBlockSoundPlayer" is null
    at knot//net.minecraft.world.level.block.LeavesBlock.animateTick(LeavesBlock.java:145)
    at knot//net.minecraft.client.multiplayer.ClientLevel.doAnimateTick(ClientLevel.java:600)
    at knot//net.minecraft.client.multiplayer.ClientLevel.animateTick(ClientLevel.java:576)
    at knot//net.minecraft.client.Minecraft.tick(Minecraft.java:1963)
```

- 触发：玩家在 ns 树叶附近（崩溃报告里 LocalPlayer pos=(4004.5, 201.0, 4087.5)，客户端 tick 已跑 3395 ticks）。

## 2. 26.3 源码事实（work/refs/mc26.3）

| 点 | 事实 |
|---|---|
| `LeavesBlock` 构造器 | `LeavesBlock(AmbientLeavesBlockSoundPlayer, BlockBehaviour.Properties)`（LeavesBlock.java:34-40，字段 ```protected final```） |
| `animateTick` | L147-152 直接 `this.ambientLeavesBlockSoundPlayer.playAmbientLeavesSounds(level,pos,this,random)` —— **不判空** ⇒ 谁传 null 谁炸 |
| 原版「无环境音树叶」写法 | `AmbientLeavesBlockSoundPlayer.noAmbientSound()`（AmbientLeavesBlockSoundPlayer.java:49-51，返回 `NO_SOUND` = `(Optional.empty(), chance=0, Optional.empty(), 0, 0)`）；`playAmbientLeavesSounds` 首先判 `ambientSound.isPresent()` ⇒ 直接返回，不会 NPE |

## 3. 修复（3 个类，ns 源码）

文件（`work/run26/port/g70/src/natures_spirit/net/hibiscus/naturespirit/blocks/`）：

| 类 | 改前 | 改后 |
|---|---|---|
| `VinesLeavesBlock` | `super((AmbientLeavesBlockSoundPlayer)null, properties);` | `super(AmbientLeavesBlockSoundPlayer.noAmbientSound(), properties);` |
| `ParticleLeavesBlock` | `super((AmbientLeavesBlockSoundPlayer)null, settings);` | `super(AmbientLeavesBlockSoundPlayer.noAmbientSound(), settings);` |
| `ProjectileLeavesBlock` | `super((AmbientLeavesBlockSoundPlayer)null, settings);` | `super(AmbientLeavesBlockSoundPlayer.noAmbientSound(), settings);` |

- 全树 grep：`extends LeavesBlock` **只有这 3 个**；且它们之间/之外**没有别的子类**（`extends ParticleLeavesBlock` / `VinesLeavesBlock` / `ProjectileLeavesBlock` = 0 处）。
- `WoodSet` 里 `new TintedParticleLeavesBlock(0.01F, properties)` 用的是 **26.3 原版** `net.minecraft.world.level.block.TintedParticleLeavesBlock`（原版自己会传合法 sound player），不需要改。

## 4. 构建与重打包（base = live nsB2）

```
python work\run26\port\g70\_build.py natures_spirit        # javac rc 0 errors 0
python work\run26\port\g70\_ns_leaves_pack.py              # 以 live nsB2 为 base，只替换 3 个 class
```

| 项 | 值 |
|---|---|
| base（live） | `work/run26/mods-stable/natures_spirit-fabric-2.3.0-26.3-nsB2.jar`，18,802,673 B，SHA-256 **`53a01a18f341f286543a20cdcad1d4364c28e424d47ab21897bb3741f7b7b1db`** |
| 候选 | `work/run26/port/g70/out/natures_spirit-fabric-2.3.0-26.3-nsB2-leaves.jar`，18,802,737 B，SHA-256 **`abd15661cb383e77fd34c8f384952cc6cf1248fdf5768e6b62fda75ac00aa602`** |
| entries | in 7987 / out 7987，**顺序一致**，`testzip=None` |
| changed | **只有 3 个**：`VinesLeavesBlock.class` / `ParticleLeavesBlock.class` / `ProjectileLeavesBlock.class`（脚本对 base 逐 entry SHA-256 比对后断言 `changed==targets`） |
| staging | `work/run26/port/g70/stage/ns-leaves/`，**115 jar** = live 114 + 候选（**候选以交付名 nsB2 放入，旧 nsB2 被排除**，避免同名 mod 双份） |

> 3 个 class 大小变化：Vines 5624→5725 B、Particle 2292→2393 B、Projectile 3553→3654 B（都 +101 B，即 `aconst_null/checkcast` 换成 `invokestatic noAmbientSound` 的差）。

## 5. 静态扫描：live 115 个 mod 的同类风险（结论：仅 NS，已全修）

工具 `work/run26/port/g70/_scan_leaves_mods.py`（只读）：对 live 每个 jar 的每个 class 先按字节找 `net/minecraft/world/level/block/LeavesBlock` / `AmbientLeavesBlockSoundPlayer`，再**解析 class 文件常量池拿真实 superclass**（direct），并传递闭包找 indirect；最后 `javap -p -c` 看构造器是 `aconst_null` 还是 `noAmbientSound()`。

结果（`g70/leaves-scan.json`）：

| 类 | jar | 类型 | 构造器判定 |
|---|---|---|---|
| `net.hibiscus.naturespirit.blocks.VinesLeavesBlock` | natures_spirit-…-nsB2.jar | direct | **NULL** |
| `net.hibiscus.naturespirit.blocks.ParticleLeavesBlock` | natures_spirit-…-nsB2.jar | direct | **NULL** |
| `net.hibiscus.naturespirit.blocks.ProjectileLeavesBlock` | natures_spirit-…-nsB2.jar | direct | **NULL** |

- 全 115 jar 合计 **3 个子类，全部在 natures_spirit，全部 NULL**；**其它 mod 0 个**自定义 `LeavesBlock` 子类 ⇒ 「同类问题」范围收敛在这 3 个，本候选已把它们全部改成 `noAmbientSound()`。
- 扫描覆盖的 115 = 当前 live 交付集（含 nsB2 本体）；后续新增 mod 可重跑该脚本。

## 6. 验收（probe 实机，未开始；我不启动游戏）

- staging：`work/run26/port/g70/stage/ns-leaves`（115 jar）。
- 判据：进世界后在 ns 树叶附近**停 30 s**（客户端 tick 必走 `animateTick`），并**放置/破坏** `*_leaves` 若干次（含 `particle_*` / `vines_*` / `wisteria` 等 3 类方块）：
  1. **0 crash**（无 crash-report）；
  2. 日志无 `LeavesBlock.animateTick` NPE（grep `LeavesBlock.animateTick` / `playAmbientLeavesSounds` = 0）；
  3. 可选：确认这些树叶仍正常渲染、掉叶子粒子正常（`ParticleLeavesBlock` 的 `spawnFallingLeavesParticle` 不受本次改动影响）。
- 预期副作用：这些自定义树叶**没有环境音**（与原版无环境音树叶一致）—— 这是正确行为，不是回归；普通 `oak_leaves` 等原版树叶仍由原版 sound player 驱动。

## 7. 限制 / 未覆盖

1. 本修复只消除 `animateTick` 的 NPE；`LeavesBlock` 的其它行为（distance/persistent 状态、粒子）不变。
2. 未改数据、未动 lang；nsB2 基线的其它已知降级见 `docs/KNOWN-LIMITATIONS.md` §natures_spirit。
3. 候选未 promote；promote 前需 Lead 断言 `sha(live) == base SHA`（`53a01a18…`）。
4. 静态扫描是「构造器传 null」风险的口径，不是运行时全量证明；实机验收仍以 probe 为准。
