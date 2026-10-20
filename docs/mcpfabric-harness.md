# mcpfabric 接入（开发验证用，不进交付）

> 2026-10-20 接入。仓库：https://github.com/denfry/mcpfabric（原 Etoryx/mcpfabric 已迁移，Modrinth: eA63YgUh）

## 是什么

Minecraft 侧的「AI 控制」模组 + MCP server：游戏内起 HTTP bridge（默认 `127.0.0.1:25599`，Bearer token），暴露 50+ 工具（读世界/写世界/命令/玩家管理/客户端控制/交互/背包/容器/合成/UI/截图/导航/事件）。

- **官方支持 26.3 Fabric**：`mcpfabric-0.8.0+26.3.jar`（248 KB）
- 二进制放 `work/run26/mcptools/mcpfabric-0.8.0+26.3.jar`
- TS MCP server 已构建：`work/run26/mcptools/mcpfabric-main/mcp-server/dist/index.js`
- 本项目用**薄 CLI** 直连 bridge（不接 DSH MCP，省一次重启）：`tools/mcpfabric_client.mjs`

## 用法

```powershell
# 1) 起测试局（mods-mcp = live 114 + mcpfabric）
python tools\launch26\launch.py --game-dir work\run26\port\g33\game-<tag> `
  --mods work\run26\port\g76\stage\mods-mcp --timeout 900

# 2) 等 bridge 起来（配置文件由模组首次运行生成）
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-<tag> info
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-<tag> call screen.get
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-<tag> call session.worlds
node tools\mcpfabric_client.mjs --game work\run26\port\g33\game-<tag> call session.join '{"worldId":"sp:lm-final"}'
```

`config/mcpfabric.config.json` 自动生成 host/port/token；**`enableUiControl` 默认 false，需要 UI 点击时改成 true 并重开一局**。

## 对验证的价值（实测）

| 能力 | 用途 |
|---|---|
| `ui.widgets` / `ui.click` / `ui.setText` | **GUI 点击**：任务书章节/翻页/提交按钮、机器界面（探针原先完全做不了） |
| `control.startUsing` / `stopUsing` | **真实按住右键**：吃东西（实测 saturation 5→7.4）、使用物品 |
| `container.open/state/click/transfer/close` | 容器/机器输入输出（basin、depot、熔炉…） |
| `inventory.selectHotbar` / `swapSlots` | 切换手持（放门/牌匾等需要手持物品） |
| `command.run` | 任意命令 + **输出捕获** |
| `vision.screenshot` | PNG 截图（1280×720） |
| `session.worlds/join`、`nav.pathTo` | 程序化进世界、A* 导航 |
| `player.getState` | health/food/saturation/pos/usingItem 等 |

## 纪律

- **只用于开发验证**：`mods-mcp` staging 存在，但 `mods-stable`（交付 114 jar）**绝不加** mcpfabric。
- bridge 仅 loopback + token；`enableUiControl` 只在验证局打开。
- 与 `sky262-mcp`（WS 25576）并存不冲突：前者强在 GUI/容器/真实输入，后者强在方块读写与自研方法。