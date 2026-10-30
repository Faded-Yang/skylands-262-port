# fix-clipboardscreen-npe —— create-fly ClipboardScreen send() content null

> 参考 docs/api-landmines.md（ClipboardManager 签名）、docs/fix-ponder-crash.md（剪贴板相关地雷）；本补丁只改目标 class。

## 现象
- crash-2026-10-21_03.15.56-client.txt：
  NPE: ClipboardContent.setPages(...) because this.content is null
  at ClipboardScreen.send(ClipboardScreen.java:379)
  at ClipboardScreen.removed(ClipboardScreen.java:366)
  at ClipboardScreen.tick(ClipboardScreen.java:164)
- 触发：剪贴板 GUI 在 screen 栈上但 content 尚未初始化，removed()/tick 仍走 send()。

## 修法
- 在 ClipboardScreen.send() 开头插入：
  if (this.content == null) return;
- 一处守卫覆盖 removed()/sendIfEditingBlock() 两个调用方；不改变非 null 路径。
- 只改目标 class：com/zurrtum/create/client/content/equipment/clipboard/ClipboardScreen.class；无 helper、无新增 entry。

## 件
- 基件：live create-fly-26.2-6.0.9-2-26.3-patched.jar，SHA-256 2290891b6c699feaefacb01cc0ab0508baa60a995c83f4b75c7ceb8460963a80。
- 新件：work/run26/port/g70/out/create-fly-26.2-6.0.9-2-26.3-clipfix.jar
  - 19,650,947 B，SHA-256 310e6e0a61f2a6bcf1d7fb832e5360bc8e3de486188f33bc3f3bea78c2f41250。
- entry diff：changed 1（ClipboardScreen.class）；added 0；removed 0；其余逐字节不变。
- staging：work/run26/port/g70/stage/create-fly-clipfix（live 116，替换 create-fly；116）。

## 静态验证
- ASM 在 send() 入口插入 content null 检查；javap 确认 ifnonnull 8; return；
- -Xverify:all 加载 patched ClipboardScreen：OK；
- 未启游戏；probe 需反复打开/关闭剪贴板 + blocks 扫到 224 段复扫验证 0 crash。
