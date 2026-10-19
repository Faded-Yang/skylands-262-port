# Skylands 262 —— MC 26.3 整合包移植

在原「Create 航空学 × 浮空群岛」（MC 1.21.1 / NeoForge）基础上，把 **110 个 mod** 迁移到 **Minecraft 26.3 + Fabric** 的移植工程。
当前：**99 jar / 移植覆盖 99-of-110 / 汉化 100%**，标题与进入世界均实测通过。

## 环境要求

| 组件 | 版本 |
|---|---|
| Minecraft | **26.3** |
| Fabric Loader | **0.19.5** |
| Java | **25** |
| 内存建议 | 6 GB+（含 Create 系与浮空岛世界） |

## 交付物

目录 `work/run26/mods-stable`：**99 个 jar**，分类概览：

- **平台/依赖**：Fabric API、Architectury、Cloth Config、Balm、YungsApi、Paxi、Lithostitched、Kotlin for Forge 等；
- **Create 系**：create-fly（核心）、aeronautics、sable、createdeco（389 方块）、Design-n-Decor（774 方块）、柴油发电机、动力装载器、机械挤出机、Slice and Dice、中央厨房、toolgun、transmission linkage 等；
- **食物/农业**：Farmer's Delight refabricated、chefsdelight、corndelight、ends_delight、cultural/miners/my nethers（reduced）等；
- **世界生成**：natures_spirit（153 群系全套数据）、No Void Structures（结构虚空保护）、MoogsSoaringStructures；
- **系统/界**：sky262-quests（任务书 1.6.0）、sky262-mcp（游戏内 MCP 服务端）、JEI/创造栏相关等。

## 启动方式

1. 使用 **Fabric Loader 0.19.5 + Java 25** 启动 Minecraft **26.3** 实例；
2. 把 `work/run26/mods-stable/*.jar` 放入实例 `mods/`；
3. 双击仓库脚本 **`启动浮岛世界.bat`**（会先把 live 同步到 `watch/mods`，再启动游戏实例）；
4. 进入世界后可按 **J** 打开任务书；`/locate biome natures_spirit:redwood_forest` 可定位 NS 红杉林。

## 可选：游戏内 MCP 验证

`sky262-mcp` 随包提供（WebSocket 25576）+ `tools/mcp_fabric_client.mjs`，可用于自动化验收：

- `node tools/mcp_fabric_client.mjs player.getState`
- `node tools/mcp_fabric_client.mjs world.getBlock '{"x":0,"y":70,"z":0}'`
- `node tools/mcp_fabric_client.mjs chat.send '{"message":"/locate biome natures_spirit:redwood_forest"}'`
- `node tools/mcp_fabric_client.mjs screenshot.take '{"out":"shot.png"}'`

## 文档

| 文档 | 内容 |
|---|---|
| `docs/DELIVERY.md` | 交付清单、覆盖统计、逐件状态 |
| `docs/RELEASE-NOTES.md` | 本轮收口清单（每条有 MCP 实测证据） |
| `docs/KNOWN-LIMITATIONS.md` | 已知降级（按模块分组） |
| `docs/GUIDE-reproduce.md` | 复现构建流程 |
| `docs/API-263-data-schema.md` | 26.3 数据包/资源 schema 差异与转换要点 |
| `docs/api-landmines.md` | 26.3 API 地雷清单 |

## 许可与来源

- **代码**：MIT；**文档**：CC BY 4.0。
- 各上游 mod 版权归原作者所有，本仓库仅提供 26.3 兼容移植与构建脚本；
- `tools/mcp-fabric-mod` 来自上游 MIT 项目（游戏内 MCP 桥）。
- 若你是上游作者并希望移除相关内容，请提 issue。