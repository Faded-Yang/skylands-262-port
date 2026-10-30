# Create 剪贴板 GUI NPE 修复（R-clipboard）

> 证据：`game-v102/crash-reports/crash-2026-10-21_03.15.56-client.txt`；扫方块到 index 224 (`create:clockwork_bearing`) 时，`ClipboardScreen.send/removed` 对 `this.content == null` 解引用。

## 根因

- `ClipboardScreen.removed()` 先执行 `this.content = this.content.setPreviouslyOpenedPage(i)`（第 329 行），再 `send()`；
- `send()` 里又 `this.content = this.content.setPages(...)`；
- 当屏幕的 clipboard content 未初始化（从方块/物品打开后 content 为空）时，`removed()`/`send()` 直接 NPE。

## 修复

`work/run26/port/g145/src/ClipboardScreen.java`：

- `removed()`：仅当 `this.content != null` 才遍历 pages + `send()`；最后总是 `super.removed()`；
- `send()`：入口先判 `content == null` 直接 return（防御其它调用路径）。

## 候选

| 项 | 值 |
|---|---|
| 文件 | `work/run26/port/g150/stage-final/mods-candidate/create-fly-26.2-6.0.9-2-26.3-patched.jar` |
| 改动 | 仅 `ClipboardScreen.class`（ASM 在原 class 上插入判空，保留原 frames；inner 不重建） |
| SHA-256 | `6e334359d3089f8e5fa5b5b9086b46b6c5db55150526530b896ed378394a0063` |
| staging | `g146/stage-final/mods-candidate`（116 jar，create-fly 同名替换） |

## 验证（g146 VerifyError 复盘）

- 第一版用 decompiled 源码重编译整个 `ClipboardScreen`，本地 `-Xverify:all` 通过，但游戏内打开剪贴板报 `VerifyError: Expecting a stackmap frame`；
- 改为 ASM 直接修改 **原 live class**：在 `removed()` / `send()` 开头插入 `if (content == null) return;`，`COMPUTE_FRAMES` 重算，inner classes 不替换；
- 本地 `java -Xverify:all` 加载 4 个 ClipboardScreen 类全部 OK；

## 验证

- 从方块/物品打开剪贴板 GUI 后按 ESC/切换 screen：不再 NPE；
- blocks 全量复扫可从 224 继续；0 crash。
