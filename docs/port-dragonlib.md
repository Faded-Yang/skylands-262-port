# port-dragonlib —— dragonlib 3.0.29（Fabric 1.21.1）移植**失败**分析

> 日期：2026-10-19 ｜ 专线：crashfix-26 ｜ 结论：**失败（不进交付）**，原因不是 classTweaker 元数据，而是**整包 intermediary 命名空间**。
> base = 当前 live **74 jar**（aeronautics `1BED71C9…`、sable `1088C4FE…`、create-fly `0E9B26D3…`）。

---

## 0. 状态（lead 格式）

| mod | 源版本 | 依赖 | jar SHA-256 | staging | 结果 | 遗留 |
|---|---|---|---|---|---|---|
| dragonlib | 3.0.29+mc1.21.1-fabric（唯一 Fabric 构建是 1.21.1） | architectury>=13（live 22.0.5）、fabric-api | 候选 `0862eef23c587867b8b621cc00ca3fb14ab26f34d1b358410c8222ac3a155afa`（1,357,664 B） | `port\g66\stage\batch2`（**未 promote**） | ❌ **失败**：启动即 `RuntimeException: Could not execute entrypoint stage 'main' … NoClassDefFoundError: net/minecraft/class_3302` | 需 **intermediary→official 全量重映射**（mappings + tiny-remapper）；或等上游 26.x Fabric 构建 |

---

## 1. 做过的两步（都必要但都不够）

1. **剥 JIJ**（lead 要求）：原 jar 内嵌 3 个 1.21.1 依赖 `architectury-fabric-13.0.6` / `forgeconfigapiport-fabric-21.1.1` / `mixinextras-fabric-0.5.3`，与 live 的 architectury 22.0.5 / ForgeConfigAPIPort 26.3.1 / loader mixinextras 0.5.5 冲突 ⇒ 删除 `META-INF/jars/*` 与 `fabric.mod.json` 的 `jars` 列表。候选 `86f854fa…`。
2. **classTweaker 崩**：`dragonlib.accesswidener` 头是 `accessWidener v2 intermediary`，条目全是 `net/minecraft/class_xxx`；26.3 loader 运行期 namespace = `official` ⇒ 直接 `ClassTweakerFormatException: Namespace (intermediary) does not match current runtime namespace (official)`，启动即崩。
   **按 lead 优先级 2 处理**：从 `fabric.mod.json` 移除 `accessWidener` 键（文件留在 jar 内不读）。候选 `0862eef2…`。
3. 重跑标题 ⇒ **更深的同类问题**：crash-report `Initializing game` / `Could not execute entrypoint stage 'main' … DragonLibFabric.onInitialize(DragonLibFabric.java:9)` / `Caused by: NoClassDefFoundError: net/minecraft/class_3302`。
   同时日志有 18 条 `@Mixin target net.minecraft.class_xxx was not found`（`class_1792/class_2818/class_310/…`）—— 说明**整个 jar 的 MC 引用都是 intermediary 名**，不是个别条目的问题。

---

## 2. 判据（census，可复算）

| jar | intermediary 引用 | named 引用 | 结论 |
|---|---|---|---|
| dragonlib 3.0.29（1.21.1 Fabric） | **3,271** | 2 | 必须整包重映射 |
| YungsApi 26.1.2-Fabric-6.1.3 | 0 | 606 | 可用（已 PASS） |
| Paxi 26.1.2-Fabric-6.1.0 | 0 | 26 | 可用（已 PASS） |
| CEI 26.1.2 Fabric | 0 | 1,214 | 可用（下一批） |
| DragonsPlus 26.1.2 Fabric | 0 | 647 | 可用（下一批） |

⇒ **规则（已验证，写进台账）**：本项目 26.3 运行期是 **official（named）命名**；**26.x 的 Fabric 构建是 named**（可直接放宽版本跑），**1.21.1 的 Fabric 构建是 intermediary**（启动即 class_xxx 找不到，必须全量重映射）。

---

## 3. 为什么本轮不继续做全量重映射（广度优先决策）

- 需要 1.21.1 的 **intermediary→Mojang official** 映射（官方 intermediary + Mojang mappings 组合），再对 614 个类 / 3,271 处引用做 tiny-remapper；
  同时 mixin refmap（`dragonlib-*-refmap.json`）与 AW 条目也要跟着转 named —— 工作量接近「重做一次移植」，且 dragonlib 只是**库**（当前没有已装内容 mod 依赖它）。
- 按 lead「广度优先、失败不卡」：**标记失败并继续**（CEI/DragonsPlus 26.1.2 是 named，已开始 batch3）。

---

## 4. 证据 / 复现

- crash report：`g66/out/evidence/dragonlib-crash-report.txt`（NoClassDefFoundError class_3302）。
- candidate（未 promote）：`g66/out/dragonlib-3.0.29-fabric-26.3-noaw.jar`（`0862eef2…`）、`…-stripjij.jar`（`86f854fa…`）。
- staging：`g66/stage/batch2`（75 jar，含未 promote 的 dragonlib；**该 staging 不应被 promote**）。
- 重跑：`python g66/_dragonlib_strip.py` → `_dragonlib_noaw.py` → `launch.py --game-dir …/game-batch2b --mods …/stage/batch2 --watch-title`。

---

## 5. 后续若必须做

1. 取 1.21.1 intermediary mappings（Fabric maven）+ Mojang official mappings，组合成 intermediary→official tiny v2；
2. `tiny-remapper` 重映射 614 类 + mixin refmap + AW 条目 → 生成 named 版；
3. 再回 batch2 流程（title → world），并核对 architectury 22 API 兼容。
