# fix-ponder-shaders —— 把 ponder/create 的 GLSL 移植到 26.3（`#moj_import` → `#include`）

> **结论：15 条管线编译错误 → 0 条**（旧件 `F950B952…` 实测 15 条，新件 0 条），
> 交付件本体 `TITLE_SCREEN_OK` 37.4 s + `WORLD_OK` 56.0 s，各类错误计数全 0，
> `mods-stable` 仍 **71 jar**，地雷扫描 **83 → 81**（只少不多）。
>
> | 项 | 结果 |
> |---|---|
> | `Couldn't compile pipeline` | 旧件 **15** → 新件 **0** |
> | `moj_import` / `invalid directive` / `ShaderCompileException` / `Failed to load optional` | 旧件 54 / 15 / 15 / 1 → 新件 **0 / 0 / 0 / 0** |
> | 交付件 jar 变化 | 14336 entries，**只有 6 个 entry 变**（4 个 shader + 2 个 class），无增删 |
> | Ponder 真机验到哪一层 | `/ponder create:basin` → **PonderUI 真的打开、3D 场景真的开始渲染**；死在**下一族** `PreparedFrame.executeSolid()`（26.3 改成要 `RenderPass` 参数，设计级改动，不在本轮）——见 §9 |
> | 重扫 | `create-fly` 原始发现 1123→1120，地雷组 83→**81**（HIGH 27/27、MED 16→14、LOW 40/40），**新增 0 组**；归零的正是 `getDynamicUniforms` + `writeTransform` |
>
> ⚠ **没有把「编译过」说成「能画」**：本轮证明的是「管线全部编译成功 + ponder 场景渲染流程真的往前跑」，
> 不是「屏幕上有动画」。§9 把断点精确到方法行号。

---

## 0. 目录（`work/run26/watch` 全程未读写；未动 `mods-full`/`mods-fix2`/`mods-crashfix`/`work/sable-26`/`work/build26`/`g6`–`g16`）

```
work/run26/port/g18/
  shaders_old/            从交付件里导出的 4 个旧 GLSL（改前原文，留档）
  vanilla_shaders/        26.3.jar 里 assets/minecraft/shaders/** 全量（对照用，93 个文件）
  shaders_new/            改后的 4 个 GLSL（交付内容）
  javap_*.txt             ShaderManager / PipelineBuilder / RenderPipelines / BindGroupLayouts /
                          DefaultVertexFormat / RenderSystem / PreparedFrame … 的 javap 现场证据
  asm/PatchPipelines.java          +1 个 withBindGroupLayout(DYNAMIC_TRANSFORMS)
  asm/PatchDynamicUniforms.java    DynamicUniforms → DynamicGpuData 两处 method-ref 重定向
  oldcls/ newcls/         改前 / 改后 class（包路径完整）
  _patch_jar.py _jar_diff.py _mkmods.py _mkworld.py _run_world.py _deliver.py  由 g16 复制（同一深度）
  probe/                  一次性驱动 mod（phase=ponderscene，**不进交付**）
  mods-r1 … mods-r5      每轮 70 硬链接 jar + 当轮 create + 探针
  game-r1 … game-r5 / final   每次都是存档模板的**全新副本**（用一次就换名字）
  evidence/               每次的 latest.log / console.log
  scan_after.md / .json   重扫结果
```

---

## 1. 「15 条」到底是谁（先把清单钉死）

`work/run26/port/g16/evidence/final-world-latest.log` 里 `Couldn't compile pipeline` 共 **15 行**，逐条点名：

| # | pipeline | 编译期报的错 | 根因 |
|---|---|---|---|
| 1–12 | `ponder:pipeline/entity_block_{solid,cutout,translucent}`<br>`ponder:pipeline/entity_block_light_{…}`<br>`ponder:pipeline/nether_entity_block_{…}`<br>`ponder:pipeline/nether_entity_block_light_{…}` | `'#' : invalid directive: moj_import`（vsh 3–6 行）<br>+ `'location' : SPIR-V requires location for user input/output`（10 行）<br>+ `'ProjMat'/'ModelViewMat' : undeclared identifier`<br>+ `fog_spherical_distance`/`sample_lightmap` : no matching overloaded function | 同一份 `assets/ponder/shaders/entity_block.{vsh,fsh}` |
| 13–14 | `create:pipeline/glowing` / `create:pipeline/glowing_translucent` | 同上，`create:core/glowing_shader:3..5` | `assets/create/shaders/core/glowing_shader.{vsh,fsh}` |
| 15 | `ponder:pipeline/position_color_triangles` | `ShaderCompileException: Unable to find shader defined uniform (DynamicTransforms)` | **Java 侧**少挂一个 bind group layout（shader 是 vanilla 的 `core/position_color`，资源改不了） |

> ⚠ 交接说明里写的是「15 条 = `ponder:pipeline/entity_block_*`」，实测**不全是**：
> 12 条 entity_block + 2 条 create glowing + 1 条 position_color_triangles。
> 旧的 3 行 `#moj_import` 报错在日志里被重复计数，所以「54 行 moj_import」≠ 54 个错。

15 行完整报错（`entity_block` 一份，12 条 pipeline 逐字相同）：

```
com.mojang.renderpearl.util.ShaderCompileException: Couldn't parse GLSL: ponder:entity_block:3: error: '#' : invalid directive: moj_import
ponder:entity_block:4: error: '#' : invalid directive: moj_import
ponder:entity_block:5: error: '#' : invalid directive: moj_import
ponder:entity_block:6: error: '#' : invalid directive: moj_import
ponder:entity_block:8: error: 'location' : SPIR-V requires location for user input/output
   …（9/10/12/14/16/21/22/23/24 行同一条）
ponder:entity_block:27: error: 'ProjMat' : undeclared identifier
ponder:entity_block:27: error: 'ModelViewMat' : undeclared identifier
ponder:entity_block:28: error: 'fog_spherical_distance' : no matching overloaded function found
ponder:entity_block:29: error: 'fog_cylindrical_distance' : no matching overloaded function found
ponder:entity_block:30: error: 'sample_lightmap' : no matching overloaded function found
```

注意顺序 = 因果链：**include 失败 ⇒ uniform/函数全没声明**；另外还有一条**独立**的 location 要求。
所以「老 uniform 名」不是改名，是 `#moj_import` 没生效导致的连带错误（§3.3 有 26.3 的原文对照）。

---

## 2. 26.3 的 shader 加载器到底怎么工作（javap 现查，不凭记忆）

### 2.1 include 机制：`#include <namespace:path.glsl>`，由 Java 提供文本

`javap -p -c -cp 26.3.jar net.minecraft.client.renderer.ShaderManager`（`javap_shadermanager.txt`）：

| 证据 | 含义 |
|---|---|
| `SHADER_INCLUDE_CONVERTER = new FileToIdConverter("shaders/include", ".glsl")` | include 文件在 `assets/<ns>/shaders/include/*.glsl` |
| `includeShaderLocationToId()`：`fileToId(id).withSuffix(".glsl")` | 文件 `.../include/fog.glsl` ⇒ id **`minecraft:fog.glsl`**（**带 `.glsl` 后缀**） |
| `loadInclude(...)` → `CachedIncludeSource.create(id, text)` | Java 侧把 include 文本交给编译器的缓存对象 |
| `ShaderSource` 接口：`getShader(id, type)` / `getInclude(id)` / `close()` | 编译器按 id 向 Java 取 include |
| `loadConfigs()` 里 `ShaderType.byLocation(id)` 分 `.vsh/.fsh`，`SHADER_INCLUDE_CONVERTER.matches(id)` 分 classpath 扫描 | 只有 `.vsh/.fsh` 是 shader，`shaders/include/**.glsl` 是 include |

⇒ **`#moj_import` 这个指令 26.3 的编译器完全不认识**（它来自 1.21.x 的 include 语法），
26.3 用 GLSL 标准的 **`#include <...>`**，且 include 由 vanilla 的 `ShaderManager` 提供，
**不需要 mod 侧写任何 include 钩子**（这也是能走纯资源路线的根据）。

vanilla 自己怎么写（`vanilla_shaders/.../core/entity.vsh` 第 4–10 行原文）：

```glsl
#version 330
#extension GL_ARB_separate_shader_objects : require

#if defined(PER_FACE_LIGHTING) || !defined(NO_CARDINAL_LIGHTING)
#include <minecraft:light.glsl>
#endif
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:sample_lightmap.glsl>
```

### 2.2 uniform：全部搬进 std140 UBO，名字没变、容器变了

`assets/minecraft/shaders/include/dynamictransforms.glsl`（26.3 原文）：

```glsl
layout(std140) uniform DynamicTransforms {
    mat4 ModelViewMat;
    mat4 TextureMat;
    vec4 ColorModulator;
    vec3 ModelOffset;
};
```

`fog.glsl` → `layout(std140) uniform Fog { vec4 FogColor; float FogEnvironmentalStart; … }`；
`projection.glsl` → `uniform Projection { mat4 ProjMat; }`。

⇒ `ModelViewMat` / `ProjMat` / `FogColor` **一个都没改名**，但它们的声明现在只在 include 里，
include 挂掉就全变 `undeclared identifier`。**不需要改 Java 的 uniform 上传**（见 §2.4）。

### 2.3 SPIR-V 要 `layout(location=…)`，varying 按 location 配对

- 编译器是 `com.mojang.renderpearl.frontend.shaders.GlslCompiler.compileToSpv`（报错栈里的 `GlslCompiler.java:140`），
  它要求所有 in/out 都带 location，否则就是报错里那 10 行 `SPIR-V requires location for user input/output`。
- **顶点属性按名字**匹配：`PipelineBuilder.generateBackendCreateInfo` 用
  `Map<String(SPIR-V input name), InterfaceVariable>` 去查 `VertexFormat` 的元素名，
  查不到就抛 `vertex shader (%s) attrib (%s) does not have a matching vertex buffer element`。
  `AttribBinding` 的 location 直接取 shader 自己声明的 `InterfaceVariable.location()`。
- **varying 按 location** 配对：`Vertex shader (%s) missing output at location %d consumed by Fragment shader`、
  `… base type mismatch at location %d`、`… vector length mismatch at location %d`。
  ⇒ vsh 的 out 和 fsh 的 in 必须 **同号同类型**。

这解释了两件事：

1. `ponder:entity_block` 一份 shader 被 **两种** `VertexFormat` 复用（12 条 pipeline 里 6 条用 `ENTITY`、6 条用 `BLOCK`），
   而 26.3 里 `BLOCK` 只有 4 个元素（`Position, Color, UV0, UV2`）、`ENTITY` 有 6 个
   （`Position, Color, UV0, UV1, UV2, Normal`）。因为**匹配按名字**，所以只要
   声明名字对得上、location 自洽，同号不必等于格式下标 → 一份 shader 能同时服务两种格式。
   这也是旧 shader 里 `#if defined(OVERWORLD) || defined(NETHER)` 只给 ENTITY 变体声明 `UV1/Normal` 的原因
   （BLOCK 没有这两个元素，声明了就会报 "does not have a matching vertex buffer element"）。
2. `#version 150` 的 `glowing_shader` 必须升到 330（`layout(location)`、UBO 都要 330 起）。

### 2.4 bind group：pipeline 必须声明 shader 用到的每个 uniform block

`PonderRenderPipelines` 用的是 **26.3 形状**（这部分 ZurrTum 分支已经改好了）：

```
RenderPipeline.builder(RenderPipelines.MATRICES_FOG_SNIPPET)   // GLOBALS + PROJECTION + DYNAMIC_TRANSFORMS + FOG
    .withVertexShader(ponder:entity_block).withFragmentShader(ponder:entity_block)
    .withBindGroupLayout(BindGroupLayouts.SAMPLER0_SAMPLER2)   // Sampler0 + Sampler2
    .withVertexBinding(0, ENTITY 或 BLOCK)
    .withPrimitiveTopology(QUADS).withDepthStencilState(DEFAULT)
```

`MATRICES_FOG_SNIPPET` = `GLOBALS_SNIPPET`(`Globals`) + `BindGroupLayouts.PROJECTION` + `DYNAMIC_TRANSFORMS` + `FOG`
（`javap_renderpipelines.txt` 第 567–598 行）。`BindGroupLayouts` 的 uniform 名字是
`DynamicTransforms / Projection / Fog / Globals / Sampler0 / Sampler2`（`javap_bgl.txt`），
和 include 里 block 的名字一字不差 ⇒ **只要 include 写对，block 就自动对上，Java 不用动**。

---

## 3. 逐条根因与修法

### 3.1 A 类：`#moj_import` → `#include`（12 + 2 = 14 条）

| 文件 | 改前 | 改后 |
|---|---|---|
| `assets/ponder/shaders/entity_block.vsh` | `#moj_import <minecraft:fog.glsl>` 等 4 行 | `#include <minecraft:fog.glsl>` 等 4 行 |
| `assets/ponder/shaders/entity_block.fsh` | `#moj_import <minecraft:fog.glsl>` | `#include <minecraft:fog.glsl>` |
| `assets/create/shaders/core/glowing_shader.vsh` | 3 行 `#moj_import` + `#version 150` | 3 行 `#include` + `#version 330` |
| `assets/create/shaders/core/glowing_shader.fsh` | 2 行 `#moj_import` + `#version 150` | 2 行 `#include` + `#version 330` |

**为什么用 include 而不用「内联」**：两种都能修，但 include 是 vanilla 自己用的唯一写法，
且把 UBO 布局留在 vanilla 侧（vanilla 改 block 布局时 shader 自动跟随）。
内联要手抄 `DynamicTransforms/Fog/Projection` 三个 block，一旦和 `BindGroupLayouts` 的字段顺序
有偏差就是另一类难查的错。include 不需要任何 Java 钩子（§2.1），所以仍然是**纯资源**路线。

### 3.2 B 类：补 `layout(location=…)` + `#extension`（同样是那 14 条）

以 `entity_block` 为例（改后全文见 `shaders_new/`）：

```glsl
#version 330
#extension GL_ARB_separate_shader_objects : require

#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:sample_lightmap.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
#if defined(OVERWORLD) || defined(NETHER)
layout(location = 3) in ivec2 UV1;
#endif
layout(location = 4) in ivec2 UV2;
#if defined(OVERWORLD) || defined(NETHER)
layout(location = 5) in vec3 Normal;
#endif

uniform sampler2D Sampler2;

layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
layout(location = 2) out vec4 vertexColor;
layout(location = 3) out vec2 texCoord0;
…（body 一行未改）

layout(location = 0) out vec4 fragColor;   // fsh
```

`glowing_shader` 的 6 个 varying 用 0–5 连续编号，vsh/fsh 对齐（`normal` 在 fsh 里仍然声明但不用，
保持接口形状不变）。**数学、discard、fog 调用全部原样**，只加限定符。

> 一处**等价替换**要记下来：`glowing_shader.vsh` 原来用
> `lightMapColor = texelFetch(Sampler2, UV2 / 16, 0);`（1.21 的 block.vsh 写法），
> 改成 26.3 vanilla 的 `lightMapColor = sample_lightmap(Sampler2, UV2);`。
> 两者在 1.21 就是同一套 lightmap 采样的两种写法（`sample_lightmap` = `texture(uv/256 + 半texel)`，
> `texelFetch(uv/16)` = 同一格），26.3 里**所有** vanilla shader 都用 `sample_lightmap`。
> `ponder:entity_block.vsh` 本来就用的是 `sample_lightmap`，所以两边现在一致。

### 3.3 C 类：`position_color_triangles` 少挂 `DynamicTransforms`（1 条，**必须动 class**）

vanilla 的 `core/position_color.vsh` 第 7–8 行 `#include <minecraft:dynamictransforms.glsl>` +
第 18 行 `gl_Position = ProjMat * ModelViewMat * …`，fsh 第 39 行 `color *= ColorModulator;`
⇒ 它**同时**要 `Projection` 和 `DynamicTransforms`。

而 `PonderRenderPipelines.<clinit>` 给它挂的是 `GLOBALS_SNIPPET` + `PROJECTION`：

```
733: getstatic BindGroupLayouts.PROJECTION
736: invokevirtual RenderPipeline$Builder.withBindGroupLayout(BindGroupLayout)Builder
739: ldc "core/position_color"          <- 插入点：此处栈上就是 builder
742: invokevirtual RenderPipeline$Builder.withVertexShader(String)Builder
```

`position_color` 是 **vanilla 的** shader（`minecraft:core/position_color`），别的 pipeline 也在用，
**不能改资源**（改了对全游戏生效）；这个 pipeline 又不能删（ponder 三角形渲染要用）。
所以唯一的修法是给这一条 builder 链补一个 bind group layout —— **+2 条直线指令**：

```
+ getstatic     BindGroupLayouts.DYNAMIC_TRANSFORMS : Lcom/mojang/renderpearl/api/pipeline/BindGroupLayout;
+ invokevirtual RenderPipeline$Builder.withBindGroupLayout (L…BindGroupLayout;)L…Builder;
```

栈形状 `[builder] → [builder]` 不变、无分支目标移动、无帧变化。

### 3.4 D 类（本轮顺带修，**不属于 shader 族**）：`SceneRenderer` 的 `DynamicUniforms`

只有真的把 PonderUI 打开才会撞到（§9）：26.3 把
`net.minecraft.client.renderer.DynamicUniforms` 改名成 `DynamicGpuData`，
`RenderSystem.getDynamicUniforms()` 的**返回类型**跟着变，于是
`SceneRenderer.prepare` 第 81 行 `NoSuchMethodError: 'DynamicUniforms RenderSystem.getDynamicUniforms()'`。
替代类上有一模一样的方法：

```
old: RenderSystem.getDynamicUniforms()LDynamicUniforms;
     DynamicUniforms.writeTransform(Lorg/joml/Matrix4f;)Lcom/mojang/renderpearl/api/buffers/GpuBufferSlice;
new: RenderSystem.getDynamicUniforms()LDynamicGpuData;
     DynamicGpuData.writeTransform(Lorg/joml/Matrix4f;)Lcom/mojang/renderpearl/api/buffers/GpuBufferSlice;
```

⇒ 纯 owner/descriptor 重定向，指令一条不多一条不少、栈不变。
全 jar 只有这 **1 个类**引用 `DynamicUniforms`（逐常量池扫过），所以改动面封闭。

**为什么这个也一起交付**：它是「ponder 场景真的开始画」路上的**前置**（不修就永远到不了 §9 的断点），
而修法比改一个常量还小、且已逐指令验证。若只想保留纯 shader 版本，回滚方法是
`g18/out-jar/create-r2.jar`（= 只有 shader + `PonderRenderPipelines`），见 §12。

---

## 4. 改动清单（交付件里只这 6 个 entry 变了）

| entry | 改前 | 改后 | 性质 |
|---|---|---|---|
| `assets/ponder/shaders/entity_block.vsh` | 1255 B | 1462 B | 资源 |
| `assets/ponder/shaders/entity_block.fsh` | 578 B | 710 B | 资源 |
| `assets/create/shaders/core/glowing_shader.vsh` | 799 B | 1081 B | 资源 |
| `assets/create/shaders/core/glowing_shader.fsh` | 611 B | 784 B | 资源 |
| `com/zurrtum/create/client/catnip/render/PonderRenderPipelines.class` | 8066 B | 7984 B | +2 指令（`withBindGroupLayout(DYNAMIC_TRANSFORMS)`） |
| `com/zurrtum/create/client/ponder/foundation/render/SceneRenderer.class` | 13949 B | 13947 B | 2 处 method-ref 重定向 |

jar 级证明（`_jar_diff.py`）：

```
entries: A=14336 B=14336
only in A (0):   only in B (0):
differing entries (6):          <- 上面这 6 个，其余 14330 个 entry 内容逐字节相同
```

---

## 5. 逐类验证

### 5.1 指令级（`_instr_cmp.py`，去掉偏移与 `#nnn` 后逐行 diff）

`PonderRenderPipelines`：`<clinit>` **只多 2 行**（就是 §3.3 那对），其余 2 个方法逐指令相同。

```
DIFF  static {};
   @@ -321,2 +321,4 @@
    invokevirtual … withBindGroupLayout:(L…BindGroupLayout;)L…Builder;
   +getstatic … BindGroupLayouts.DYNAMIC_TRANSFORMS:…
   +invokevirtual … withBindGroupLayout:(L…BindGroupLayout;)L…Builder;
    ldc … String core/position_color
```

`SceneRenderer`：10 个方法里 9 个**逐指令相同**，`prepare(...)` **只换 2 行**（同一位置、同一栈）：

```
-invokestatic  RenderSystem.getDynamicUniforms:()Lnet/minecraft/client/renderer/DynamicUniforms;
+invokestatic  RenderSystem.getDynamicUniforms:()Lnet/minecraft/client/renderer/DynamicGpuData;
-invokevirtual DynamicUniforms.writeTransform:(Lorg/joml/Matrix4f;)L…GpuBufferSlice;
+invokevirtual DynamicGpuData.writeTransform:(Lorg/joml/Matrix4f;)L…GpuBufferSlice;
```

### 5.2 字节码校验器（`CheckClassAdapter`，含 joml + fastutil + 26.3 + 交付 jar）

```
old PonderRenderPipelines: (无输出)     new: (无输出)
old SceneRenderer:         (无输出)     new: (无输出)
```

（第一次跑 old 报 `ClassNotFoundException: org.joml.Vector3fc` / `it.unimi.dsi.fastutil.…` 是
**classpath 不全**，补上 joml-1.10.5 + fastutil-8.5.12 后 old/new 都无输出 = 都通过。）

### 5.3 GLSL 侧

没有本地 glslang，**用 26.3 自己的 renderpearl 编译器验**（每次真启动到标题即触发资源重载）：

| 轮次 | jar 内容 | `Couldn't compile pipeline` |
|---|---|---|
| 0（旧交付件 `F950B952…`） | 原样 | **15** |
| r1 | 只换 4 个 shader | **1**（只剩 `position_color_triangles`） |
| r2 | r1 + `PonderRenderPipelines` | **0** |
| r5（= 交付件） | r2 + `SceneRenderer` | **0** |

r1 的日志原文（`evidence/r1-title-latest.log`）——14 条一起消失，只剩那条 Java 侧的：

```
[15:16:41] [Worker-Main-2/ERROR]: Couldn't compile pipeline (ponder:pipeline/position_color_triangles):
com.mojang.renderpearl.util.ShaderCompileException: Unable to find shader defined uniform (DynamicTransforms)
[15:16:43] [Render thread/WARN]: Failed to load optional shader programs:
 - ponder:pipeline/position_color_triangles
```

r2 的日志（`evidence/r2-title-latest.log`）：

```
compile=0  moj_import=0  invalid_directive=0  optional=0
```

---

## 6. A/B 汇总（每次都是**全新存档副本**；`watch` 未触碰）

| 运行 | jar | 结果 |
|---|---|---|
| 旧件标题/世界（g16 既有证据） | `F950B952…` | `TITLE_SCREEN_OK` / `WORLD_OK`，`Couldn't compile pipeline` **15** |
| r1 标题（`game-r1`） | shader only | `TITLE_SCREEN_OK` 29.1 s，**1** |
| r2 标题（`game-r2`） | +`PonderRenderPipelines` | `TITLE_SCREEN_OK` 28.2 s，**0** |
| r4 世界 + `/ponder create:basin`（`game-r4`） | r2 | PonderUI 打开 → `NoSuchMethodError getDynamicUniforms()` @ `SceneRenderer.prepare:81` |
| r5 世界 + `/ponder create:basin`（`game-r5`） | r2 + `SceneRenderer` | PonderUI 打开 → `NoSuchMethodError executeSolid()` @ `SceneRenderer.prepare:83`（下一族） |
| **交付件标题**（`g18/final`） | `6DD6B46F…` | **`TITLE_SCREEN_OK` 37.4 s** |
| **交付件世界**（`g18/final`, `lm-final-w2`） | `6DD6B46F…` | **`WORLD_OK` 56.0 s**，`joined=True marker_seen=True` |

交付件世界日志计数（`evidence/final-world2-latest.log`）：

```
Couldn't compile pipeline: 0     moj_import: 0            invalid directive: 0
ShaderCompileException: 0        Failed to load optional: 0
Registry loading errors: 0       NoSuchMethodError: 0      NoSuchFieldError: 0
ExceptionInInitializerError: 0   NullPointerException: 0   ReportedException: 0
Exception while updating neighbours: 0
```

---

## 7. 交付

| 文件 | 备份 | 原 SHA-256 | 新 SHA-256 |
|---|---|---|---|
| `work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar` | **`.bak-shader`**（19,639,144 B） | `F950B9529AAF732BEADC2A626D7B916773518BC3B7A8053C0226343A234F6E0E` | **`6DD6B46F20CD665F00753E3EBF9890EC121EEC9918E042C073C1AAEF1CB6ED9B`**（19,639,341 B / 14336 entries） |

`mods-stable` = **71 jar**（改已有 jar，没加新 jar）。
`.bak-ponder` / `.bak-landmine` / `.bak-landmine-glint` / `.bak-itemhelper` / `.bak-clock` **均未覆盖**。

---

## 8. 重扫（`python tools/scan_landmines.py --only create-fly`）

| 指标 | 改前（`g16/scan_after.md`） | 改后（`g18/scan_after.md`） |
|---|---|---|
| 原始指令级发现 | 1123 | **1120** |
| 去重归组 | 275 | **272** |
| 地雷总数 | 83 | **81** |
| 高危 / 中危 / 低危 | 27 / 16 / 40 | **27 / 14 / 40** |

组级 diff（`_scandiff.py`）：**只少 2 组，新增 0 组** —— `getDynamicUniforms`、`writeTransform`（就是 §3.4 修的）。
上一轮修的 `RenderTypes.glint*` / `InterpolationHandler` / `OutputTarget` 仍然 0 命中（没被碰坏）。
shader 编译错误本来就不在地雷扫描范围（它扫字节码，不扫 GLSL）。

---

## 9. Ponder 真机能画到哪一层（如实）

探针 `g18/probe/sky262lm-probe.jar` 的 `phase=ponderscene`（**一次性，不进交付**）做的是真事：

1. 反射 `PonderIndex.getSceneAccess()` → `doScenesExistForId`，在 49 个候选 id 里确认 **35 个真实存在**；
2. 用 create 自己的**客户端命令**打开场景：`/ponder create:basin`
   （注意：create 6 的命令是 `/ponder <identifier>`，参数名叫 `scene` 但不是 `scene` 字面量 ——
   写成 `/ponder scene create:basin` 会被解析成 id=`minecraft:scene` 并报
   `Could not find ponder scenes for item: minecraft:scene`，这是我踩过的坑）；
3. 等 `mc.gui.screen()` 变成 `PonderUI`，再保持 ~12 s 让渲染线程真的去画。

### 9.1 r4（r2 件，只有 shader + 管线）

```
[sky262lm] SCENE_CMD /ponder create:basin
[sky262lm] SCENE_STATE held=1 screen=com.zurrtum.create.client.ponder.foundation.ui.PonderUI   <- UI 真的开了
[Render thread/ERROR]: Unreported exception thrown!
java.lang.NoSuchMethodError: 'net.minecraft.client.renderer.DynamicUniforms com.mojang.blaze3d.systems.RenderSystem.getDynamicUniforms()'
    at …ponder.foundation.render.SceneRenderer.prepare(SceneRenderer.java:81)
    at …net.minecraft.client.gui.render.GuiRenderer.preparePictureInPictureState(GuiRenderer.java:315)
```

### 9.2 r5（交付件）

```
java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.feature.FeatureRenderDispatcher$PreparedFrame.executeSolid()'
    at …ponder.foundation.render.SceneRenderer.prepare(SceneRenderer.java:83)     <- 前进了 2 行
```

26.3 的 `PreparedFrame` 里这 5 个方法**名字还在，但都要一个 `RenderPass` 参数**：

```
executeSolid(RenderPass) / executeTranslucent(RenderPass) / executeWaterMask(RenderPass)
executeOit(OitStage, RenderPass) / executeOutline(RenderPass) /
executeTranslucentAfterTerrain(RenderPass) / executeSeeThrough(RenderPass) / executeAlwaysOnTop(RenderPass)
```

而 `SceneRenderer.prepare(SceneRenderState, GuiRenderState, FeatureRenderDispatcher, int)` **拿不到**
`RenderPass`（它由 `GuiRenderer`/`CommandEncoder` 那一层持有）⇒ 这不是改名，
是 **26.3 的 phase/RenderPass 模型要真接进去**，属于设计级改动，本轮不做。

### 9.3 所以「能不能画」

| 层 | 状态 |
|---|---|
| 15 条管线编译 | ✅ **归零**（本轮交付） |
| `PonderRenderTypes` / `EntityBlockRenderType` 建对象 | ✅ 上一轮已修（`PONDER_CLINIT_OK`，15/15 字段非 null） |
| PonderUI 能打开、场景渲染流程开始跑 | ✅ **本轮实测**（`screen=PonderUI`，栈进到 `GuiRenderer.preparePictureInPictureState → SceneRenderer.prepare`） |
| 把几何体提交进 26.3 的渲染相位 | ❌ 卡在 `PreparedFrame.execute*(RenderPass)`（§9.2），需要设计级移植 |
| 屏幕上有 3D 动画 | ❌ 未验到（被上一行挡住）；再往后还有已知的地雷 #7 `MutableQuadView.diffuseShade()` |
| 截图 | 无（没有画面可截） |

**明确一句：本轮交付不等于「Ponder 动画已经能看见」**，只等于「着色器这一族修完，断点往后推了两层」。

---

## 10. 已知限制

- 没有重跑 107 mod 全量矩阵，只跑 `mods-stable` 71 jar + 4 次 A/B + 2 次探针世界。
- 没有重编 create 工程（交付件是字节码补丁，整包重编会覆盖 26.3 资源路径/垫片）。
- `glowing_shader` 的 lightmap 采样从 `texelFetch(UV2/16)` 换成 `sample_lightmap(Sampler2, UV2)`（§3.2 末尾说明，等价）。
- `position_color_triangles` 补 `DynamicTransforms` 之后**没有单独验过它的画面**（ponder 三角形渲染路径还没跑到），
  只验到「管线编译通过、注册进 `PIPELINES_BY_LOCATION`」。
- `g18/probe/sky262lm-probe.jar` 是一次性验收驱动，**不在交付件里**（`mods-stable` 仍 71 jar）。

---

## 11. 下一步建议（按性价比）

1. **`PreparedFrame.execute*(RenderPass)`**：26.3 的相位模型移植。要么在 `SceneRenderer.prepare` 里拿到
   `GuiRenderer` 那一层已经打开的 `RenderPass`（需要扩签名/换调用点），要么让 ponder 场景按 26.3 的
   `SubmitNodeStorage` 提交而不是自己 `execute*`。这是「能看见」的最后一层。
2. **`MutableQuadView.diffuseShade()`**（地雷 #7）：在 1 之后就会撞上，FRAPI 17 换成 `ShadeMode`。
3. `position_color_triangles` 的画面验收（三角形/GUI 元素）。

---

## 12. 复现命令

```powershell
$base = "C:\Users\95959\OneDrive\Desktop\Work\skylands-262"
$g18  = "$base\work\run26\port\g18"
$name = "create-fly-26.2-6.0.9-2-26.3-patched.jar"
$jar  = "$base\work\run26\mods-stable\$name"
$asm  = "$env:APPDATA\.minecraft\libraries\org\ow2\asm\asm\9.10.1\asm-9.10.1.jar"
$javac= "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\javac.exe"
$java = "$env:APPDATA\.minecraft\runtime\java-runtime-epsilon\bin\java.exe"

# 1) 换 4 个 shader（源 jar 用交付前的 .bak-shader）
python "$g18\_patch_jar.py" "$jar.bak-shader" "$g18\out-jar\r1.jar" `
  "assets/ponder/shaders/entity_block.vsh=$g18\shaders_new\assets\ponder\shaders\entity_block.vsh" `
  "assets/ponder/shaders/entity_block.fsh=$g18\shaders_new\assets\ponder\shaders\entity_block.fsh" `
  "assets/create/shaders/core/glowing_shader.vsh=$g18\shaders_new\assets\create\shaders\core\glowing_shader.vsh" `
  "assets/create/shaders/core/glowing_shader.fsh=$g18\shaders_new\assets\create\shaders\core\glowing_shader.fsh"

# 2) 两个 ASM 补丁（先取类，再改，再比对）
#    PonderRenderPipelines: withBindGroupLayout(DYNAMIC_TRANSFORMS)
& $javac -cp $asm -d "$g18\asm\out" "$g18\asm\PatchPipelines.java"
& $java -cp "$g18\asm\out;$asm" PatchPipelines "$g18\oldcls\…\PonderRenderPipelines.class" "$g18\newcls\…\PonderRenderPipelines.class"
#    SceneRenderer: DynamicUniforms → DynamicGpuData
& $javac -cp $asm -d "$g18\asm\out" "$g18\asm\PatchDynamicUniforms.java"
& $java -cp "$g18\asm\out;$asm" PatchDynamicUniforms "$g18\oldcls\…\SceneRenderer.class" "$g18\newcls\…\SceneRenderer.class"

# 3) 打进 jar + 逐 entry 比对
python "$g18\_patch_jar.py" "$g18\out-jar\r1.jar" "$g18\out-jar\r5.jar" `
  "com/…/PonderRenderPipelines.class=$g18\newcls\…\PonderRenderPipelines.class" `
  "com/…/SceneRenderer.class=$g18\newcls\…\SceneRenderer.class"
python "$g18\_jar_diff.py" "$g18\out-jar\r5.jar" "$jar.bak-shader"

# 4) 标题 / 世界（每次全新存档副本）
python tools\launch26\launch.py --game-dir "$g18\game-r2" --mods "$g18\mods-r2" --watch-title --timeout 300
python "$g18\_mkworld.py" --game "$g18\final" --template "$base\work\run26\vfix-saves\placed" --name lm-x --phase noop
python "$g18\_run_world.py" --game-dir "$g18\final" --mods "$base\work\run26\mods-stable" --world lm-x --tag x --marker "logged in with entity id" --timeout 300

# 5) Ponder 真机探针（一次性，不进交付）
python "$g18\_build_probe.py"
python "$g18\_mkmods.py" "$g18\out-jar\r5.jar" "$g18\mods-r5"
python "$g18\_mkworld.py" --game "$g18\game-r5" --template "$base\work\run26\vfix-saves\placed" --name lm-r5 --phase ponderscene
python "$g18\_run_world.py" --game-dir "$g18\game-r5" --mods "$g18\mods-r5" --world lm-r5 --tag scene-r5 --timeout 300

# 6) 只保留 shader 版本的等价物（回滚 SceneRenderer 用）
#    $g18\out-jar\create-r2.jar
```
