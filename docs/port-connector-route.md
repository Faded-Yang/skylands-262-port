# port-connector-route —— Sinytra Connector 可行性：**不可行（方向相反）**

> 日期：2026-10-19 ｜ 实验目录 `work/run26/port/g69/` ｜ 结论：Connector 是「在 NeoForge 上跑 Fabric mod」，不能把 NeoForge mod 加载到 Fabric。

## 1. 实验（1 次标题启动）

- staging：`g69/stage/connector-test` = live 74 jar + `connector-3.1.0-beta.3+26.2-full.jar`（Modrinth CDN 下载，sha512 校验 OK）+ `sophisticatedbackpacks-26.3-3.26.13.2209.jar`（Modrinth NeoForge 26.3 构建）。
- 启动：`launch.py --game-dir g69/game-connector-test --mods … --watch-title` ⇒ **TITLE_SCREEN_OK 27.2s，0 crash**。
- 关键日志：
  `[main/WARN]: Found 2 non-fabric mods:`
  `\t- connector-3.1.0-beta.3+26.2-full.jar`
  `\t- sophisticatedbackpacks-26.3-3.26.13.2209.jar`
  且 `Loading 155 mods:`（与 live 74 基线相同数量）⇒ **两个 jar 被 Fabric Loader 直接忽略**，没有加载、没有注册。
- 证据：`g69/out/evidence/connector-test-title.log`。

## 2. 为什么（元数据）

- Connector jar 内**没有 `fabric.mod.json`**，只有 `META-INF/neoforge.mods.toml`：`modLoader=javafml`，depends `neoforge [26.2,26.3)`、`minecraft [26.2,26.3)`；
  description 原文：**allows running Fabric mods on NeoForge**；Modrinth project `connector` 的 loader 也是 `neoforge`。
  ⇒ 它是「NeoForge 侧兼容层」，把 **Fabric mod 跑在 NeoForge** 上 —— 与我们的目标（NeoForge mod 跑在 Fabric 26.3）**方向相反**。
- `sophisticatedbackpacks-26.3-3.26.13.2209.jar` 同样无 fabric.mod.json，`neoforge.mods.toml` depends `neoforge [26.3.0.47-beta,26.4)` ⇒ Fabric 同样忽略。

## 3. 反向方案调研（NeoForge→Fabric）

- 网上出现过 **「Sporran (NeoForge to Fabric Translator)」**（modpackindex 209440），但：Modrinth 搜索无此项目、modpackindex 页面被 Cloudflare 拦截，**无法验证/下载**；不纳入方案。
- 结论：**不存在可用的工业级「NeoForge mod → Fabric」翻译层**。

## 4. 路线结论

1. **Connector 路线作废**：不是「等 26.3 版」的问题，而是加载方向不对；`mods-stable` 也**不能**放这些 NeoForge jar（会被忽略，无收益）。
2. 缺的 mod 仍按既有结论走：**26.x Fabric 构建（5 个）→ 放宽版本试装；其余重写或用 Python/资源层替代**。
3. `sophisticatedbackpacks/core/storage` 虽有 NeoForge 26.3 构建，但 Fabric 下无法加载；只能走「重写」路线（Tier C 大件）。
