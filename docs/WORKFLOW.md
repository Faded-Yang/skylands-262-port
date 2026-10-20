# 新的开发/验证工作流（2026-10-20 起）

> 核心变化：**用 mcpfabric（游戏内 MCP）替代自研 sky262-mcp**，并把「静态审计 + 全量动态 sweep + GUI 点击」变成可重复的脚本。

## 1. 验证环境（dev-only，不进交付）

| 项 | 位置 |
|---|---|
| mcpfabric jar（26.3 Fabric） | `work/run26/mcptools/mcpfabric-0.8.0+26.3.jar` |
| 验证用 mods 目录（live 113 + mcpfabric = 114） | `work/run26/port/g76/stage/mods-mcp` |
| 验证用游戏目录（含存档、enableUiControl=true） | `work/run26/port/g33/game-mcpfab` |
| CLI 客户端 | `tools/mcpfabric_client.mjs` |
| 说明 | `docs/mcpfabric-harness.md` |

起局：

```powershell
python tools\launch26\launch.py --game-dir work\run26\port\g33\game-mcpfab `
  --mods work\run26\port\g76\stage\mods-mcp --timeout 1200
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-mcpfab call screen.get
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-mcpfab call session.join '{"worldId":"sp:lm-final"}'
```

## 2. 全量动态审计（新）

```powershell
# 方块：逐个 setblock，检查未注册/崩溃
node tools\sweep_blocks.mjs --game <gameDir>          # 4212 blockstates → 4187 ok / 25 unknown / 0 crash（清理后 4187/0/0）

# 物品：逐个 give，检查未注册 + 中文名 + raw key
node tools\sweep_items.mjs --game <gameDir>           # 4811 items → 4630 ok / 71 unknown / 110 rawkey（修复中）

# 数据引用完整性（静态）
python tools\audit_data_refs.py                    # 0 block/tag 缺失；item 缺失 4（已清理）
```

输出 JSON 在 `work/run26/port/g29/{sweep_blocks,sweep_items}.json`。

## 3. 功能链路验证（mcpfabric 能力）

| 场景 | 用法 |
|---|---|
| GUI 点击（任务书/机器界面） | `ui.widgets` 列控件 → `ui.click {id}`；模组 screen 允许，只列真 widget |
| 真实按住右键（吃/使用） | `control.startUsing` → 等待 → `control.stopUsing` → `player.getState` 看 food/saturation |
| 机器/容器输入输出 | `container.open` → `container.state/transfer` |
| 换手持/放方块 | `inventory.selectHotbar` → `interact.placeBlock` |
| 命令 + 输出 | `command.run {command:"..."}`（返回 output 数组） |
| 截图 | `vision.screenshot`（PNG 1280×720） |

## 4. 修复 → 验证 → 合并

1. lane 负责人出 staging（**必须以当前 live 为底**，逐 jar 报 diff/SHA）；
2. 合并候选 staging 由 Lead 组（overlay + 冲突合并），交 probe 用 mcpfabric 验；
3. probe 判据：`sweep_blocks`/`sweep_items` 数字改善 + 功能 PASS + 0 crash；
4. Lead promote：`sha(live) == 候选 base`、断言 distinct mod id == jar 数、跑标题回归；
5. 更新 `docs/USER-FEEDBACK-R1.md` / `docs/LEDGER-FULL.md` / GitHub 仓。

## 5. 其它已装 MCP（新会话生效）

| MCP | 用途 |
|---|---|
| `mcpfabric`（游戏内） | 见上 |
| `mcmodding` | Fabric/NeoForge 官方文档语义检索（26.3 API / 移植写法） |
| `modrinth` | 按 MC 版本 + loader 检索 mod 版本/文件 |
| `github` | 仓库读写（文档/工具推送） |

> 注：`~~sky262-mcp~~` 与 `tools/mcp_fabric_client.mjs` 已删除（被 mcpfabric 取代），交付从 114 → **113 jar**。