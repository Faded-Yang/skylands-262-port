# 参考资料索引（refs-index，2026-10-21 更新）

用户新提供的参考内容安装位置与用途。所有内容只作**参考/取证**，不直接进交付。

## 1. 参考 jar（`work/refs/jars/`）
| 文件 | 内容 | 用途 |
|---|---|---|
| `create-fabric-6.0.8.1+build.1744-mc1.20.1.jar` | 官方 Fabric 版 Create 6.0.8.1（1.20.1），内嵌 22 个库 jar（Flywheel/Ponder/Registrate/Registrate 生态） | Create 行为/数据/资源对照；内嵌库可用于补我们的 shim 缺失 |
| `create-aeronautics-bundled-1.21.1-1.3.2.jar` | Aeronautics 1.3.2 整合包（NeoForge 1.21.1），内嵌 `aeronautics` / `simulated` / `offroad` 三个 jar | 1.21.1 行为/数据对照；**配方/loot/advancements 数据补全来源** |

解包目录：`work/refs/jars/extracted/create-fabric-nested/`、`work/refs/jars/extracted/aeronautics-bundled/`。

## 2. 参考源码仓库（`work/refs/repos/`，经 codeload 下载）
| 目录 | 来源 | 用途 |
|---|---|---|
| `fabric-docs` | https://github.com/FabricMC/fabric-docs | Fabric 26.x 开发文档（事件/渲染/数据） |
| `neoforged-documentation` | https://github.com/neoforged/documentation | NeoForge 文档（对比 API 语义） |
| `fabricators-create-old` | https://github.com/Fabricators-of-Create/Create-Fabric-Old | **Fabric 版 Create 源码**（主仓库 `Fabricators-of-Create/Create` codeload 404，用 Old 仓库替代） |
| `create-wiki` | https://github.com/Creators-of-Create/wiki | Create 玩法/机制 wiki |
| `yan-mc-mod-dev` | https://github.com/yan-mc/minecraft-mod-dev | 26.x mod 开发参考 |

> 注：`github.com` git 协议在本机不可达；统一走 `codeload.github.com/<owner>/<repo>/zip/refs/heads/<branch>`（脚本 `tools/fetch_refs.py`）。

## 3. 已做的对照结论（2026-10-21）

### 3.1 API 正确性（重构建审计）
- `tools/scan_icce.py`：Methodref/InterfaceMethodref 与 owner 实际类型不匹配扫描（117 jar / 32016 class）：仅 **2 处 latent**（create-fly `ConfigPlacementFilter` / `LayeredOreFeature` 里对 26.3 interface 的 `<init>` 死引用），无其它 ICCE 隐患；
- `tools/scan_super.py`：superclass 实际是 interface / implements 实际是 class 的扫描：**0 处**；
- 已修的真实 ICCE：create-fly 移植注入的 80 处 `InterfaceMethodref`→`Methodref`（ContainerBridge，30 类，1.0.5）。

### 3.2 数据完整性（对照参考 jar）
| 模组 | live recipes | 参考 recipes | live loot | 参考 loot | live advancements | 参考 advancements |
|---|---:|---:|---:|---:|---:|---:|
| aeronautics + simulated（合并件） | **0** | 45 + 73 | **0** | 40 + 94 | **0** | 35 + 96 |
| offroad | **0** | 7 | 3 | 3 | **0** | 7 |
| create（数据在 `sky262-create-recipes` 独立件） | 1607 | 1814 | 632 | — | 0 | — |

⇒ **aeronautics/simulated/offroad 的配方、loot、进度全部缺失**（这些机器/物品目前无法合成）→ 已派 `docs/fix-aero-recipes.md` 任务从参考 jar 转换补全。

## 4. 使用纪律
- 只从参考件**抽数据/行为对照**，不直接把 1.20.1/1.21.1 的 class 拷进 26.3（版本 API 不同）；
- 数据转换以 live `sky262-create-recipes` 内同类配方为 26.3 schema 权威样例；
- 参考仓库只读；构建脚本产物写 `port/gN`。