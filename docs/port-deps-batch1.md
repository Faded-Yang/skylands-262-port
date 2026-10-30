# port-deps-batch1 —— 缺失 mod 移植·依赖库批 1（Paxi / YungsApi + 状态盘点）

> 日期：2026-10-19 ｜ 专线：crashfix-26 ｜ 目标：MC 26.3 + Fabric Loader 0.19.5 + Java 25
> 验收：标题 = `launch.py --watch-title` 三标记；进世界 = `logged in with entity id`（全新 game-dir + 全新模板存档副本）。
> 本轮全部实验在 `work/run26/port/g66/`，**未写 mods-stable / watch**。

---

## 0. 结论（批 1：依赖库，2 个 PASS）

| mod | 源版本 | 依赖 | jar SHA-256 | staging | 结果 | 遗留 |
|---|---|---|---|---|---|---|
| **yungsapi** | 1.21.1 NeoForge 5.1.9 → **26.1.2-Fabric-6.1.3**（patched4） | fabric-api | `53d7ed9ee4fcb8b90a55d5dc6633b7d8ed3926a4c6243671d9262273240aee5b` | `g66/stage/batch1`（74 jar） | ✅ **TITLE 36.6s + WORLD 50.3s**，0 mixin apply failed / 0 crash / 0 registry errors | 功能面（结构放置增强）未逐项验 |
| **paxi** | 1.21.1 NeoForge 5.1.3 → **26.1.2-Fabric-6.1.0** | yungsapi | `09591c50d39b510a775e54bb25634e282f7241888a8fc957bd677ddc0e730222` | `g66/stage/batch1` | ✅ 同上（mod 列表含 `paxi 26.1.2-Fabric-6.1.0`） | `config/paxi/datapacks` 未建，数据包/世界预设功能待验 |

- 基线 = **当前 live 72 jar**：aeronautics `1BED71C9…`(31,593,072 B) · sable `1088C4FE…`(9,371,968 B) · create-fly `0E9B26D3…`(19,648,977 B) · sky262crashfix `4954F78C…`。
- 启动日志：`Loading 155 mods`、`Loaded 2343 advancements`、`logged in with entity id 64 at (-323.5, 71.0, -41.5)`。
- 证据：`g66/out/evidence/01_title.txt`、`03_checks.txt`、`batch1-world-final-result.json`、`batch1-world-final-latest.log`。

---

## 1. 依赖库状态盘点（按 lead 要求：广度优先，失败不卡）

| 库 | 原包版本 | 最新 Fabric | 状态 | 原因/下一步 |
|---|---|---|---|---|
| yungsapi | 5.1.9 (NeoForge 1.21.1) | 26.1.2-Fabric-6.1.3 | ✅ **已移植 PASS**（patched4：3 类 / 9 处补丁，沿用 r408 成果） | — |
| paxi | 5.1.3 (NeoForge) | 26.1.2-Fabric-6.1.0 | ✅ **已移植 PASS** | 数据包目录未建，功能待验 |
| kotlinforforge | 5.12.0-all | 仅 Forge/NeoForge（26.3 NeoForge 6.4.0） | ✅ **替代完成**（无需 jar） | 交付件已有 `fabric-language-kotlin 1.14.2+kotlin.2.4.21`，Fabric 侧 Kotlin 由此提供 |
| dragonlib | 3.0.29 (NeoForge 1.21.1) | **Fabric 1.21.1 构建存在**（磁盘 `port/dragonlib/dragonlib-3.0.29+mc1.21.1-fabric.jar`，3,081,029 B，已放宽 minecraft 范围到 `>=26.1- <26.4-`） | 🔶 **下一批候选** | 需 1.21.1→26.3 两层 API 适配 + 剥离 3 个 JIJ 1.21 嵌套 jar + architectury 13→交付件 22.0.5 核对 |
| lodestone | 1.8.2 (NeoForge 1.21.1) | Fabric 1.21.1 构建存在（9,592,279 B） | ❌ **失败（依赖缺失）** | 依赖 `porting_lib_base`，26.3 Fabric 无等价物；移植该前置成本远大于收益 |
| blueprint | 8.2.0 (NeoForge 1.21.1) | **无**（仅 Forge/NeoForge） | ❌ 失败（无 Fabric 构建/无源码） | 493 类 / 285 neoforge 引用，NeoForge 专属 |
| playeranimator | 2.0.4 (NeoForge 1.21.1) | Fabric 仅到 1.21.x 快照（23w13a_or_b） | ❌ 暂缓（两层 port） | 需 1.21.x→26.3 适配，属内容 mod 依赖时再做 |
| mysterious_mountain_lib | 1.2.15 | 无 Fabric（mmlib 为 NeoForge/Forge 专属，待复核） | ❌ 失败 | 无 Fabric 构建 |
| ftb-library / ftb-teams / ftb-quests | 2101.1.36/37 | 无 Fabric | ❌ 失败（价值低） | 仅 Forge/NeoForge；FTBQ 内容依赖链长 |

---

## 2. 本批踩到的两个坑（已修/已绕开）

1. **新 game-dir 首启卡「讲述人/辅助功能」请求界面** ⇒ 客户端停在标题前，日志没有 `Starting integrated`。
   lead 已修 `tools/launch26/launch.py`：启动前确保 `<game-dir>/options.txt` 含 `narrator:0` / `onboardAccessibility:false` /
   `skipMultiplayerWarning:true` / `tutorialStep:none`（只补/覆盖这 4 项）。卡住时**直接 kill 重跑**，不要等。
2. **`quickPlaySingleplayer` 在 26.3 是 `withOptionalArg()`：空格形式不生效**（`--quickPlaySingleplayer lm-final` 无效 ⇒ 停在标题）。
   必须 `--quickPlaySingleplayer=<world>`（= 形式）。`tools/watch_world.py` 目前用空格形式 ⇒ **别用它跑 world**；
   本轮用 `g66/_world.py --eq-form`（拷贝 `g21/template/lm-final` → `saves/lm-final`，删 `session.lock`，然后 `=` 形式 quickPlay）。

---

## 3. 复跑

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g66
python _mkbatch1.py     # 重建 staging = 当前 live 72 jar + 2 个库（hardlink + copy）
python _world.py --mods stage/batch1 --game game-x --tag x --timeout 240 --eq-form   # 进世界验收
```

---

## 4. 下一批建议（按依赖优先）

- **dragonlib**（Fabric 1.21.1 件已在磁盘，唯一阻塞是 1.21.1→26.3 + JIJ）→ 它解锁 `CreateDragonsPlus` 等。
- 内容侧 26.1.2 Fabric 已有的：`create-enchantment-industry`（前后置 DragonsPlus）、`natures-spirit`（数据面大）。
- `aerocopycats` 纯数据（30 个 `copycats:physics_block_properties` + 2 个空 @Mod 类）⇒ 需先移植 `copycats`（P0/P1 里的大件）。
