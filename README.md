# skylands-262 · MC 26.3 + Fabric 移植工程笔记与工具

> 把一个以 **Create / Create: Aeronautics** 为核心的 110 mod 整合包，从 Minecraft 1.21.1 / 1.20.1 时代整体移植到 **Minecraft 26.3 + Fabric** 的工程记录。
> 本仓库只包含 **我们自己写的文档、工具与代码**，不含任何游戏资源、也不含任何原 mod 的代码或 jar。

---

## 中文

### 这是什么

Minecraft 26.3 是一次「破坏性」更新：官方从 26.x 起直接发布未混淆的 jar，Fabric 生态的映射、渲染、世界生成、注册表 API 几乎全部重写。上游 Create 系模组（Create、Aeronautics、Sable、DragonsPlus、Enchantment Industry ……）大多没有 26.3 构建，且原整合包大量 mod 只有 NeoForge 或 1.20.1 版本。

这个仓库记录了我们逐个把整合包字段、API、数据格式从旧版本迁移到 26.3 的完整过程：

- 110 个 mod 的可用性调查与补齐（自研移植 / 源码级重建 / 降级注册）；
- 26.3 的 API 地雷清单（渲染两段式、注册表、BlockState、Item 模型、GUI、网络、世界生成 ……）；
- 可直接复用的工具链（反编译、jar 打包、启动器、MCP 游戏内客户端）；
- 我们自研 mod 的源码：任务系统、喷气背包、便携结构打印机、若干装饰/功能方块包；
- 我们移植并适配到 26.3 的 MIT 许可 minecraft-mcp 客户端 mod 源码。

最终交付形态是一个能启动、能建世界、能玩的 26.3 整合包（交付件 93 个 jar / 170+ mod 项），细节见 docs/DELIVERY.md。

### 目录

- docs/     移植工程笔记：硬规则、API 地雷、交付说明、各 mod 的移植记录
- tools/    工具：反编译、可复现打包、启动器、MCP 客户端、语言审计
- src/      minecraft-mcp 客户端 mod 的 26.3 适配源码（上游 MIT）
- examples/ 自研 mod 源码（任务系统）与启动脚本示例

### 值得看的几篇

- docs/HARD-RULES.md —— 移植硬规则与验证纪律（为什么「编译过 ≠ 能跑」）
- docs/api-landmines.md —— 26.3 API 地雷清单（按类名可搜）
- docs/DELIVERY.md —— 交付说明：装了什么、每个 mod 降级了什么
- docs/LEDGER-FULL.md —— 完整工程台账（含失败尝试与原因）
- docs/port-*.md —— 各 mod 的逐项移植记录
- docs/mcp-fabric-mod.md —— 用 MCP 在游戏内截图/控制客户端做验收

### 工具

- tools/decompile.py —— 用 Vineflower 反编译 jar 到源码树
- tools/pack_jar.py —— 可复现打包（自动写目录条目，避免资源不被加载）
- tools/launch26/launch.py —— 26.3 启动器（标题/进世界自动化、超时抓线程栈）
- tools/mcp_fabric_client.mjs —— 连接游戏内 MCP（截图/玩家状态/放置方块）
- tools/diff_pack.py / lang_audit.py —— 依赖清点、汉化审计

### 法律与边界

- 本仓库不包含 Minecraft 客户端/服务端、游戏资源，也不包含任何原 mod 的 jar 或反编译代码；
- 文档中提到的类名/方法名属于各自项目，仅用于技术说明；
- 若要复现整合包，需要自行合法获取相应 mod；
- 代码部分（tools/、examples/、src/ 中我们写的部分）以 MIT 授权；docs/ 以 CC BY 4.0 授权；
- src/mcp-fabric-mod 源自 InventivetalentDev/minecraft-mcp（MIT），我们做了 26.3 适配，原始版权归其作者。

---

## English

### What is this

Minecraft 26.3 is a breaking release: Mojang now ships unobfuscated jars, and Fabric's mappings, rendering, worldgen and registry APIs were largely rewritten. Most Create-family mods have no 26.3 build, and many mods in the original pack only exist for NeoForge or 1.20.1.

This repository documents the full engineering effort of migrating the pack field-by-field and API-by-API:

- availability survey and gap-filling for 110 mods (source ports, rebuilds, reduced-scope registrations);
- a 26.3 API landmine catalogue (two-phase rendering, registries, block/item model entrypoints, GUI, networking, worldgen, …);
- reusable tooling (decompilation, deterministic jar packing, automated launcher, in-game MCP client);
- sources of our own mods: quest system, jetpack, portable structure printer, decorative/functional block packs;
- our 26.3 adaptation of the MIT-licensed minecraft-mcp client mod.

The end result is a bootable, playable 26.3 Fabric pack (93 jars / 170+ mod entries). See docs/DELIVERY.md.

### Legal

- No Minecraft assets, no original mod jars and no decompiled mod code are included;
- Class/method names in docs belong to their respective projects and are used for technical explanation only;
- To reproduce the pack you must obtain the mods legally yourself;
- Our code (tools/, examples/, our part of src/) is MIT; docs/ is CC BY 4.0;
- src/mcp-fabric-mod derives from InventivetalentDev/minecraft-mcp (MIT), adapted for 26.3.

---

## Credits

- Create (and the fork used for 26.3), InventivetalentDev/minecraft-mcp, Vineflower, Fabric, and every mod author whose work this pack builds upon.
- 移植过程中的所有实验、失败与结论都记录在 docs/LEDGER-FULL.md。