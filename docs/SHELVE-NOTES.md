# 搁置与恢复说明（SHELVE NOTES）

> 面向「半年后回来接手」或「换一个人接手」：这里只写**当前事实 + 恢复所需的最小步骤 + 已知欠账**。
> 细节不在这里展开，按每节末尾的指针去读 docs/ 里的原文档。

---

## 1. 当前状态快照（2026-10-30）

| 项 | 值 |
|---|---|
| 交付版本 | **1.0.7**（2026-10-21，说明见 `docs/release-1.0.7.md`） |
| 交付件 | `work/run26/mods-stable/*.jar` = **118 jar / 118 个 mod id**；体积 173,807,510 B（≈165.8 MiB） |
| 平台 | **Minecraft 26.3**（官方未混淆 jar）+ **Fabric Loader 0.19.5** + **Java 25** |
| 清单 | `docs/DELIVERED-JARS.md`（文件名 / 字节 / SHA-256 前 16 位 / 来源分类；**仓库里没有 jar 本体**） |
| 内容规模 | 4212 blockstate / 4736 item 模型；汉化全命名空间 missing = 0（42 个 namespace） |
| 原包覆盖 | 110 mod 里绝大多数已覆盖，剩余缺口三类见 `docs/port-remaining-263.md` |

**已经验证过的（可当基线）**

- 标题画面 + 进入世界（`tools/launch26/launch.py --watch-title`；1.0.7 终验 0 crash / `Registry loading errors`=0）；
- 创造栏 35 个 tab / 1121 个可见物品格截图检测：missing（品红·黑棋盘）= 0；
- 机器矩阵 round 3（belt / mechanical crafter / deployer 建网 + 插料）、任务书 J 键 / 543 任务、喷气背包、打印器等按 `docs/release-1.0.7.md` 与 `docs/DELIVERY.md` 逐条验过；
- 汉化：`tools/lang_audit.py` 全量 0 坏文件（26.3 一次解析所有 mod lang，任一坏 JSON 会让**全部** mod 语言失效）。

**没有验证过的**

- 长时稳定性 / 存档跨版本兼容 / 多人（专用服务器只做过 server-safe 冒烟）；
- 所有件只到「标题 + 进世界 + 抽样 MCP 实拍」，不是逐功能回归。

> ⚠ **数字口径**：docs/ 里的 71 / 93 / 97 / 114 / 118 jar 是**不同轮次**的数字（1.0.7 = 118）。看到旧文档写 97 是当时的快照，不是当前事实。

---

## 2. 恢复工程的最小步骤

### 2.1 装什么

1. **Java 25 运行时**：工程里所有脚本默认用官方启动器下载的运行时
   `%APPDATA%\.minecraft\runtime\java-runtime-epsilon\bin\java.exe`（`tools/decompile.py` 与 `launch.py` 的默认值）。
2. **一份可用的 `.minecraft`（只读用）**：需要 26.3 的 version json + `<ver>.jar` + assets index（`--mc-dir` 默认 `%APPDATA%\.minecraft`，launch.py 只读它）。
3. **Fabric Loader 0.19.5 的 profile json**：`work/fabric-profile-26.3.json`（launch.py 用它拿 loader 的 7 个库坐标）。
   `work/` 被 `.gitignore` 排除，**仓库里没有这份**；用 Fabric installer 生成一次 26.3 的 profile json 放回去即可。
4. **Python 3.10+**（本工程用 DSH 自带 python 跑 `tools/`，不依赖 Gradle/Loom）。

### 2.2 拿到那 118 个 jar

- **仓库不发布任何 jar**（许可证 + 体积），按 `docs/DELIVERED-JARS.md` 的表自行合法获取；
- 上游件按文件名/版本号去对应发布页找（26.3 原生件 38 个、跨版本直装 4 个）；
- **自研/移植件（`sky262-*`）没有上游可下**：需要原工程的工作区（`work/aero-port/`、`work/sable-26/`、`work/run26/backups/`、
  `work/run26/candidates-2026-10-22/`）或用仓库里的 `tools/` 重新构建 —— 这部分如果原工程丢了，就是本仓库最大的不可恢复点，先确认备份。
  ⚠ 2026-10-30 清理时已删除全部 `work/run26/port/g*/` 轮次脚手架（见 `docs/cleanup-2026-10-30.md`），
  历史文档里出现的 `work/run26/port/gNN/...` 路径**已不存在**，只是当时的取证记录。

### 2.3 反编译参考树 `work/refs/mc26.3` 怎么来

~~~powershell
# 1) 下载 Vineflower 1.10.1 放到 tools/decompiler/
#    https://repo1.maven.org/maven2/org/vineflower/vineflower/1.10.1/vineflower-1.10.1.jar
# 2) 用 26.3 客户端 jar 反编译（26.x 是官方未混淆，反编译出来直接是 named）
python tools/decompile.py <26.3 客户端 jar> work/refs/mc26.3
~~~

- 同法反编译 `create-fly-*.jar` 得到 `work/refs/create-fly`（Create 侧 API 语义唯一权威）；
- `tools/decompile.py` 断点续跑：已存在的 `.java` 会跳过，失败条目会打印。

### 2.4 验证件（**不进交付**）

- `mcpfabric`（26.3 Fabric 客户端 mod，bridge `127.0.0.1:25599`）：放 staging 的 `mods` 里，
  `config/mcpfabric.config.json` 里 `enableUiControl/enableVision/enableCommands` 置 true，token 同文件；
- 客户端连接器：`tools/mcpfabric_client.mjs`；**免引号桥调用器**：`tools/visual-audit/mcpc.mjs`
  （PowerShell 直接传 JSON 会把反斜杠吃掉，历史踩坑）；
- `sky262-mcp`（自研客户端 mod，WS 25576）用于截图/交互，同样只进 staging。

### 2.5 恢复后 30 分钟内该做的三件事

先自建一个 staging 目录（**旧的 `port/g300/game-vis1` 已随清理删除**）：

~~~powershell
# ⓪ 建 staging：空目录即可，launch.py 会把 mods/natives/logs 写进去
mkdir work/run26/stage-new

# ① 标题画面基线（顺带验 Java/loader/profile 是否齐）
python tools/launch26/launch.py --game-dir work/run26/stage-new --mods work/run26/mods-stable --timeout 900

# ② 模型烘焙离线审计（权威显示口径，见第 4 节）
python tools/audit_models.py --out work/run26/audit/report.md

# ③ 语言审计（坏一个 JSON 会让所有 mod 语言失效）
python tools/lang_audit.py
~~~

---

## 3. 已知未完成项（按严重度）

### 3.1 显示 / 模型（最大一块欠账，详见 `docs/R569-model-display-audit.md` 第 7 节）

| 欠账 | 规模 | 状态 |
|---|---|---|
| 坏模型（离线审计口径） | **item 97 个 id / block 71 个 id** | 未修，清单 `scratch/audit/broken.json`（本仓库已同步） |
| interiors `#missing` 修复件 | 306 个模型覆盖（预期 `Missing texture references` 395→89） | **候选未 promote**：`work/run26/candidates-2026-10-22/out/sky262-modelfix-1.0.0.jar`（103,131 B，mod id 已改 `zsky262_modelfix` 以保资源包优先级，SHA 前缀 `7A1488F6`；原 `port/g300/out/` 路径已于 2026-10-30 清理迁移）；明细 `scratch/fix/CHANGELOG.md` |
| toolgun 缺 png | 日志 8 条 / 7 个唯一 item id（`create_aeronautics_toolgun`） | 未修（上游 1.21.1 资源未找到等价件） |
| tfmg 屏障图标 | `sky262-tfmg` **16 个 item 的 `items/<id>.json` 直接指向 `minecraft:item/barrier`** | 未修（上游 slug 在 26.3 无版本/404） |
| `tfmg:crankshaft` UV 越界 | uv 17..26 落在 16x16 图上 ⇒ `FaceBakery` 抛 `IllegalArgumentException`（26.3 不认 NeoForge `texture_size`，旧版是钳位） | 未修，需按 16x16 重算 uv |
| sophisticated 共用占位图标 | storage 51 + backpacks 14 个 id 全指向 `item/advanced_alchemy_upgrade` | 候选未 promote：`g300/out/sky262-sophisticated-{backpacks,storage}-*.jar`（从 Modrinth 26.3 上游取的资源补丁，`.orig` 是原件） |
| 下一轮第一件事 | 把 audit 报的 **71 个 block id** 逐个 `setblock` 实拍，区分「紫黑 / 不可见 / 形状错」 | `tools/visual-audit/block_audit.py`（约 2 分钟/批，需独占实例） |

### 3.2 内容 / 功能降级（详见 `docs/KNOWN-LIMITATIONS.md`，这里只列最容易误判为 bug 的）

- 装饰线：createdeco 389/389、Design-n-Decor 774/846 —— **无 BlockEntity、无交互/动画**（纯外观，ponder 未做）；
- natures_spirit：树用 26.3 原版 placer（NS 自定义 28 个 tree 类未移植）；village 结构数据未恢复；
- CEI `experience` 三个 ponder 场景：旧 1.21 BE nbt 已移除，场景几何在、**BE 初始状态回退默认**；
- sophisticated backpacks/storage、TFMG、Create: Connected：**机器无功能、纯装饰**；图标统一降级为扁平 `item/generated`；
- `portable_engine_liquid_fuel` / `createliquidfuel` 是**兼容壳**（只保证加载，无任何数据/行为）；
- 浮空岛世界：岛只有 2~5 格厚 ⇒ 洞穴几乎挖不出来；船可能浮空（用户已接受，见 `docs/DELIVERY.md` 第三节）。

### 3.3 用户侧未闭环

- 用户说「绝大多数物品显示有问题」，**在 1.0.7 上无法复现**（1121 格实测 missing=0）⇒ 需要一张他看到的截图 + 世界名才能定位；
- 实验性存档 `sky islands` **不能 quickPlay 无人值守进**（`BackupConfirmScreen` 继承 `Screen`，mcpfabric `ui.*` 白名单不含 ⇒ 点不掉；人手动点一次可以进）。验证一律用干净存档（如 `vis1`）。

---

## 4. 验收口径（**最容易犯的错**）

> **不要**用「grep 某个日志字符串 = 0」当模型/显示修好的判据。1.0.3 起 `Missing textures in model` 恒为 0，
> 而 26.3 同样致命的三类**不在这条字符串里**：
>
> - `Missing texture references in model <model>: <slot>`（1.0.7 实测 395 行）
> - `Rejecting block model <id>, since it contains sprites from outside of supported atlas`（32 行 = 29 个模型）
> - `Unable to bake item model: '<id>'`（1 行 = `tfmg:crankshaft`）
>
> **正确口径**：`python tools/audit_models.py` 的 reason 计数（它已与真机 `latest.log` **7 类全对齐**：
> 395/395、29/29、8/8、4/4、2/2、1/1、0/0）。另有两条硬纪律：
>
> 1. **不能只看离线审计**：坏模型多半是「渲染不出来」而不是品红 ⇒ 抽样必须 `setblock` + 实拍；
> 2. **改 jar 前先备份并记 SHA**，只让目标 class 变化；手写 jar 必须带目录条目（否则 lang 枚举不到）⇒ `tools/pack_jar.py`。

---

## 5. 本仓库里有什么 / 没有什么

| 有 | 没有（也不该有） |
|---|---|
| `docs/` 全部工程文档（作废的 1.21.11 时期三份除外） | 任何 `.jar` / 游戏 assets / 反编译的 mod 代码 |
| `tools/` 自写脚本（反编译、打包、启动器、审计、MCP 客户端） | `work/`（构建产物、staging、日志、mods-stable） |
| `src/` minecraft-mcp 客户端 mod 的 26.3 适配源码 | `.minecraft` / Java 运行时 / Vineflower jar |
| `examples/` 自研 mod 示例（任务系统）与启动脚本 | 用户存档、截图、实验室 staging |
| `scratch/audit/`、`scratch/fix/` 本轮审计与修复记录（机读清单） | node_modules、二进制工具（`github-mcp-server` 等） |

**本轮会话脚本的路径映射**（原工程在 `scratch/`，本仓库收进 `tools/visual-audit/`，内容逐字同步）：

| 原路径 | 仓库路径 |
|---|---|
| `scratch/mcpc.mjs` | `tools/visual-audit/mcpc.mjs` |
| `scratch/{tour,gridscan,iconscan,flatdup,langscan}.py` | `tools/visual-audit/` 同名 |
| `scratch/vis/*.py`（含 `icon_audit.py` / `block_audit.py`） | `tools/visual-audit/` 同名（`sys.path` 已改为按文件定位） |
| `scratch/vis/blocklist.json`、`blockaudit/homography.json`、`batch_validity.json` | `tools/visual-audit/`（`blockaudit/` 子目录保留） |
| `scratch/audit/{report.md,broken.json}`、`scratch/fix/CHANGELOG.md` | `scratch/audit/`、`scratch/fix/`（路径不变，文档引用可直接用） |

> 这些脚本里的**绝对工程路径**仍指向原机目录（`C:\...\skylands-262`），跑之前按本机路径替换；
> 配套的游戏截图 / `all_results.json` 等运行产物不随仓库发布。

---

## 6. 不要重试的死路（完整清单见 `docs/HARD-RULES.md`、`docs/LEDGER-FULL.md` 搜「死路」）

- 用 mcpfabric `ui.*` 点掉「实验性存档」确认框 —— 类不在白名单，永久 `ui_refused`；
- 用 Windows 桌面 MCP 注入游戏窗口 —— 受「用户空闲」门控，且必须先 `AppActivate`；
- 假设 item 模型只走 item 烘焙链 —— Create 的 Flywheel PartialModel 会把 item 模型**按 block 规则** bake（`Rejecting` 的主因）；
- 假设 26.3 认 NeoForge 的 `texture_size` —— 不认（真实 jar 里 0 个类含该字符串）；
- 用文件路径前缀直接判图集归属 —— armor trim 是 `paletted_permutations` 运行时生成；
- 只 grep `Missing textures in model` 判「模型修好了」 —— 见第 4 节。

---

## 7. 变更记录：2026-10-30 清理与搁置

- 工程目录腾空间：`work/run26` **143.80 GB → 5.36 GB**（删掉 131 个 `port/g<数字>` 轮次脚手架 137.91 GB +
  `mods-aero`/`mods-full`/`node_modules`）；整个工程 146.21 → **7.69 GB**；C: 可用 153.6 → 221.3 GB。
  逐项清单与保留理由见 [cleanup-2026-10-30.md](cleanup-2026-10-30.md)。
- **保留**：交付件 `mods-stable`(118 jar)、用户世界 `watch`、手改 jar 回滚 `backups`、`server26`、
  `mcptools`、**未 promote 候选 `candidates-2026-10-22/`**、`port/` 里非 `g*` 的上游原包与自写 stub 源码、`work/refs/mc26.3`。
- 仓库同步：本次把 2026-10-22 审计轮的全部文档/工具（含 `tools/audit_models.py`、`tools/visual-audit/`）与
  `docs/DELIVERED-JARS.md`、本文件一并推送到 `main`。
- 项目暂**搁置**；恢复从第 2 节开始，验收口径从第 4 节开始。
