# Nixie Tube 右键服务端崩溃修复（R-nixie）

> 证据：`game-g148` blocks 224→1000 扫到 ~371 时 `crash-2026-10-21_03.31.17-server.txt`：`NoSuchMethodError: CommandSourceStack.<init>(CommandSource, Vec3, Vec2, ServerLevel, ...)`。

## 根因

- `DynamicComponent.getCommandSource` 仍用 1.21 的 9 参构造：`(CommandSource, Vec3, Vec2, ServerLevel, LevelBasedPermissionSet, String name, Component displayName, MinecraftServer, Entity)`；
- 26.3 该构造已删，公开构造改为 7 参：`(CommandSource, Vec3, Vec2, ServerLevel, PermissionSet, Component, MinecraftServer)`；
- 右键 Nixie Tube 触发 `NixieTubeBlock.useItemOn` → `displayCustomText` → `DynamicComponent.parseCustomText` → 构造 → NoSuchMethodError（服务端 tick 崩溃）。

## 修复

`DynamicComponent.getCommandSource` 改为 26.3 7 参构造：

```java
new CommandSourceStack(CommandSource.NULL, Vec3.atCenterOf(pos), Vec2.ZERO, level,
    LevelBasedPermissionSet.GAMEMASTER, Component.literal("create"), level.getServer());
```

只替换 `DynamicComponent.class`；同时保留 ClipboardScreen 判空补丁（同一 jar）。

## 候选

| 项 | 值 |
|---|---|
| 文件 | `g153/stage-final/mods-candidate/create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 改动 | `DynamicComponent.class` + `ClipboardScreen.class`（clip 判空，ASM 保留 frames） |
| SHA-256 | `f574ae39944ab426d481cbd973b87205d0dca2d464776fdf28192f34d43625d9` |
| staging | `g153/stage-final/mods-candidate`（116 jar，create-fly 同名替换） |

## 验证

- `javap` 确认调用 7 参构造；
- 右键 Nixie Tube（任意手持物品，含剪贴板）：服务端不再抛 NoSuchMethodError，世界不崩；
- clipboard 打开/关闭仍正常；blocks 224→1000 续扫。
