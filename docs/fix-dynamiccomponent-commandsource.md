# fix-dynamiccomponent-commandsource —— Nixie Tube 右键 NoSuchMethodError

> 参考 docs/API-1.21.11.md（CommandSourceStack/API 迁移）、work/refs/mc26.3/net/minecraft/commands/CommandSourceStack.java:69（26.3 7 参构造）、work/refs/create-fly/.../DynamicComponent.java。

## 现象
- g33/game-v102/crash-2026-10-21_03.31.17-server.txt：
  NoSuchMethodError: CommandSourceStack.<init>(CommandSource, Vec3, Vec2, ServerLevel, ...)
  at DynamicComponent.getCommandSource(DynamicComponent.java:42)
  at NixieTubeBlockEntity.displayCustomText:165 <- NixieTubeBlock.useItemOn:118
- 旧 9 参：source,pos,rotation,level,permission,String name,Component displayName,server,entity；
- 26.3 7 参：source,pos,rotation,level,permission,server,entity（name/Component 两参已删）。

## 修法
- ASM 只改 DynamicComponent.getCommandSource：
  - 删除参数 String "create"、Component.literal("create")（以及对应两次 LDC/Component.literal 指令）；
  - 构造描述符改为 7 参。
- COMPUTE_FRAMES | COMPUTE_MAXS 重算 StackMapTable（上次 clipfix 无 frames 的教训）。
- 只改目标 class：com/zurrtum/create/foundation/utility/DynamicComponent.class；无 helper、无新增 entry。

## 件
- 基件：live create-fly-26.2-6.0.9-2-26.3-patched.jar，SHA-256 2290891b6c699feaefacb01cc0ab0508baa60a995c83f4b75c7ceb8460963a80。
- 新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-dynfix.jar
  - 19,650,888 B，SHA-256 afe9e8b5b898843941121189890f7e4b3ae3c2f9091e340f94b7b1e437904f15。
- entry diff：changed 1（DynamicComponent.class）；added 0；removed 0。
- staging：work/run26/port/g70/stage/create-fly-dynfix（live 116，替换 create-fly；116）。

## 静态验证
- javap patched getCommandSource：无旧 9 参描述符，7 参描述符存在；
- -Xverify:all 加载 patched DynamicComponent：OK（frames 已重算）；
- 未启游戏；probe 验 Nixie Tube 右键 0 crash。

## 同类静态扫描（create-fly 全 jar）
用 ASM 扫描所有 CommandSourceStack.<init> 调用：
1. com/zurrtum/create/foundation/utility/DynamicComponent#getCommandSource -> 旧 9 参（本补丁已修）。
2. com/zurrtum/create/client/flywheel/impl/FlwCommands#lambda$createDebugCommand$0 -> 旧 9 参（未修）。
   - 源码 work/refs/create-fly/.../FlwCommands.java 用 new CommandSourceStack(null,...,null) 调 Coordinates.getBlockPos；
   - 触发面：flywheel/debug 命令（非普通方块交互），但仍是同类 NoSuchMethodError，P1 latent；
   - 若需要同法删除 name/Component 两参并改 7 参，我可再出一个小件。
其余 create-fly 类无 CommandSourceStack.<init> 调用。
