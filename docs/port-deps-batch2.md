# port-deps-batch2 —— dragonlib（失败）+ CEI/DragonsPlus（第一断点）

> 日期：2026-10-19 ｜ 专线：crashfix-26 ｜ base = live **74 jar**（aeronautics `1BED71C9…`、sable `1088C4FE…`、create-fly `0E9B26D3…`，完整 SHA 列表 `g66/out/evidence/base-live-74.json`）。
> 结论：**dragonlib 失败（整包 intermediary）**；**CEI+DragonsPlus 未通过（create-fly 流体 API 漂移，第一断点已修但需要 API 适配）**。两者均未 promote。

---

## 0. 状态表（lead 格式）

| mod | 源版本 | 依赖 | jar SHA-256 | staging | 结果 | 遗留 |
|---|---|---|---|---|---|---|
| dragonlib | 3.0.29+mc1.21.1-fabric | architectury>=13、fabric-api | `0862eef23c587867b8b621cc00ca3fb14ab26f34d1b358410c8222ac3a155afa`（1,357,664 B） | `g66/stage/batch2`（未 promote） | ❌ **失败**：`NoClassDefFoundError: net/minecraft/class_3302` @ `DragonLibFabric.onInitialize` | 整包 intermediary→official 重映射（3,271 处引用、614 类）；成本高，广度优先跳过，详见 `docs/port-dragonlib.md` |
| create_enchantment_industry | 2.5.2-c（Fabric 26.1.2） | create>=6.0.9-1、fabric-api | `2dd6a51d9c57673e2d6bd529092173601dfa42894a8381df8c6199648c8f96f0`（872,709 B，flowfix） | `g66/stage/batch3`（未 promote） | 🔶 **部分**：首个 `NoClassDefFoundError: FlowableFluid$Still` 已修（CP Utf8 → `FluidEntry$Still/Flowing`，2 处/包）；下一断点 `IllegalAccessError: FluidEntry$Still` | 需按 create-fly **现行 fluid builder API** 重写 `CEIFluids`/`CDPFluids.registerPair`（`FluidEntry$Still/Flowing` 包私有 + 私有构造器，不能用字节码补访问） |
| create_dragons_plus | 1.11.4-p1（Fabric 26.1.2，CEI 前置） | create>=6.0.9-1、fabric-api | `df6eaf8cbdb8987f6bcd97aac70afc281ba488e49d61bcfd5d0fc3f368d18854`（543,926 B，flowfix） | 同上 | 🔶 同上（同一断点） | 同上 |

---

## 1. 关键规则（本轮最重要的发现，已进台账）

**26.3 运行期是 official（named）命名空间；只有 26.x 的 Fabric 构建是 named，1.21.x 的 Fabric 构建是 intermediary（class_xxx）。**

| jar | intermediary 引用 | named 引用 |
|---|---|---|
| dragonlib 3.0.29（1.21.1 Fabric） | **3,271** | 2 |
| YungsApi 26.1.2-Fabric | 0 | 606 |
| Paxi 26.1.2-Fabric | 0 | 26 |
| CEI 26.1.2 Fabric | 0 | 1,214 |
| DragonsPlus 26.1.2 Fabric | 0 | 647 |

⇒ 选件时先做这个 census：**intermediary 引用 > 0 的 1.21.x 构建不要直接试**（启动必 `class_xxx` 找不到）；priority 只给 26.x Fabric 构建。

---

## 2. dragonlib 失败时间线（证据 `g66/out/evidence/dragonlib-crash-report.txt`）

1. 剥 JIJ（architectury 13.0.6 / forgeconfigapiport 21.1.1 / mixinextras 0.5.3）→ `86f854fa…`；
2. `accessWidener v2 intermediary` ⇒ loader 直接拒绝（`ClassTweakerFormatException`）→ 移除 `accessWidener` 键 → `0862eef2…`；
3. 重跑 ⇒ `NoClassDefFoundError: net/minecraft/class_3302` @ `DragonLibFabric.onInitialize`，另 18 条 `@Mixin target net.minecraft.class_xxx was not found`。

⇒ 结论：不是元数据小修，需要整包重映射；且 dragonlib 目前只是**库**（没有已装内容 mod 依赖它），因此本轮**跳过**。

---

## 3. CEI + DragonsPlus 第一断点

基线（未修）崩在 Bootstrap：
`NoClassDefFoundError: com/zurrtum/create/infrastructure/fluids/FlowableFluid$Still` @ `CDPFluids.registerPair(CDPFluids.java:63)`
（create-fly 26.3 把 `FlowableFluid.Still/Flowing` 移成 `FluidEntry$Still/Flowing`）。

已做：CP Utf8 就地改名（包内各 2 处；jar 其余 entry 不动；`residual old refs = 0`）⇒ 下一断点：
`java.lang.IllegalAccessError: failed to access class com.zurrtum.create.infrastructure.fluids.FluidEntry$Still from plus.dragons.createdragonsplus.registry.CDPFluids`。

`javap` 事实：`FluidEntry$Still/Flowing` 是**包私有 class**、构造器 **private(FluidEntry)**；create-fly 现行入口应是 `FluidEntry` 的 builder/工厂（`FlowableFluid` 仍是 public 基类）。
⇒ 修法不是加 access，而是**改写 `CDPFluids.registerPair` / `CEIFluids` 两层（DP 1 处 + CEI 1 处，约 6-10 行）走 26.3 的 FluidEntry 构造路径**，并核对返回类型（`RegisteredFluid` record 3 字段）。属 API 适配，跨轮。

---

## 4. 文件/复跑

- 候选（未 promote）：`g66/out/dragonlib-3.0.29-fabric-26.3-noaw.jar`、`…-stripjij.jar`、`g66/out/dp-1.11.4p1-26.3-flowfix.jar`、`g66/out/cei-2.5.2c-26.3-flowfix.jar`；
- staging：`g66/stage/batch2`（75）、`g66/stage/batch3`（76）；
- 复跑：`python g66/_dragonlib_strip.py` / `_dragonlib_noaw.py` / `_dp_flowfix.py` → `launch.py --game-dir … --mods … --watch-title`。

---

## 5. 建议下一步

1. CEI/DP：等上游 26.2/26.3 Fabric 构建，或按 §3 重写两处 fluid 注册（跨轮）；
2. 优先做 **natures_spirit 26.1.2 Fabric**（named、数据面大但无 create API 依赖）；
3. 1.21.x Fabric 库（dragonlib/playeranimator/lodestone）**一律跳过**（intermediary），除非做全量重映射流水线。
