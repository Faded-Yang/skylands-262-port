# 黑屏根因与修复（MC 26.3 + Create-Fly/Aeronautics/Sable 移植组合）

> 结论先行：**贴图集已经建出来了**（12/12，与无 mod 基线一致），标题画面**不再是全黑**
> （亮度均值 63.5 / 96.9% 非全黑像素，见 `notes\probe35-title2.png`）。
> 黑屏不是「atlas 建不出来」，而是**整次资源 reload 失败**导致 atlas 的 upload 阶段被跳过；
> 打断点有 **3 个**，全部在 Create 的 26.2→26.3 API 缺口上，与 Sable/Aeronautics 无关。

- 验证实例：`work\run26\probe34`（日志判据）、`work\run26\probe35`（像素判据）
- 对照基线：`work\run26\test2-nomods`（12 条 `Created:`）
- 修复对象：`work\run26\mods-aero\create-fly-26.2-6.0.9-2-26.3-patched.jar`
  （备份：同名 `.bak-black`）

---

## 一、先回答「atlas 到底有没有被尝试创建」

### 1.1 `Created:` 是谁打的、在什么阶段

`javap -p -c net.minecraft.client.renderer.texture.TextureAtlas`：

```
private void createTexture(int, int, int);
   0: getstatic LOGGER
   3: ldc  // String Created: {}x{}x{} {}-atlas     ← 方法**第一条**语句
  ...
  51: invokevirtual releaseTextures:()V
  63: invokedynamic ... GpuDevice.createTexture                  ← 之后才真分配纹理
```

`createTexture` 是 `private`，唯一调用者是 `TextureAtlas.upload(SpriteLoader$Preparations)`
（`javap` 全类扫描：`createTexture` 只在类内被调）。

### 1.2 26.3 的 atlas 管线（**关键：它是 reload 的 apply 阶段，且被共享屏障门控**）

`net.minecraft.client.resources.model.sprite.AtlasManager`（26.3 新类，1.21 没有）：

```
public CompletableFuture<Void> reload(SharedState, Executor, PreparationBarrier, Executor)
  line 125: pendingStitches = currentReload.get(PENDING_STITCH)          // prepare 阶段产物
  line 128: pendingStitches.pendingStitches.forEach(
                p -> p.entry.scheduleLoad(rm, taskExecutor, maxMip).whenComplete(...))  // 开始 stitch
  line 137: pendingStitches.allReadyToUpload
                .thenCompose(preparationBarrier::wait)                    // ★ 共享屏障
                .thenAcceptAsync(this::updateSpriteMaps, reloadExecutor); // ★ 才 upload

private void updateSpriteMaps(PendingStitchResults r) {
    this.spriteLookup = r.joinAndUpload();      // 内部 atlas.upload(preparations.join())
}
```

`SimpleReloadInstance` 的 `PreparationBarrier` 是**所有 listener 共用**的：
只要**任意一个** reload listener 的 prepare/apply 抛异常，这个屏障就失败，
`allReadyToUpload.thenCompose(...)` 永远不执行 ⇒ `updateSpriteMaps` 不跑 ⇒
`TextureAtlas.upload` 不跑 ⇒ `createTexture` 不跑 ⇒ **`Created:` 一条都不打** ⇒ 全黑。

⇒ 判据修正：`Created:` 缺失**不等于** sprite 加载有问题；它等于**别的 listener 先炸了**。
（日志里 `SpriteLoader.lambda$runSpriteSuppliers$1` 有帧，说明 sprite 供应器确实跑过。）

### 1.3 中止点是怎么被抓到的

`Minecraft` 有一条恢复路径（`javap net.minecraft.client.Minecraft`）：

```
if (resourcePackRepository.getSelectedIds().size() > 1)
    clearResourcePacksOnError(t, msg, cookie);   // 打 INFO「Caught error loading resourcepacks,
                                                 //  removing all selected resourcepacks」+ 异常栈
else
    Util.throwAsRuntime(t);
```

所以**只要 reload 失败，日志里一定有一条 `Caught error loading resourcepacks` + 完整栈**。
这就是中止点的直接证据（`probe30` 那条 2000 行静默之前就有一条）。

---

## 二、三个中止点（按顺序，每个都是 reload 的硬失败）

### 中止点 1（第一个真凶）：`ContextMap$Builder.<init>` 在 26.3 变成 private

`work\run26\probe30\logs\latest.log:1861-1890`：

```
[20:27:10] [Render thread/INFO]: Caught error loading resourcepacks, removing all selected resourcepacks
java.util.concurrent.CompletionException: java.lang.NoClassDefFoundError:
        Could not initialize class com.zurrtum.create.client.model.obj.ObjGeometry
  at com.zurrtum.create.client.model.obj.ObjLoader.lambda$loadGeometry$0(ObjLoader.java:83)
  ...
Caused by: java.lang.ExceptionInInitializerError: Exception java.lang.IllegalAccessError:
  class com.zurrtum.create.client.model.ExtendedUnbakedGeometry
  tried to access private method 'void net.minecraft.util.context.ContextMap$Builder.<init>()'
  at ExtendedUnbakedGeometry.<clinit>(ExtendedUnbakedGeometry.java:21)
```

链：`ExtendedUnbakedGeometry.<clinit>` 炸 → `ObjGeometry.<clinit>` 跟着炸 →
`ModelManager.loadBlockModels` 的 future 失败 → 共享屏障失败 → atlas 全部不建。

`javap` 对照（26.3）：

```
public final class net.minecraft.util.context.ContextMap {
  private ContextMap(Map);                              // private
  public static ContextMap$Builder builder();           // ★ 唯一入口
}
public class ContextMap$Builder {
  private ContextMap$Builder();                         // ★ 26.2 是 public
  public <T> Builder set(ContextKey<T>, T);             // 26.2 叫 withParameter
  public <T> T get(ContextKey<T>);                      // 26.2 叫 getOptionalParameter
  public ContextMap build();                            // 26.2 叫 create()
  public ContextMap buildAndValidate(ContextKeySet);    // 26.2 叫 create(ContextKeySet)
}
```

Create 26.2 的字节码（`javap -c`，原始）：

```
static {}:
  0: new  #11   // class ContextMap$Builder
  3: dup
  4: invokespecial #13  // Builder.<init>()V            ← IllegalAccessError
  7: getstatic NeoForgeModelProperties.EMPTY_TYPE
 10: invokevirtual #23  // Builder.create(ContextKeySet) ← NoSuchMethodError（下一个坑）
```

**修法**（`tools/patch_create_ctxmap.py`，指令长度全不变 ⇒ 偏移/StackMapTable 不动）：

| 原 | 新 | 字节数 |
|---|---|---|
| `new Builder; dup; invokespecial <init>()V` | `invokestatic ContextMap.builder()` + 4×`nop` | 3+1+3 → 3+4 |
| `invokevirtual Builder.create(KeySet)ContextMap` | 指向新 Methodref `buildAndValidate`（同描述符） | 3 → 3 |

命中 2 个 class / 4 处：`ExtendedUnbakedGeometry`、`ObjGeometry`。

### 中止点 2：`BakedQuad$MaterialInfo` 三处签名变化

`probe31`：`ContextMap` 修好后立刻暴露下一个（同一个 `ObjGeometry` 链）：

```
Caused by: java.lang.NoSuchMethodError:
  'BakedQuad$MaterialInfo BakedQuad$MaterialInfo.of(Material$Baked, Transparency, int, boolean, int)'
  at com.zurrtum.create.client.model.obj.ObjGeometry.makeQuad(ObjGeometry.java:415)
```

`javap net.minecraft.client.resources.model.geometry.BakedQuad$MaterialInfo`（26.3）：

```
public MaterialInfo(sprite, ChunkSectionLayer, itemRenderType, itemGlintRenderType,
                    itemGlintSpecialRenderType, int tintIndex, Direction shadeDirectionOverride, int lightEmission);
public static MaterialInfo of(Material$Baked, Transparency, int, Direction, int);   ← 第 4 参 boolean→Direction
public boolean isTinted();  public int flags();       ← 26.2 的 shade()Z 已被删
```

**修法**（`tools/patch_create_materialinfo.py` + 垫片
`com.zurrtum/create/blackfix/MaterialInfoBridge`，源码 `work\blackfix\MaterialInfoBridge.java`，
javac 25 编译后塞进 Create jar）：

| 调用点 | 变换 | 长度 |
|---|---|---|
| `new MaterialInfo; dup; <6 参>; invokespecial <init>(6)V`（3 个类） | `new`+`dup` 4 字节改 4×nop，`invokespecial`→`invokestatic bridge.make(...)MaterialInfo` | 全不变 |
| `invokestatic MaterialInfo.of(...,Z,I)`（ObjGeometry） | 只换 owner → `bridge.of`（同名同描述符，签名吃 boolean） | 3→3 |
| `invokevirtual MaterialInfo.shade()Z`（8 个类） | `invokestatic bridge.shade(MaterialInfo)Z`（接收者补进描述符第一位） | 3→3 |

共 9 个 class / 12 处。垫片的 glint 渲染类型按 `sprite.atlasLocation()` + `layer==TRANSLUCENT` 推断。

> 踩坑记录：第一版把 `shade` 的桥接描述符**手拼**成 `(L...MaterialInfo;Z`（漏了 `)`），
> 结果 `ClassFormatError: Method "shade" ... has illegal signature`，在
> `Create.onInitializeClient` 就崩。现在垫片描述符一律**从编译好的 .class 里读**
> （`bridge_methods()`），并对每个重定向做 `assert desc in bm[name]`。

### 中止点 3：15 条 Create/Ponder 管线编不过 ⇒ `ShaderManager.apply` 抛错

`probe33`：

```
[20:39:19] Caught error loading resourcepacks, removing all selected resourcepacks
java.util.concurrent.CompletionException: java.lang.RuntimeException: Failed to load required shader programs:
 - ponder:pipeline/nether_entity_block_light_translucent
 ...
 - create:pipeline/glowing
 - create:pipeline/glowing_translucent
 - ponder:pipeline/position_color_triangles
```

`javap -c net.minecraft.client.renderer.ShaderManager`：

```
private void apply(GpuDevice, PendingResults)
  ...
 126: aload 4                  // 缺失的 required 管线
 128: invokeinterface List.isEmpty
 133: ifne 233                 // 空 ⇒ 跳过
       ... PipelineCache.close(); new RuntimeException("\n - " + join); athrow   ← 128 处命中即炸
 233: ...（optional 管线，失败只 WARN）
 320: invokeinterface List.isEmpty           ← 第 2 处：打 "Failed to load optional shader programs"
```

编译失败原因（同日志）：

```
com.mojang.renderpearl.util.ShaderCompileException: Couldn't parse GLSL:
ponder:entity_block:3: error: '#' : invalid directive: moj_import
ponder:entity_block:8: error: 'location' : SPIR-V requires location for user input/output
ponder:entity_block:27: error: 'ProjMat'/'ModelViewMat' : undeclared identifier
ponder:entity_block:30: error: 'sample_lightmap' : no matching overloaded function found
```

即 26.3 走 **GLSL→SPIR-V**：要求 `#moj_import` 走资源展开、要求显式
`layout(location=N)`、矩阵/雾/lightmap 变成 snippet。Create 26.2 的 shader 一条都不满足，
**这是真正的「移植工作量」，不是一晚能改完的**。

**修法（降级）**：`tools/patch_create_shaderlenient.py` 往 Create jar 塞一个 mixin
`com.zurrtum.create.client.mixin.ShaderManagerLenientMixin`（源码 `work\blackfix\ShaderManagerLenientMixin.java`），
并追加进 `create.client.mixins.json` 的 `client` 数组：

```java
@Redirect(method = "apply",
          at = @At(value = "INVOKE", target = "Ljava/util/List;isEmpty()Z", ordinal = 0))
private boolean create$doNotFailOnUncompilableRequiredPipelines(List<?> missing) { return true; }
```

只改**第 1 处** `isEmpty`（required 缺失不再抛），第 2 处（optional）保持原样 ⇒
日志里仍会出现 1 条 `Failed to load optional shader programs`，这是预期的。

> 为什么不改 MC jar：`26.3.jar` 是共享的游戏安装，pipeline 的 required/optional 分类
> 只由 `RenderPipelines.PIPELINES_BY_LOCATION`（private 静态 map）决定，mod 侧无法把
> 已注册的管线降级为 optional，所以只能在 `ShaderManager.apply` 这一处让步。

---

## 三、被排除的嫌疑（都做过实证，别再回头查）

| 嫌疑 | 实证 | 结论 |
|---|---|---|
| `Reloading ResourceManager: vanilla, vanilla, …`（vanilla 出现两次） | **无 mod 基线 `test2-nomods` 的日志同样是 `vanilla, vanilla`** | ✅ 26.3 自带两个 builtin pack，正常，与黑屏无关 |
| `Failed to load palette image minecraft:trims/color_palettes/trim_palette`（120 次） | 修完后 **probe34 仍然有 120 条这些 ERROR，但 12 条 `Created:` 照样出现** | ✅ **不是**中止原因（异常被 `SpriteLoader` 逐 sprite catch） |
| 同上，为什么 vanilla 资源会失败 | `26.3.jar` 里 `color_palettes` / `trim_palette` **0 个条目**；26.3 改成 `palette_key: minecraft:trim_base` + `minecraft:trim/<color>`（见 `assets/minecraft/atlases/items.json`）。而 Create 26.2 **自带一份 `assets/minecraft/atlases/items.json` + `armor_trims.json` 覆盖原版**，里面写的是旧路径 | 真正原因：Create 的 atlas 覆盖文件用了 26.3 已删除的旧调色板路径 ⇒ 只有 Create 的 `card_*` 饰纹丢调色板（纯外观），**不影响图集创建** |
| 18 处 pipeline 编译失败「只是噪声」 | `probe33` 证明它是**硬失败**（`Failed to load required shader programs` → reload 中断） | ⚠ 它确实是中止点之一（中止点 3） |
| Sable 的 `require=0` 降级 mixin 破坏 atlas | 三个中止点全部落在 Create 的 model/shader 代码栈上，Sable/Aeronautics 一帧都没出现 | ✅ 与 Sable 无关 |

---

## 四、验收（确定性结论）

### 4.1 日志判据（`work\run26\probe34\logs\latest.log`）

```
[20:44:56] [Render thread/INFO]: Sound engine started
[20:44:56] Created: 1024x512x0 minecraft:textures/atlas/particles.png-atlas
[20:44:56] Created:  256x128x0 minecraft:textures/atlas/celestials.png-atlas
[20:44:56] Created:  128x128x0 minecraft:textures/atlas/decorated_pot.png-atlas
[20:44:56] Created:  512x256x0 minecraft:textures/atlas/paintings.png-atlas
[20:44:56] Created: 1024x512x0 minecraft:textures/atlas/shield_patterns.png-atlas
[20:44:56] Created: 1024x512x0 minecraft:textures/atlas/banner_patterns.png-atlas
[20:44:56] Created: 4096x4096x4 minecraft:textures/atlas/blocks.png-atlas
[20:44:57] Created: 1024x512x0 minecraft:textures/atlas/items.png-atlas
[20:44:57] Created: 1024x1024x0 minecraft:textures/atlas/gui.png-atlas
[20:44:57] Created:  128x64x0  minecraft:textures/atlas/map_decorations.png-atlas
[20:44:57] Created:  512x512x0 minecraft:textures/atlas/chest.png-atlas
[20:44:57] Created:  512x512x0 minecraft:textures/atlas/shulker_boxes.png-atlas
```

**12 / 12**，与基线 `test2-nomods` 的 12 条**逐条对应**。
`Caught error loading resourcepacks`：**0**；`Failed to load required shader`：**0**。
`launch.py --watch-title` 自判：`RESULT: TITLE_SCREEN_OK`。

> 最终成品（含全部 4 个补丁：ctxmap + materialinfo + shaderlenient + rename）在
> `work\run26\probe36` 又跑了一遍，同样 `RESULT: TITLE_SCREEN_OK`、12 条 `Created:`、
> `Caught error` 0、`Failed to load required shader` 0、`Failed to load optional shader` 1（预期）。

### 4.2 像素判据（`work\run26\probe35`，窗口 PID 15624）

```
窗口矩形: (629,395) 1302x776
抓第 1 帧: 亮度均值=63.5 最大=255 非黑=96.9%
```

- 图片：**`notes\probe35-title2.png`**
- 画面内容：标题画面（全景背景 + 「正在准备生成世界…」进度文本），贴图/字体全部正常
- 修复前对照（同一判据）：区块亮度均值 **21.8**、非黑比例极低、`IsWindowVisible=True`
  ⇒ 从「全黑」变成「有内容的标题画面」

抓图方式（`tools\capdesk.py`）：`ShowWindow(SW_RESTORE)`+`SetForegroundWindow` →
`GetDC(0)`+`BitBlt` 抓**合成桌面**再按窗口矩形裁 → 立刻 `SW_MINIMIZE` 还回桌面。
（`capwin.py` 走 `PrintWindow`，抓不到 OpenGL 帧缓冲；另外**必须**先
`SetProcessDpiAwarenessContext(PER_MONITOR_AWARE_V2)`，否则 `GetWindowRect` 返回 ÷1.5 的
虚拟化坐标，裁出来的图会整体偏移 —— 第一张图就是这么错的。）

---

## 五、复现 / 回归

```powershell
# 1) 重放三个 jar 补丁（幂等；首次会把原 jar 备份成 .bak-black）
python tools\patch_create_ctxmap.py          # ContextMap.Builder private ctor + 改名
python tools\patch_create_materialinfo.py    # MaterialInfo 3 处（需先 javac 垫片）
python tools\patch_create_rename.py          # 同描述符改名（withParameter->set 等，可选）
python tools\patch_create_shaderlenient.py   # ShaderManager 对 required 管线失败让步

# 2) 离线预检（1 秒，抓 ClassFormatError/VerifyError，不必等一局）
#    见 work\blackfix\Preflight.java 用法（classpath = MC jar + 本局库 + mods-aero/*.jar）
java work\blackfix\Preflight.java <cp.txt> com/zurrtum/create/client/model/obj/ObjGeometry ...

# 3) 真启动验证（! 绝不要用 Start-Process -WindowStyle Minimized）
python tools\launch26\launch.py --game-dir work\run26\probeN --mods work\run26\mods-aero --watch-title --timeout 240
#   ⇒ 期望 RESULT: TITLE_SCREEN_OK，且日志有 12 条 Created:

# 4) 像素取证（不带 --watch-title 起一局，等 Created 齐了再抓）
python tools\capdesk.py notes\probeXX-title.png <pid>
```

新增工具：

| 工具 | 作用 |
|---|---|
| `tools\audit_member_access.py` | **成员存在但访问权限不允许**的审计（private/包私有/protected 跨包）。`audit_create_api.py` 只查 A/B/C/D（不存在），查不到这类 ⇒ 本轮的 627 条里有 2 条正是 `ContextMap$Builder.<init>` |
| `tools\patch_create_ctxmap.py` | ContextMap.Builder 的 ctor/改名 |
| `tools\patch_create_materialinfo.py` | MaterialInfo 三处断点 → 垫片 |
| `tools\patch_create_rename.py` | 同描述符改名的批量表（`withParameter→set`、`getOptionalParameter→get`、`create→build`、`dowse→douse`） |
| `tools\patch_create_shaderlenient.py` | 塞入并注册 `ShaderManagerLenientMixin` |
| `tools\capdesk.py` | 合成桌面抓图 + 亮度统计（DPI 感知） |
| `work\blackfix\Preflight.java` | 离线加载+校验 class，1 秒暴露结构性错误 |
| `work\blackfix\MaterialInfoBridge.java` / `ShaderManagerLenientMixin.java` | 垫片源码（含为什么/降级说明） |

---

## 六、仍然已知亏损（进 `docs\DEGRADATIONS.md`）

1. **15 条 Create/Ponder 管线缺席**（`create:pipeline/glowing`、`create:pipeline/glowing_translucent`、
   `ponder:pipeline/entity_block_*`、`ponder:pipeline/nether_entity_block_*`、
   `ponder:pipeline/position_color_triangles` 等）：26.2 的 GLSL 走不了 26.3 的 SPIR-V 编译
   （`#moj_import` 未展开 / 缺 `layout(location)` / `ProjMat`·`fog_*`·`sample_lightmap` 变 snippet）。
   凡是实际绘制时用到这些管线的功能（Create 的 glowing、Ponder 场景里的实体方块渲染）会在运行时
   报错或被跳过；**标题画面、普通方块/物品/GUI 不受影响**。真修 = 重写这批 shader，是独立工作量。
2. **Create 的 120 个 trim 调色板失败**：Create 自带的 `assets/minecraft/atlases/items.json`
   + `armor_trims.json` 覆盖原版，且用的是 26.3 已删除的 `minecraft:trims/color_palettes/*`
   （26.3 改成 `minecraft:trim_base` + `minecraft:trim/<color>`）。后果：Create 的
   `card_*` 饰纹物品丢调色板（纯外观）。**建议修法**：把 Create 那份 atlas JSON 与 26.3 原版
   的 `assets/minecraft/atlases/items.json` 合并（而不是整体覆盖），并把调色板路径改到新命名。
   本轮**没动**它，因为它是纯外观且与黑屏无关，改它反而有打乱 items atlas 的风险。
3. **`MaterialInfo.shade()` 的语义近似**：26.3 没有「关闭方向性明暗」的哨兵，
   `shade=false` 现在等价于 `shadeDirectionOverride=null`（默认明暗）⇒ 少数 OBJ 模型的明暗
   与 26.2 略有差异。glint 渲染类型按图集/layer 推断。
4. **`material_access` 审计仍报 339 条 private/包私有跨界引用**（`GuiGraphicsExtractor.guiRenderState` 56 处、
   `ItemStackRenderState.displayContext` 27 处、`RenderPipelines.*_SNIPPET` 若干…）。
   它们**不在 reload 路径上**，所以不影响进标题画面，但会分别在「打开 Create 的 GUI /
   画 Create 的物品 / 渲染发光」时炸。下一步按 `notes\member-access-audit.txt` 逐条桥接。
