# sky262-mcp（游戏内 MCP 桥）使用说明

上游：`InventivetalentDev/minecraft-mcp`（MIT）Fabric client mod，26.3 适配版。
当前验证件：`g90/out/sky262-mcp-0.1.0.jar`（serve 端 cb41b808 已验证 `player.getState`/`screenshot.take`；另有别名件 ec7a37d2）。

## 启动

- 放到客户端 `mods/`，启动游戏（client-only）；日志出现：
  `[MCP] WebSocket server started on 127.0.0.1:25576` / `[MCP] WebSocket server ready on port 25576`。
- 首次启动会把默认 `mcp.json` 写到游戏 `config/`。

## 客户端

`tools/mcp_fabric_client.mjs`（Node）：

```bash
node tools/mcp_fabric_client.mjs player.getState
node tools/mcp_fabric_client.mjs screenshot.take --out shot.png
```

协议：WebSocket `ws://127.0.0.1:25576`，JSON-RPC 风格 `{id, method, params}`。

## 方法名清单（jar 内 RequestHandler switch 的原始字符串）

| 方法 | 说明 |
|---|---|
| `chat.get` | 取聊天记录 |
| `chat.send` | 发送聊天；参数 `{"message":"..."}`（不是 `text`） |
| `player.getState` | 玩家位置/朝向/维度/血量等 |
| `player.moveTo` | 传送/移动 |
| `player.lookAt` | 看向坐标 |
| `player.jump` | 跳跃 |
| `player.breakBlock` | 破坏方块 |
| `player.placeBlock` | 放置方块 |
| `player.interact` | 交互 |
| `world.getBlock` | 读取方块 |
| `world.nearbyEntities` | 附近实体 |
| `screenshot.take` | 返回 base64 PNG |
| `reflect.invoke` / `reflect.getField` / `reflect.setField` / `reflect.newInstance` | 反射 |
| `class.info` | 类信息 |
| `vars.get` / `vars.list` / `vars.delete` / `vars.clear` | 对象注册表变量 |

> 注意：**README 的 snake_case 不是实际方法名**；probe 曾按 `get_player_state`/`take_screenshot` 调用得到 `Unknown method`。ec7a37d2 追加了这些 snake_case 别名，但已验证件 cb41b808 只认上表原名。

## 已知构建要点

- 不要依赖 `fabric.mod.json` 的 `jars` JIJ：client entrypoint 执行时嵌套 jar 未上 classpath ⇒ `NoClassDefFoundError org/java_websocket/server/WebSocketServer`；应把 Java-WebSocket 的 `org/java_websocket/**` 直接 shade 进主 jar。
- 26.3 Screenshot：`Screenshot.takeScreenshot(client.gameRenderer.mainRenderTarget(), consumer)`（无 `getMainRenderTarget()`）。
