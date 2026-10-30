# 全 mod 重构计划与第一轮结果（refactor-100，2026-10-21）

> 背景：用户提供新参考（Fabric/NeoForge 文档、官方 Create Fabric 1.20.1 jar、Aeronautics 1.21.1 bundled jar、Create 源码/wiki），
> 并要求「全 mod 重构一次，现版本问题还是太多」。

## 0. 参考安装（见 `docs/refs-index.md`）
- `work/refs/jars/`：`create-fabric-6.0.8.1+build.1744-mc1.20.1.jar`（内嵌 22 库 jar，含 Flywheel/Ponder/Registrate）、`create-aeronautics-bundled-1.21.1-1.3.2.jar`（内嵌 aeronautics 1.3.2 / simulated / offroad）；
- `work/refs/repos/`：fabric-docs、neoforged-documentation、create-wiki、yan-mc-mod-dev、**fabricators-create-old**（Create Fabric 源码，`Fabricators-of-Create/Create` 主库 codeload 404，用 `Create-Fabric-Old` 替代）。

## 1. 第一轮：API 正确性全量审计（自动，已出结果）
新增工具：
- `tools/scan_icce.py`：常量池 Methodref/InterfaceMethodref 与 owner 实际类型不匹配（117 jar / 32016 class）；
- `tools/scan_super.py`：superclass 是 interface / implements 是 class。

结果：
- ICCE 隐患：**仅 2 处 latent**（create-fly `ConfigPlacementFilter` / `LayeredOreFeature` 对 26.3 interface 的死引用，未在启动路径）；
- superclass/interface 错配：**0 处**；
- 已修的真实 ICCE：create-fly 80 处容器桥常量池 tag 错误（ContainerBridge，30 类，1.0.5），这是「Create 机器一点就崩」主因。

⇒ 结论：**API 层不再有大面积系统性错误**；剩下的是「数据缺失」+「行为差异」。

## 2. 第二轮：数据完整性（正在做）
对照参考 jar：
| 模组 | 现有 recipes | 参考 | loot | 参考 | advancements | 参考 |
|---|---:|---:|---:|---:|---:|---:|
| aeronautics+simulated | 0 | 45+73 | 0 | 40+94 | 0 | 35+96 |
| offroad | 0 | 7 | 3 | 3 | 0 | 7 |
| create（独立 data 件） | 1607 | 1814 | 632 | — | 0 | — |

已产出：`sky262-aero-recipes-1.0.0.jar`（`39ca9ff6`，124 条配方 + offroad 7 advancements，静态 0 missing）→ staging `g76/stage/g170-aero-rec` 待真机验证（等用户客户端退出）。
进行中：aero/simulated/offroad 的 loot + advancements 转换。

## 3. 第三轮（计划）：行为/内容复刻
- 用 `fabricators-create-old` 源码 + create-fabric 1.20.1 jar 对照，复查移植中「有空实现/简化」的机器行为（belt/saw/crafter/deployer/controls 等）；
- 用 fabric-docs / neoforged-documentation 校正 26.3 API 语义（渲染/事件/数据组件）；
- 每次改动走既有测试台（blocks 4187 / 机器矩阵 / 世界加载 / 图标）回归。

## 4. 验收门槛（每轮）
1. 启动：5 类日志错误 = 0；2. 世界加载：registry=0、0 crash；3. 机器矩阵：对应链路 PASS；4. 目标内容可获取（配方/JEI）；5. 截图留档。
