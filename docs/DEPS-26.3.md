# DEPS-26.3 — MC 26.3 + Fabric 依赖盘点（Create Aeronautics + Simulated + Sable）

> 生成时间：2026-10-17（本机实测，Modrinth / GitHub / Fabric Maven API 全部查证）
> 目标：把「已有 / 缺失」盘清楚，能下载的都下到位。
> 所有版本号、约束字符串均来自**实测原文**，不是推测。

---

## 1. 补丁产物：Create-Fly 26.2 → 26.3

| 项 | 值 |
|---|---|
| 产物路径 | `work\aero-port\libs26\create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 大小 | 20,988,638 B（原件 21,272,478 B —— 变小是重压缩，条目集不变） |
| 原件 | `work\aero-port\libs26\create-fly-26.2-6.0.9-2.jar` |
| 补丁脚本 | `work\aero-port\tools\patch_createfly.py`（python `zipfile`，**未用 PowerShell 动 zip**） |
| 验证脚本 | `work\aero-port\tools\verify_patch.py` / `inspect_jar.py` / `jar_scan.py` / `scan_refs.py` |

### 改了什么

`fabric.mod.json` 里**唯一一行**：

```
-  "minecraft": ">=26.2- <26.3-",
+  "minecraft": ">=26.2- <26.4-",
```

### 验证结果（全部通过）

| 检查 | 结果 |
|---|---|
| 条目数 | 源 **17740** / 产物 **17740**（相等） |
| 条目集合 | `set(dst) == set(src)` ✅ |
| 条目顺序 | 完全一致 ✅ |
| **逐条目 SHA-256 比对** | **只有 `fabric.mod.json` 不同，其余 17,739 个条目字节级相同** ✅ |
| 压缩方式 | 无一处 `compress_type` 变化 ✅ |
| `testzip()` | 返回 `None`（无损坏条目）✅ |
| `META-INF/jars/` 条目 | 源 0 个 → 产物 0 个（**本来就没有**，不是被我丢的） |
| 其他元数据条目 | `META-INF/MANIFEST.MF`（含 `Fabric-Loom-Client-Only-Entries` 长行）、`create.classtweaker`（AW）、`create.mixins.json`、`create.client.mixins.json`、`LICENSE`、`licenses/*` 全部保留 ✅ |
| **重新读出 `fabric.mod.json`** | ✅ 可解析，`depends.minecraft == ">=26.2- <26.4-"` |
| 抽样读内容 | `assets/pack.png` 74,546 B、`create.mixins.json` 2,376 B 均可正常读出 ✅ |

重读出的最终 `depends` / `breaks`：

```json
"depends": { "fabricloader": "*", "minecraft": ">=26.2- <26.4-", "java": ">=25" }
"breaks":  { "fabric-api": "<0.152.0" }
```

> `breaks` 门槛 `<0.152.0` 对我们无影响：我们要装的 Fabric API 是 `0.163.0+26.3`。

---

## 2. Create-Fly 26.2 的原始声明与内嵌内容（实测）

### `depends`（原文）

| 依赖 | 约束 |
|---|---|
| `fabricloader` | `*` |
| `minecraft` | `>=26.2- <26.3-`（**已补丁放宽为 `>=26.2- <26.4-`**） |
| `java` | `>=25` |

### `breaks`（原文）

| 被排除 | 约束 |
|---|---|
| `fabric-api` | `<0.152.0` |

### 其他 `fabric.mod.json` 键

`id=create`、`version=6.0.9-2`、`name=Create Fly`、`license=CC0-1.0`、`environment=*`、
`accessWidener=create.classtweaker`、`mixins=[create.mixins.json, {create.client.mixins.json, client}]`、
entrypoints = `main` / `client` / `create_plugin`(`AllEarlyRegistries`) / `jei_mod_plugin` / `rrv_client`。

### 内嵌 jar 清单（`META-INF/jars/*.jar`）

**空 —— 0 个。**（确认了任务里「它说内嵌为空」的说法）

整个 `META-INF/` 只有 2 个条目：`META-INF/`（目录）、`META-INF/MANIFEST.MF`。

### 包结构（证明它是「全自带」的胖 jar）

17,740 条目 = `assets/` 7,850 + `com/` 5,229（**全部在 `com/zurrtum/create/` 下，5,227 个 class**）
+ `data/` 4,353 + `legacy_copper/` 275 + `holdmyitems/` 20 + `licenses/` 6 + 顶层配置 8。

⇒ **Flywheel、Ponder 都被 shade 进 `com.zurrtum.create`**，27 个 `.class` 级 `flywheel` 引用全是内部包名。

### 类引用扫描（对 5,227 个 `.class` 的常量池做关键字扫描）

| 关键字 | 命中 class 数 |
|---|---|
| `forgeconfigapiport` / `fuzs/forgeconfigapiport` | **0** |
| `net/minecraftforge` | **0** |
| `foundry/veil`、`veil` | **0** |
| `dev/ryanhcode`、`sable` | **0**（122 个 "sable" 命中全是 `Disable`/`Encasable` 之类的子串误报） |
| `molang` | **0** |
| `com/electron`、`teamresourceful`、`porting_lib`、`registrate`、`nightconfig` | **0** |

**结论：Create-Fly 26.2 自身在 26.3 上不需要任何伴随库**（除 Fabric Loader / Fabric API / Java 25）。
旧 `libs\` 里的 `forgeconfigapiport` / `veil` / `core` / `toml` / `molang` **不是 Create 的需求**，
而是 **Aeronautics/Simulated 侧的需求**（见 §4）。

### ⚠ 但有两个**自建垫片**仍然是必需的（给 Aeronautics 编译用）

Create-Fly 26.2 里**没有**这些包（实测条目计数）：

| 包 | 26.2 里的 class 数 |
|---|---|
| `com/tterrag/registrate/**` | **0** |
| `com/zurrtum/create/foundation/particle/**` | **0** |
| `com/zurrtum/create/foundation/data/**` | **3**（只有 `Mods`、`Mods$Builder`、`package-info`） |

⇒ `libs\create-fly-helpers-shim.jar`（11 class）+ `libs\create-fly-registrate-shim.jar`（49 class）
**在 26.2/26.3 上依然需要**，且它们是**对着 1.21.11 编的**，需要按 26.3 重编（或至少重验签名）。

---

## 3. 「已有 / 缺失」依赖矩阵（26.3）

| # | 依赖 | 26.3 有吗 | 版本 | 来源 URL | 结论 |
|---|---|---|---|---|---|
| 1 | **Fabric Loader** | ✅ 有 | `0.19.5`（稳定）/ `0.20.0` | `https://maven.fabricmc.net/net/fabricmc/fabric-loader/0.19.5/fabric-loader-0.19.5.jar` | **已下载** ✅ |
| 2 | **Fabric API** | ✅ 有 | `0.163.0+26.3`（`depends: loader>=0.19.3, java>=25, minecraft ~26.3-`；内含 44 个模块 jar） | `https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/0.163.0%2B26.3/fabric-api-0.163.0%2B26.3.jar` | **已下载** ✅ |
| 3 | **Create（Create-Fly）** | ⚠ 上游无 26.3 | 上游最新 `v6.0.9-26.2-2`（26.2） | 上游：`github.com/ZurrTum/Create-Fly`；本地已有 26.2 jar | **已打补丁**：`create-fly-26.2-6.0.9-2-26.3-patched.jar` ✅ |
| 4 | **Forge Config API Port** | ✅ **有 26.3！** | `26.3.1`（`ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar`） | `https://cdn.modrinth.com/data/ohNO6lps/versions/JpKvrr9J/ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar` | **已下载** ✅ |
| 5 | ↳ `depends`（FCA 26.3.1 原文） | — | `minecraft ~26.3-`、`fabricloader >=0.19.4`、`fabric-api >=0.160.6` | 同上 | 与本包 #1/#2 相符 ✅ |
| 6 | ↳ **nightconfig `core`** | ✅ 不需要单下 | `core-3.8.4.jar`（旧版 3.8.3） | FCA 26.3.1 的 `META-INF/jars/` JiJ | **已被 FCA 内嵌覆盖** ✅ |
| 7 | ↳ **nightconfig `toml`** | ✅ 不需要单下 | `toml-3.8.4.jar` | 同上 | **已被 FCA 内嵌覆盖** ✅ |
| 8 | ↳ FCA 的 v5 配置 API | ✅ 仍在 | `fuzs/forgeconfigapiport/fabric/api/v5/ConfigRegistry.class` 存在 | 实测 FCA 26.3.1 条目 | Aeronautics 的 `Fabric*ConfigService` 里的 `v5` import **不用改** ✅ |
| 9 | **Veil（Foundry Veil）** | ❌ **不存在** | 最新 `4.5.2`，**只有 1.21.1**（Modrinth 109 个版本 `game_versions` 全为 `["1.21.1"]`） | `https://modrinth.com/mod/veil`（id `3KUWeVhG`）；GitHub `FoundryMC/Veil`，**分支只到 `1.21`**，最新 release `mc1.21.1-4.5.2-fabric`(2026-10-10)，license LGPL-3.0 | **需自己编，或用垫片顶掉** ⚠ |
| 10 | ↳ **`molang-compiler`** | ❌ 无独立发布 | `3.1.1.19` | 只作为 **Veil 的 JiJ** 存在（`META-INF/jars/molang-compiler-3.1.1.19.jar`，另有 `glsl-processor-0.2.3.jar`） | 无 26.x 独立包；**随 Veil 一起解决**（编 Veil 时顺手带上） ⚠ |
| 11 | **Sable** | ❌ 不存在 | 最新 `2.0.6`，**只有 1.21.1**（Modrinth 28 个版本全 `["1.21.1"]`） | `https://modrinth.com/mod/sable`（id `T9PomCSv`）；GitHub `ryanhcode/sable` 只有 `mc1.21.1-*` release | **必须自己编**（另有人在做，PolyForm-Shield-1.0.0）❌ |
| 12 | **Sable Companion** | ❌ 不存在（**Modrinth 上根本没有**） | `1.21.1-1.6.0` | GitHub `ryanhcode/sable-companion`：**只有 `main` 一个分支、0 个 release**，**license = MIT** | **必须自己编**（最便宜的一件：17 个 class / 36 KB，MIT 授权最干净）❌ |
| 13 | **Create Aeronautics / Simulated** | ❌ 不存在 | 只有 `1.21.1`（Modrinth id `oWaK0Q19`，`categories: neoforge`） | `https://modrinth.com/mod/create-aeronautics` | **必须自己编**（= 我们自己的 `aeronautics-fabric`）❌ |
| 14 | `create-fly-helpers-shim` | — 非上游 | 自建，11 class | 本地 `libs\create-fly-helpers-shim.jar` | **仍需**，需按 26.3 重编 ⚠ |
| 15 | `create-fly-registrate-shim` | — 非上游 | 自建，49 class（含 `com.tterrag.registrate.*`） | 本地 `libs\create-fly-registrate-shim.jar` | **仍需**，需按 26.3 重编 ⚠ |

### 一句话总结矩阵

- **26.3 上现成可用的**：Fabric Loader、Fabric API、Forge Config API Port（+ 它 JiJ 的 nightconfig core/toml）、
  以及**打了补丁的 Create-Fly 26.2**。这四样**全部已下到位**。
- **26.3 上不存在的**：Veil、molang-compiler、Sable、Sable Companion、Aeronautics/Simulated
  → 全部只能自己编（或垫片）。
- 好消息：**Create 侧一个伴随库都不需要**（§2 扫描证明），要把 26.3 跑起来的技术缺口
  **完全集中在 Sable 那一套 + Veil** 上。

---

## 4. 为什么旧版 `libs\` 里那堆伴随库会出现（归因更正）

旧 1.21.11 那套的 `build.gradle`（`work\aero-port\aeronautics-fabric\build.gradle`）里的真实归因：

| 旧 jar | 谁需要它 | 26.3 上的处置 |
|---|---|---|
| `forgeconfigapiport-fabric-21.11.1.jar` | **Aeronautics/Simulated**（`FabricAeroConfigService` / `FabricSimConfigService` 用 `fuzs...api.v5.ConfigRegistry`） | 换 FCA `26.3.1` ✅ 已下 |
| `core-3.8.3.jar` / `toml-3.8.3.jar` | 上面那个的 JiJ 依赖（`modLocalRuntime`） | 换 3.8.4，**由 FCA JiJ 自带**，不用单独放 ✅ |
| `veil-fabric-1.21.1-4.5.0.jar` | **Aeronautics/Simulated**（`src/main` 里 **86 处** `foundry.veil` import） | ❌ 无 26.3；见下 |
| `sable-companion-fabric-1.21.1-1.6.0.jar` | **Aeronautics**（`dev.ryanhcode.sable.companion.*`，**sable 本体里没有这个包**，实测 0 个 class） | ❌ 自己编（MIT） |
| `molang-compiler-3.1.1.19.jar` | Veil 的 JiJ（`modLocalRuntime`） | 随 Veil |
| `create-fly-*-shim.jar` | Aeronautics 编译期的 Create 内部 API 垫片 | ⚠ 仍需，重编 |

### Veil 的真实耦合面（决定「编 Veil」还是「写垫片」）

`src/main` 里 **16 个不同符号 / 86 处 import**：

| 分组 | 符号 | import 数 |
|---|---|---|
| **网络**（已知已写过垫片） | `VeilPacketManager` 27、`ServerPacketContext` 20、`ClientPacketContext` 9、`PacketContext` 8 | **64** |
| 渲染/杂项 | `VeilRenderLevelStageEvent` 4、`Color` 3、`Colorc` 2、`MatrixStack` 2、`VeilLevelPerspectiveRenderer` 2、`VeilEventPlatform` 2、`AdvancedFbo` 2、`CodecReloadListener` 1、`CodecUtil` 1、`VeilRenderSystem` 1、`PostPipeline` 1、`PostProcessingManager` 1 | **22** |

> 注意：`excluded-wip`（未编译进产物）另有 3 处 veil import，不计。
> 也就是说：**74% 的 Veil 耦合是 4 个网络符号**，垫片化成本主要在剩下 12 个渲染符号上。

---

## 5. 必须我们自己编的清单（按难度/风险排序）

| 顺序 | 组件 | 为什么必须自己编 | 授权 | 体量参考 |
|---|---|---|---|---|
| ① | **Sable Companion** | Modrinth 无、GitHub 仅 `main`、官方只出 1.21.1 | **MIT**（最干净） | 17 class / 36 KB |
| ② | **Sable** | 上游只有 1.21.1（2.0.6） | PolyForm-Shield-1.0.0（禁竞争性使用） | 783 java / 48,312 行 + Rust `sable_rapier` |
| ③ | **Aeronautics / Simulated** | 上游只有 1.21.1（NeoForge） | `LicenseRef-Simulated-Project-License`（自定义） | 现成 `aeronautics-fabric` 工程 |
| ④ | **Veil**（或垫片） | 上游分支只到 1.21，Modrinth 全 1.21.1 | LGPL-3.0 | 需覆盖上表 16 个符号 |
| ⑤ | 两个 Create 垫片 | 非上游资产，签名对 1.21.11 | 自建 | 11 + 49 class |

**Sable 那一套（①②③）是主战场；Veil（④）是第四条隐蔽的硬依赖，别忘。**

---

## 6. 交付物：`work\aero-port\libs26\` 现状

| 文件 | 大小 | 说明 |
|---|---|---|
| `create-fly-26.2-6.0.9-2-26.3-patched.jar` | 20,988,638 | **本次产物**，minecraft `>=26.2- <26.4-` |
| `create-fly-26.2-6.0.9-2.jar` | 21,272,478 | 未打补丁的原件（保留对照） |
| `fabric-api-0.163.0+26.3.jar` | 1,774,707 | ✅ 新下载 |
| `fabric-loader-0.19.5.jar` | 1,984,980 | ✅ 新下载 |
| `ForgeConfigAPIPort-v26.3.1-mc26.3.x-Fabric.jar` | 609,574 | ✅ 新下载 |
| `sable-fabric-1.21.1-2.0.6.jar` | （下载中，他人在跑） | 官方 1.21.1 基线，**非本任务产物**，未动 |

API 查询缓存（JSON/XML 原文）已挪到 `work\aero-port\tools\api-dumps\`，不污染 `libs26`。

### 复用的脚本（都在 `work\aero-port\tools\`）

| 脚本 | 用途 |
|---|---|
| `patch_createfly.py` | 打补丁 + 重打包 + 自校验（条目数/集合/testzip/回读） |
| `verify_patch.py` | 逐条目 SHA-256 对比、压缩方式对比、关键元数据存在性 |
| `inspect_jar.py` | 列条目/内嵌 jar/读 `fabric.mod.json` |
| `jar_scan.py` | 包结构统计 + 关键字命中 |
| `scan_refs.py` | 对 class 常量池做伴随库关键字扫描 |
| `modrinth_check.py` / `modrinth_search.py` | Modrinth `project` / `version` / `search` 查询（`game_versions` 是否含 26.x） |
| `gh_check.py` / `parse_gh.py` | GitHub API（分支/Release/license）—— ⚠ python urllib 打 `api.github.com` 会 403，**要用 `curl.exe` 下 JSON 再让 python 解析** |

---

## 7. 风险 / 待验

1. **补丁只放宽了版本字符串，没验运行期兼容**。`>=26.2- <26.4-` 能让 Fabric Loader 放行，
   但 26.2→26.3 的 mixin target / 方法签名是否还匹配，只能真启动才知道。
2. **`java >=25`**：Fabric API `0.163.0+26.3` 与 Create-Fly 26.2 都要求 Java 25（= `java-runtime-epsilon`）。
3. **Veil 是第四条硬依赖**，容易被"Sable 编完就好了"的叙事盖过去；`src/main` 有 86 处 import。
4. **`sable-companion` 的 `dev.ryanhcode.sable.companion.*` 不在 `sable` jar 里**（实测 sable 2.0.5 port 里该包 0 个 class）
   —— 两个 jar 都要，别以为编好 sable 就够了。
5. FCA `26.3.1` 要求 `fabricloader >=0.19.4`：用 `0.19.5`/`0.20.0` 都行，**别用 0.19.3 及以下**。
