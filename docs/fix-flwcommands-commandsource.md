# fix-flwcommands-commandsource —— FlwCommands 旧 CommandSourceStack 9 参

> 同类 P1 latent：create-fly client/flywheel/impl/FlwCommands#lambda$createDebugCommand$0。
> 参考 docs/fix-dynamiccomponent-commandsource.md、work/refs/mc26.3/net/minecraft/commands/CommandSourceStack.java:69（26.3 7 参构造）。

## 现象
- FlwCommands 的 flywheel/debug 命令 lambda 里仍用旧 9 参 CommandSourceStack 构造：
  source,pos,rotation,level,permission,String name,Component displayName,server,entity。
- 普通方块交互不触发；仅调用该 debug 命令时会 NoSuchMethodError。

## 修法
- ASM 只改 FlwCommands.lambda$createDebugCommand$0：
  - 删除 String name 与 Component displayName 两个 null 实参（第 3/4 个 null）；
  - 构造描述符改 26.3 7 参：source,pos,rotation,level,permission,server,entity。
- COMPUTE_FRAMES | COMPUTE_MAXS 重算 StackMapTable。
- 只改目标 class：com/zurrtum/create/client/flywheel/impl/FlwCommands.class；无 helper、无新增 entry。

## 件
- 基件：live create-fly-26.2-6.0.9-2-26.3-patched.jar，SHA-256 e78bcc123d3b838b535060ce5272ef00f03254ee24ed53909452ba76671c3aa4（19,677,598 B）。
- 新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-flwfix.jar
  - 19,677,559 B，SHA-256 a9a8101df790479178490b9bd8c4fe59a064d31413f36950d0ff64a6c7197e7d。
- entry diff：changed 1（FlwCommands.class）；added 0；removed 0；其余逐字节不变。
- staging：work/run26/port/g70/stage/create-fly-flwfix（live 116，替换 create-fly；116）。

## 验证
- -Xverify:all 加载 patched FlwCommands：OK；
- 扫描 patched jar：FlwCommands 与 DynamicComponent 均为 7 参，全 jar 无旧 9 参 CommandSourceStack 构造；
- 未启游戏；debug 命令可后续抽验。
