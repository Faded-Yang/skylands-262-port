# interact-probe 验证方法（可复用）

> 由 `interact-probe` 汇总；配套探针在 `work\run26\port\g33\probe\src\skylands262\g33probe\G33Probe.java`，驱动脚本 `work\run26\port\g33\_run.py`。

## 1. hold 类方块逐块验证：phase S

```powershell
cd work\run26\port\g33
python _run.py --tag S-check --game-dir game-S-check --mods stage\<arm> --phase S --g-list "simulated:physics_assembler,simulated:throttle_lever"
```

- 每块：自动放置在石柱上（5 列网格）→ 三次机位对准 → 60 tick 按住（每 3 tick 一次 `mc.gameMode.useItemOn` + 每 tick 反射驱动 `activeTick`/`activeOnMouseMove(0,-6)`）→ 每 6 tick 记录 fraction/managerActive → release 后再记录。
- fraction 通用读取：取 `HoldInteractionManager.active`（私有静态字段）实例，依次尝试 `getFraction()` / 字段 `animatedValue` / `value` / `progress`。
- 读不到会返回负数哨兵（-1 无 active、-2 反射异常、-3 无可用字段）；遇到负数说明该 handler 字段名不同，需 javap 查。
- 判据：fraction 单调上升、无周期清零、release 后 `managerActive=false`。

## 2. 合成输入的边界（实测结论）

- `MouseHandler.onButton(handle, MouseButtonInfo(1,0), 1/0)`：只更新按键状态并派发 Screen；**不会**触发 `Minecraft.tick → handleKeybinds → startUseItem`，因此**不能**启动 hold（两臂 isActive 均 false）。
- `KeyMapping.set(key,true) + KeyMapping.click(key)`：会被每 tick 的 Input 轮询覆盖，`handleKeybinds` 里 keyUseDown 仍为 false。
- 要在客户端真正启动交互，实测最可靠的是 `mc.gameMode.useItemOn(player, hand, BlockHitResult)`；要模拟按住重复触发，则每 3 tick 调一次 useItemOn。
- `InputConstants` 在 26.3 位于 `com.mojang.blaze3d.platform.InputConstants`（不是 `net.minecraft.client.input`）。

## 3. 截图与槽位绑定（避免串位）

- vanilla `Screenshot.grab(mc,false)` 按秒级时间戳命名，连续截图会同秒产生 `_2` 后缀，按 mtime 排序会串位；
- 探针每次 grab 后立即扫描 `gameDirectory/screenshots` 取最新文件，写进事件：`G_SHOT name=block_i id=... file=<刚写入文件名>`；**永远用日志里的 file 名映射槽位**。
- 结论：用 `G_SHOT file=` 绑定后 A9 singles 12 张 sha 全唯一；此前 g3 的 s2/s3 重复就是 mtime 串位。

## 4. 看图判据

- 进度条/提示文字必须裁剪放大：进度条在准星右侧、竖条 14×72；hold tip 在屏幕中下；
- F2 的「已将截图保存为…」会在左下堆叠遮挡，crop 取右侧/中下；
- 普通世界 vs sublevel 同机位对比时，先确认两张图都是目标方块（本次 A9 出现过「相机拍到远处/天空」的废片；已加硬闸：aim 后 `mc.hitResult.blockPos == 放置位置` 才截图）。

## 5. sublevel 内交互现状（R430 时点）

- pick（sable pick7）已能返回世界坐标：`[sky262pick] scanned=2 bestWorld=(-339.118,77.604,-37.5) replaced=1813`；
- 但该世界位置在世界层是 air（方块在 sublevel 里），`gameMode.useItemOn` 客户端发出后**服务端 `useWithoutItem` 不触发**（union dbg 实测服务端只有普通世界那条）；
- 结论：需客户端 quiet_use 拦截或服务端按 plot 坐标解析方块（ponder-26 处理中）。

## 6. 常用探针 phase 速查

| phase | 用途 |
|---|---|
| H | 组装 sublevel、物理/pose 测量、h-clean 清净场景交互 |
| L | 组装器 floor/wall/ceiling 拉杆与 hold 交互截图 |
| T | 油门拉杆 + 对接连接器渲染 |
| G | 网格/单块渲染对照截图（含 aim 硬闸与 G_SHOT file 绑定） |
| S | 逐块 hold 行为验证（fraction 单调/release） |
| R | 重复 useItemOn 模拟真实按住（复现清零/重启） |
| V/W/X/Y/M | 合成鼠标/startUseItem/空手 vs 持物/pick/纯 mixin 实验（历史用途） |

## 7. 纪律

- 每次 run 用全新 game-dir（`_run.py` 自动拷模板存档 + 删 session.lock）；
- 只用 staging，**从不写 `mods-stable`**；
- 跑完 `_run.py` 会杀进程树；确认 `Get-Process java`；
- 默认 1280×720；截图需清晰。