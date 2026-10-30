# sweep-blocks-gui-patch —— 右键扫方块时关闭 GUI

> 对象：work/run26/port/g33/lab/test_blocks_use_fix.mjs（右键交互扫）；不是 tools/sweep_blocks.mjs（后者只 setblock，不右键，无 screen 问题）。
> clipfix ASM 版已弃用（probe VerifyError），改由 aero 完整重编译 d8db812c 路线；本 patch 只改扫描脚本。

## 问题
原脚本每个方块：
1. setblock；
2. tp 到旁边；
3. interact.useItem（右键）；
4. world.getBlock。

它从不检查 screen。会打开 GUI 的方块（剪贴板、文件夹、蓝图、Ponder、容器等）把 Screen 留在栈上，下一次 setblock/tp/useItem 实际作用在旧 Screen 上；ClipboardScreen 的 removed()/tick() 在 content 未初始化时触发 send() NPE，表现为 blocks 224 附近崩溃/大量假失败。

## Patch 内容
文件：
- work/run26/port/g33/lab/test_blocks_use_gui.mjs（完整可用脚本）
- work/run26/port/g33/lab/test_blocks_use_gui.patch（相对 test_blocks_use_fix.mjs 的 unified diff）

新增 closeScreens()：
- 每格开始时先清一次残留 screen；
- interact.useItem 后立即清 screen；
- screen.get -> none 才算成功；screen.close 最多重试 6 次、每次 350ms；
- screen.get RPC 失败（客户端可能崩）按失败处理，不吞；
- 清不掉就写 errors（screen stuck）并 break，避免整轮在坏 screen 上继续跑。

记录：
- guiOpened[]：本次 use 后看到 screen 的方块；
- entry.screenBefore / screenAfterUse / screenClosed；
- summary 增加 guiOpened 计数。

## 使用
把 probe 当前脚本备份后，直接运行新脚本：
node work/run26/port/g33/lab/test_blocks_use_gui.mjs --game <gameDir> [--limit N] [--ids <json>] [--out <json>]

或把 patch 应用到等价脚本；关键 helper 是 closeScreens。

## 预期
- 剪贴板/文件夹/蓝图/Ponder 方块右键后 screen 被关闭，后续方块继续；
- blocks 224 段不再因旧 screen 崩溃或误报；
- 若某方块确实让客户端崩，guiOpened/errors 能定位到 id；
- 仍建议配合 aero d8db812c / clipfix 等价修复，因为 screen.close 本身会走 ClipboardScreen.removed()。
