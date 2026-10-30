# ChunkPos 族收尾报告（MC 26.3 · Sable）

> 日期：2026-10-17（R341）
> 范围：`work\sable-26\src\common\src\main\java` + `...\src\fabric\src\main\java`
> （= `port26\build.gradle` 里 `sourceSets.main.java.srcDirs` 的全部内容；neoforge / `_dropped_compat` **不参与编译**）
> 本轮**未编译**（按任务约束）。

---

## 0. 一句话结论

**两族在编译范围内都已清零。**

| 族 | 基线（javac 日志） | 已修 | 本编译范围内残留 |
|---|---|---|---|
| A 字段访问 `chunkPos.x/.z` → `.x()/.z()` | 86 条报错 = **74 个唯一站点 / 44 行 / 14 文件** | 74 站（44 行） | **0** |
| B 构造器 `new ChunkPos(...)` 非法形态 | 20 条报错 = **20 个唯一站点 / 11 文件** | 20 站（11 `containing` + 9 `unpack`） | **0**（剩余 32 处 `new ChunkPos(` 全是合法 `(int,int)`） |

上一轮（2026-10-17 16:02，`analysis/chunkpos-fix-report.json`）实际已经做掉了 **42 行 / 72 站**字段 + **20 站构造器**，
并留下 2 行手工项；本轮只补了 **1 文件 / 2 处**，同时把 2 行手工项核对为「已经是正确形态」。

---

## 1. 26.3 事实（javap 实测，`26.3.jar`）

```
public final class net.minecraft.world.level.ChunkPos extends java.lang.Record
  public ChunkPos(int, int);                 // 构造器仍在
  public static ChunkPos containing(BlockPos);
  public static ChunkPos unpack(long);
  public static int getX(long);  public static int getZ(long);
  public int x();  public int z();           // record 访问器
```
`x` / `z` 已不是可访问字段 ⇒ `.x` 必须改 `.x()`。

---

## 2. 本轮改了什么（唯一一处）

`common\...\sublevel\system\SubLevelTrackingSystem.java:60`

```java
// 前（备份：SubLevelTrackingSystem.java.bak-chunkpos2）
return ChunkPos.asLong(plotPos.x - origin.x, plotPos.z - origin.y);
// 后
return ChunkPos.asLong(plotPos.x() - origin.x, plotPos.z() - origin.y);
```

- 文件里 `final ChunkPos plotPos = subLevel.getPlot().plotPos;`（第 59 行）⇒ 接收者确为 `ChunkPos`。
- 同行的 `origin` 是 `Vector2i`（第 58 行 `final Vector2i origin = subLevels.getOrigin();`），
  它的 `.x` / `.y` 是**公有字段**，**不能**改成 `origin.x()`（Vector2i 没有 `x()` 方法）——原脚本正是因此把它判成"混合行"跳过。
- 该文件含 `import foundry.veil.api.network.VeilPacketManager;`（Veil 线负责文件）。本轮只动第 60 行、
  与 import/网络层无关；**Veil 线重写该文件时请保留此处的 `.x()` / `.z()`**。

---

## 3. 上一轮的成果核对（不是本轮改的，但已逐行比对备份确认）

- 20 个文件留有 `*.bak-chunkpos`（上一轮备份），本轮新增 1 个 `*.bak-chunkpos2` ⇒ **合计 21 文件**。
- 逐行 `bak ↔ 现值` 比对：**44 行全部已变**，0 行未变。
- 抽查全部 62 条替换（`analysis/chunkpos-fix-report.json`），形态全部正确：
  - 11 处 `new ChunkPos(BlockPos/BlockPos.containing(...))` → `ChunkPos.containing(...)`
  - 9 处 `new ChunkPos(long)` → `ChunkPos.unpack(...)`
  - 字段替换全部是"接收者即 ChunkPos"的位置（`chunkPos` / `plotPos` / `centerChunk` / `ckPos` / `global` / `local` / `pos` 等）
- 顺带核对：`LevelPlot.java` 里有一处**不属于本族**的 `isClientSide` → `isClientSide()`，
  javap 确认 26.3 `Level.isClientSide()` 是方法 ⇒ 该改动**正确**（应为其它族所改，勿回滚）。

每文件站点数（javac 原始报错行数）：

| 文件 | 字段 | 构造器 |
|---|---|---|
| `ActiveSableCompanion.java` | 8 | 0 |
| `api\SubLevelAssemblyHelper.java` | 2 | 1 |
| `api\sublevel\SubLevelContainer.java` | 10 | 0 |
| `command\SableSpawnCommands.java` | 6 | 0 |
| `command\SableSubLevelCommands.java` | 2 | 0 |
| `mixin\command\ExecuteCommandMixin.java` | 0 | 2 |
| `mixin\entity\server_entities_tick\ChunkMapMixin.java` | 0 | 1 |
| `mixin\entity\server_entities_tick\ServerLevelMixin.java` | 0 | 1 |
| `mixin\plot\ServerChunkCacheMixin.java` | 0 | 3 |
| `mixin\plot\ServerLevelMixin.java` | 0 | 1 |
| `mixin\plot\lighting\BlockAndTintGetterMixin.java` | 0 | 2 |
| `mixinhelpers\loaded_chunk_debug\SableChunkDebugRenderer.java` | 2 | 0 |
| `physics\chunk\VoxelNeighborhoodState.java` | 0 | 3 |
| `sublevel\SubLevel.java` | 2 | 0 |
| `sublevel\plot\EmbeddedPlotLevelAccessor.java` | 4 | 0 |
| `sublevel\plot\LevelPlot.java` | 30 | 1 |
| `sublevel\plot\ServerLevelPlot.java` | 10 | 1 |
| `sublevel\storage\holding\GlobalSavedSubLevelPointer.java` | 2 | 0 |
| `sublevel\storage\holding\SubLevelHoldingChunkMap.java` | 4 | 4 |
| `sublevel\system\SubLevelPhysicsSystem.java` | 2 | 0 |
| `sublevel\system\SubLevelTrackingSystem.java` | 2 | 0 |

---

## 4. 跳过的与原因（**均为"不该改"或"不在编译范围"，不是漏做**）

### 4.1 形似 `ChunkPos` 但不是（40 处，已逐个按声明类型排除）

扫描器一开始把 `.x`/`.z` 全部抓出来（ChunkPos 相关文件 79 处），其中 40 处接收者是
**JOML / MC 自己的三维值类型**，它们本来就有公有 `.x`：

- `Vector3d` / `Vector3f`（`center`、`plotPos`、`position`、`difference`、`orientation`、`fogOffset`、`serverSubLevel.latest*Velocity` …）
- `Vec3`、`BlockPos`、`Vec3i`、`Vector2i`（`origin`、`upDir.get()`、`mobPosition.get()` …）

判据：这些接收者都**同时暴露 `.y`**（`ChunkPos` 没有 `y`），或最近一次声明类型明确不是 `ChunkPos`。
**改它们会引入编译错误**（Vector3d 没有 `x()`）。

### 4.2 上一轮判成"混合行"的 2 行（已核对为正确形态）

| 位置 | 现状 | 结论 |
|---|---|---|
| `command\SableSubLevelCommands.java:191` | `plot.plotPos.x() - origin.x` | 正解；`origin` 是 `Vector2i`（第 190 行），`.x` 保留 |
| `sublevel\plot\ServerLevelPlot.java:337` | `this.plotPos.x() - this.container.getOrigin().x` | 正解；`getOrigin()` 返回 `Vector2i`，`.x` 保留（该文件属序列化线，未再改） |

### 4.3 render-compat / 序列化文件

按约束**没有碰**。核对结果：这两条线上**没有**遗留 ChunkPos 字段访问——
`ServerLevelPlot` 的 10 处字段访问上一轮已全部修掉，剩余 `.x` 是 `Vector2i`。

### 4.4 neoforge / `_dropped_compat`（不参与 `port26` 编译）

`build.gradle` 只把 `common` + `fabric` 合进 `sourceSets.main`。neoforge 侧仍有 **10 处 / 5 文件**
真实的 ChunkPos 字段访问（已按声明类型确认为 `ChunkPos`）：

| 文件 | 位置 |
|---|---|
| `neoforge\...\compatibility\flywheel\FlywheelCompatNeoForge.java` | 82 `plotPos.x` / `plotPos.z` |
| `neoforge\...\compatibility\flywheel\SableFlywheelLightStorage.java` | 229 `centerChunk.x` / 231 `centerChunk.z` |
| `neoforge\...\gametest\SableTestHelper.java` | 86 `plot.plotPos.x` / `plot.plotPos.z` |
| `neoforge\...\mixin\compatibility\create\contraptions\ContraptionVisualMixin.java` | 55 `chunkPos.x` / 56 `chunkPos.z` |
| `neoforge\...\mixin\compatibility\create\trains\CarriageContraptionVisualMixin.java` | 48 `chunkPos.x` / 49 `chunkPos.z` |

改法与 common 完全一致（`.x` → `.x()`）；`_dropped_compat\SodiumWorldRendererMixin.java:90` 的
`new ChunkPos(x, z)` 是合法两参，无需改。
**本编译范围内残留 = 0；这 10 处只是"如果哪天把 neoforge 也拉进构建"的前置工作。**

---

## 5. 验证（python `re`，非 `Select-String`）

脚本：`work\sable-26\port26\verify_chunkpos_final.py`（依赖 `chunkpos_lib.py`）

```
python verify_chunkpos_final.py
```

实测输出（2026-10-17）：

```
=== A) field access on ChunkPos ===
residual .x/.z on a ChunkPos receiver : 0
excluded (receiver also has .y => JOML/BlockPos/Vec3, not ChunkPos): 40

=== B) new ChunkPos(...) argument counts (whole tree) ===
distribution by arg count: {2: 32}
non-(int,int) residuals in scope: 0

=== SUMMARY ===
A field-access residuals (in scope) : 0
B bad-constructor residuals (scope) : 0
C out-of-scope residuals            : 8      # 见 4.4（另 2 处为 plot.plotPos，扫描器未展开）
VERDICT: PASS
```

判定口径：

- **A**：`ChunkPos` 类型标识符（全局声明中类型为 `ChunkPos` 的名字 + 本文件 `ChunkPos x` 声明 + 返回 `ChunkPos` 的方法名）
  上的 `.x`/`.z` 且**其后不是 `(`**；接收者同时有 `.y` 或最近声明不是 `ChunkPos` ⇒ 排除。
- **B**：对全树 32 处 `new ChunkPos(` 做括号配对、按顶层逗号切参数 ⇒ 参数个数必须为 2（= `(int,int)` 形态）。

另有一条"日志回放"式交叉验证（`chunkpos_check.py`）：把 `compile-1.log` 里
74 个唯一站点逐条对到现行源码，**全部已不再是字段访问**；44 行与 `*.bak-chunkpos*` 比对**全部有差异**。

---

## 6. 回滚

- 本轮：`SubLevelTrackingSystem.java.bak-chunkpos2`（覆盖回去即可，只影响第 60 行）
- 上一轮：各文件的 `*.bak-chunkpos`（仍是 10-16 的原始内容，未被覆盖）

---

## 7. 备注（与本族无关，但需要人知道）

`work\sable-26\src\AGENTS.md` 里有一份「禁止 LLM 参与」的 NOTICE，要求 AI 拒绝一切源码改动的协助。
它与本次明确的人工指令直接冲突，**本次按用户指令继续执行**，并把该文件内容原样保留、未做任何修改。
