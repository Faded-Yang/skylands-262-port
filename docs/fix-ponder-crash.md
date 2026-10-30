# fix-ponder-crash —— 打开「思索」(Ponder) 崩：NoSuchMethodError PreparedFrame.executeSolid()

> **状态：候选件已构建 + 静态/装载证据链 PASS；游戏内 A/B 未实测（由 task-18 interact-probe 做）。**
> 改动：create-fly **1 个 class**（SceneRenderer，5 处 × 3 字节），其余 14,335 个 entry **逐字节不变**。
> 结果：**硬崩消掉**（prepare 不再调用 26.3 已删的 5 个无参 execute*()）；
> **Ponder 场景几何体仍然画不出来**（既有损失，R403 起就有；本轮把「崩」降回「看不见动画」）。
> 真实渲染的入口已定位（见 §7），但需要方法体重写 + 真机 A/B，本轮**没做**。

- 任务板：task-15
- 关联文档：docs/HANDOFF.md §7.1（「Ponder 教学动画画不出来」）、docs/fix-renderpass.md（Ponder 管线的 color target）
- 交付目录：work/run26/port/g31/（out/ 候选件、out/evidence/ 证据、stage/ 两组 A/B、_build_ponderfix.py / _smoke.py / _stage.py）

---

## 0. 交付件

| 项 | 路径 / 值 | size | SHA-256 |
|---|---|---|---|
| **候选（PRIME）** | work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix.jar | 19,639,158 B | 4dad19af113ce4fd3f149f4d602fe54895d4f7fed56318ed50584ade0b16b008 |
| 基线（只读，**本轮未修改**） | work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar | 19,639,168 B | 64b68869181c19ad42b540af7fcc30d2b19333063a7177c90cef4864802ab28a |
| 被改的 class（原） | com/zurrtum/create/client/ponder/foundation/render/SceneRenderer.class | 13,947 B | 816a9346c23b790a1526b4df189a24d609f1b30c43096a74bb7656075419e627 |
| 被改的 class（新） | 同上（**大小不变**） | 13,947 B | 02069fb43b1b27b8ccddd2fa8d1b1f3505297d30a61788776ec67663930b4cb3 |
| A/B staging（硬链接） | work/run26/port/g31/stage/mods-baseline / mods-candidate | 各 71 jar / 137.3 MB | 见 stage/manifest.json |

- **promote 时把候选重命名为 create-fly-26.2-6.0.9-2-26.3-patched.jar**（fabric.mod.json 未改：id=create / version=6.0.9-2，同槽位替换）。
- **基线声明（硬校验）**：本补丁基于 create-fly 64b68869…28a / **19,639,168 B** / mtime 2026-10-18 19:36:16
  （= R407 swing+GLFW 合并件，见 docs/fix-valuesettings.md §0.1）。_build_ponderfix.py 开头硬校验该 SHA 与大小，
  变了就 SystemExit 拒绝打补丁。
- 构建/交付期间 **mods-stable 与 watch 都没被写**：watch 只**读**了 crash-report（Copy-Item 复制到 g31 evidence，
  SHA 与原文件一致：8BEBD1E211552FE30FE8520435C23CED8082BF4859D6097218FC88D95A6FBE98）。

### 0.1 staging（给 task-18 的两组目录，硬链接建，非复制）

| 目录 | 内容 | create-fly |
|---|---|---|
| g31/stage/mods-baseline | 71 jar，其余 70 个与 mods-stable 逐字节相同（硬链接） | 64b68869… / 19,639,168 B（会崩的基线） |
| g31/stage/mods-candidate | 同上 70 个硬链接 + 换入候选 | 4dad19af… / 19,639,158 B |

_stage.py 逐文件核对 SHA 后才算建好；manifest.json 记录两个目录的 create-fly SHA 与总大小。
**A/B 记得用全新存档副本**（同一存档被试过一次会变实验性 ⇒ 假超时）。

---

## 1. 崩溃现场（用户实测，2026-10-18 20:13:36）

- crash-report：work/run26/watch/crash-reports/crash-2026-10-18_20.13.36-client.txt（只读复制：
  g31/out/evidence/00_crash-2026-10-18_20.13.36-client.txt）
- 触发：**按住小键盘 + 打开「思索」（Ponder）**（Create 的 Ponder 面板，任何场景）

~~~
java.lang.NoSuchMethodError: 'void net.minecraft.client.renderer.feature.FeatureRenderDispatcher$PreparedFrame.executeSolid()'
	at com.zurrtum.create.client.ponder.foundation.render.SceneRenderer.prepare(SceneRenderer.java:83)
	at com.zurrtum.create.client.ponder.foundation.render.SceneRenderer.prepare(SceneRenderer.java:33)   <- 桥方法
	at net.minecraft.client.gui.render.GuiRenderer.preparePictureInPictureState(GuiRenderer.java:315)
	at net.minecraft.client.gui.render.GuiRenderer.preparePictureInPicture(GuiRenderer.java:307)
	at net.minecraft.client.gui.render.GuiRenderer.prepare(GuiRenderer.java:179)
	at net.minecraft.client.gui.render.GuiRenderer.render(GuiRenderer.java)
~~~

SceneRenderer.java:83 对应的正是 javap 里 prepare(SceneRenderState,GuiRenderState,FeatureRenderDispatcher,int)
的 **offset 268**（invokevirtual PreparedFrame.executeSolid:()V）；:33 是同文件的桥方法
prepare(PictureInPictureRenderState,…)（纯 checkcast + 转发）。

---

## 2. 根因（javap 实测）

### 2.1 26.3 的 PreparedFrame 把 8 个 execute 全改成要 RenderPass

~~~
$ javap -p -cp 26.3.jar 'net.minecraft.client.renderer.feature.FeatureRenderDispatcher$PreparedFrame'
  public void executeSolid(com.mojang.renderpearl.api.commands.RenderPass);
  public void executeTranslucent(RenderPass);
  public void executeWaterMask(RenderPass);
  public void executeOit(OitStage, RenderPass);
  public void executeOutline(RenderPass);
  public void executeTranslucentAfterTerrain(RenderPass);
  public void executeSeeThrough(RenderPass);
  public void executeAlwaysOnTop(RenderPass);
  public void close();
  public boolean isEmpty(); hasAnyOutline(); hasAnyWaterMask(); hasAnySeeThrough();
~~~

**没有任何无参重载**。而 create-fly 的 SceneRenderer.prepare 连调 5 个无参版本：

~~~
266: aload 13
268: invokevirtual #265  PreparedFrame.executeSolid:()V            <- 崩在这（source line 83）
271: aload 13
273: invokevirtual #268  PreparedFrame.executeTranslucent:()V
276: aload 13
278: invokevirtual #271  PreparedFrame.executeOutline:()V
281: aload 13
283: invokevirtual #274  PreparedFrame.executeTranslucentAfterTerrain:()V
286: aload 13
288: invokevirtual #277  PreparedFrame.executeAlwaysOnTop:()V
291: aload 13
293: ifnull 331
296: aload 13 / 298: invokevirtual #278  PreparedFrame.close:()V    <- close() 无参，仍存在
~~~

⇒ **只 NOP 掉 executeSolid 不够**：下一行 executeTranslucent() 会立刻抛同一个错。5 处必须一起处理。

### 2.2 prepare 阶段拿不到 RenderPass

GuiRenderer.preparePictureInPictureState(T,int) 只把 3 个参数转给渲染器，**没有 pass**：

~~~
19: aload_3                       // PictureInPictureRenderer
24: aload_1                       // state
26: getfield  GuiRenderer.renderState           // GuiRenderState
30: getfield  GuiRenderer.featureRenderDispatcher
33: iload_2                       // scaleFactor
34: invokevirtual PictureInPictureRenderer.prepare:(PictureInPictureRenderState;GuiRenderState;FeatureRenderDispatcher;I)V
~~~

RenderPass 是**后面**才被创建的：CommandEncoder.createRenderPass(...) 只出现在
PictureInPictureRenderer.prepare（原版那条）与 GuiRenderer.executeDraw(GuiRenderer$Draw, RenderPass) 里，
prepare 阶段确实拿不到。⇒ **不能在 prepare 里把 frame 就地执行**（除非自己建 pass，见 §7 Route 2）。

### 2.3 为什么 create-fly 会写成这样（移植痕迹）

SceneRenderer 里 26.3 的三个钩子都已实现，但**语义被拆错了**：

| 方法 | 现状（javap） |
|---|---|
| renderToTexture(SceneRenderState, PoseStack, SubmitNodeCollector) | **空方法**（0: return）——这是 26.3 原版 PiP 渲染器用来「提交几何体」的钩子，被留空 |
| prepare(SceneRenderState, GuiRenderState, FeatureRenderDispatcher, int) | 把 26.2 的整套流程搬进来：自建 GpuTexture（create/catnip/gui/render/GpuTexture）→ 设灯光 → renderScene(...) 提交 → prepareFrame → **5 个无参 execute** → close → 手动 blit 自己的纹理 |
| prepare(PictureInPictureRenderState,…) / renderToTexture(PictureInPictureRenderState,…) | 纯桥方法（checkcast + 转发） |

也就是说：**26.3 的渲染期钩子（renderToTexture + 原版 prepare 自建的 RenderPass）没被用上，26.2 的立即执行流程被照搬**，
而 26.2 的无参 execute*() 在 26.3 已删。这是「搬流程没搬相位」的典型。

另外一条**上游半成品痕迹**（不是本轮原因，但和 §7 路线有关）：GpuTexture.prepare 会把
dev/eriksonn/aeronautics/compat/RenderBitsBridge.outputColorTextureOverride / outputDepthTextureOverride
设成 Ponder 自己的 color/depth view（GpuTexture.clear 再置空）。全 71 jar 扫描：**读这两个字段的只有
QuadParticleFeatureRendererMixin 的两个私有方法 getColorTexture/getDepthTexture**（粒子渲染用它取目标纹理），
**没有任何地方用它们建 RenderPass**。⇒ 这是一座「备好了纹理、没接上 pass」的桥。

---

## 3. 修法（最低目标：不崩）

**字节级 patch，单 class，5 处等长替换**：

| javap off | 原 5 字节 | 新 5 字节 | 说明 |
|---|---|---|---|
| 266..270 | 19 0d b6 01 09（aload 13; invokevirtual executeSolid） | 19 0d 57 00 00（aload 13; **pop**; nop; nop） | 帧对象推上栈后丢掉，净栈 0 |
| 271..275 | 19 0d b6 01 0c | 19 0d 57 00 00 | executeTranslucent |
| 276..280 | 19 0d b6 01 0f | 19 0d 57 00 00 | executeOutline |
| 281..285 | 19 0d b6 01 12 | 19 0d 57 00 00 | executeTranslucentAfterTerrain |
| 286..290 | 19 0d b6 01 15 | 19 0d 57 00 00 | executeAlwaysOnTop |

**为什么安全**

- 每处 aload 13 → invokevirtual ()V 的净栈变化是 **0**；换成 aload 13 → pop 后仍是 **0** ⇒ 后续所有
  StackMapTable 帧（122 行）**逐一相同**，分支目标（291/293/301/304/328/331）位移 0。
- 只改 3 字节/处（b6 xx xx → 57 00 00），指令总长、offsets、LineNumberTable 全不变。
- 常量池**故意不删**：5 个 Methodref 变成「死引用」，永不解析 ⇒ 不会 NoSuchMethodError（JVM 只在执行时解析）。
- close()（仍在 26.3）保留，prepareFrame 照常调用：等价于「把场景提交进一个 frame，然后直接释放」。
  renderScene(...) 已提交的节点被丢弃 ⇒ **场景区不画东西**（既有损失），但 UI/文字/交互不受影响。

同一处**不做**的事（以及为什么）：

- 不删/改 renderToTexture、不删 prepare：那是 §7 的渲染路线，需要方法体重写 + 真机 A/B，本轮不动。
- 不逐处替换成「真 executeSolid(RenderPass)」：prepare 没有 pass（§2.2），除非自建（§7 Route 2）。

---

## 4. 证据链（全部在 g31/out/evidence/）

| # | 证据 | 结论 |
|---|---|---|
| 00 | 00_crash-2026-10-18_20.13.36-client.txt | 用户实测崩溃原文；SHA 与 watch 原件一致 |
| 01 | 01_jar_audit.txt | 基线 SHA/大小**硬校验通过**；entry 14,336→14,336；**内容变化 entry 恰好 1 个**；**raw deflate 流 14,335/14,336 逐字节相同**；testzip() = None；无签名文件 |
| 02 | 02_javap_old_c.txt / 02_javap_new_c.txt | 前后完整 javap -p -c |
| 03 | 03_javap_diff.txt | unified diff **只删 5 行 invokevirtual、只加 15 行 pop+nop+nop**，无其它差异 |
| 04 | 04_javap_v_old.txt / _new.txt | StackMapTable **122 行完全相同**；LineNumberTable **171 条完全相同** |
| 05 | 05_clsdiff.txt | 成员数 old=15 new=15 **SAME**；changed methods **1 / 15**（只有 prepare(SceneRenderState,…)） |
| 06 | 07_smoke_{baseline,candidate,control}.txt | 见 §4.1（类加载冒烟 + 代码级链接审计 + 反向对照） |
| — | _smoke.py / smoke/PonderAudit.java | 冒烟工具源码（ASM 9.10.1） |

### 4.1 类加载冒烟（不是「javap 看着对」——真跑 JVM 校验器）

Class.forName(..., initialize=true) 会**强制链接（= 全类字节码校验）后执行 clinit**。
classpath = create-fly（目标件）+ 26.3.jar + 288 个 .minecraft/libraries jar + 70 个 mods jar。

| 用例 | 结果 |
|---|---|
| **baseline** | CLASS_INIT_OK；代码级链接审计：used_refs=83 / ok=78 / **member_missing=5**，恰好是 5 个 PreparedFrame.execute*()V，owner_not_found=0 |
| **candidate** | CLASS_INIT_OK（校验器通过）；used_refs=78 / ok=78 / **member_missing=0**，owner_not_found=0 |
| **control**（把候选第一个 pop 改回 nop，制造 +1 栈） | **CLASS_INIT_FAILED java.lang.VerifyError: Inconsistent stackmap frames at branch target 331** |

**control 是关键**：它证明这套冒烟**真的在跑 JVM 校验器**（对照用例必须失败），不是「加载一下就 OK」。
同时 control 的字节码 dump 里能看到候选的 5 处 19 0d 57 00 00，而 baseline 的 5 个 Methodref 在代码里已消失。

> 链接审计是**代码级**（ASM 遍历字节码指令，不扫常量池）：常量池里的 5 个 Methodref 是故意留下的死引用，
> 扫常量池会误报；反射解析沿真实父类/接口链走，避免把 Level.dimensionType() 这类继承成员误判缺失。
> 结果说明：**prepare 里 crash 之后的所有调用（close → ponder$updateTransforms(null) → resetParticles →
> Lighting.updateLevel → popPose → GpuTexture.clear → BlitRenderState.<init> → addBlitToCurrentLayer）
> 在 26.3 运行期都能解析**，补丁不会把崩溃推迟到后面几行。

---

## 5. 降级（写进交付说明/台账时用）

| 项 | 修前 | 修后 |
|---|---|---|
| 打开 Ponder | **客户端硬崩**（crash-report） | 不崩，Ponder 面板可开 |
| Ponder 场景几何体（方块/装置动画） | 画不出来（R403 起既有损失） | **仍然画不出来** |
| Ponder 文字/UI/翻页/交互 | （崩，看不到） | 跟随 GUI 正常（理论推断，**未实测**） |
| 场景区域显示 | 崩 | 显示 GuiRenderer.CLEAR_COLOR 清屏色（GpuTexture.prepare 清过、随后 blit 该纹理；可能是一块纯色/透明区）。**未实测** |

即：**「崩」→「既有可见损失」**，没有新增降级项。

---

## 6. A/B 口径（task-18 interact-probe）

**两组 staging 已建好，直接喂 tools/launch26/launch.py --mods：**

~~~
# 基线（应复现崩溃）
python tools\launch26\launch.py --game-dir <全新副本> --mods work\run26\port\g31\stage\mods-baseline --timeout 300
# 候选（应不崩）
python tools\launch26\launch.py --game-dir <另一个全新副本> --mods work\run26\port\g31\stage\mods-candidate --timeout 300
~~~

**操作**：进世界 → 按住小键盘（复现用户输入组合）→ 打开 Ponder（Create 物品/装置提示的「思索」按钮，或任意 Ponder 场景）。

**判定字段**

| 判定 | 基线（mods-baseline） | 候选（mods-candidate） |
|---|---|---|
| crash-report 新增 | **1 个**，NoSuchMethodError ... PreparedFrame.executeSolid() @ SceneRenderer.prepare(SceneRenderer.java:83) | **0 个** |
| latest.log grep NoSuchMethodError prepare(Ponder 前缀) | 命中 | **不命中** |
| Ponder 面板 | 打不开（已崩） | 打开，文字/按钮/翻页可见、可点 |
| 场景区域 | — | 纯色/空白（**这是预期**，不是失败；见 §5） |
| 关闭 Ponder 后继续玩 30 s | — | 无新异常、无 crash-report |

⚠ **两个容易造成假阳性的点**：
1. **先松开小键盘再点 Ponder** —— 按住不放时其它交互（shift 选物/滚轮）会污染判定；用户是「按住 + 打开」两个动作，崩溃点是 **Ponder prepare**，不依赖按键仍按住。
2. 一定要用**全新存档副本**；同存档被试过会变实验性（台账硬规则）。

---

## 7. 「真正把 Ponder 画面画出来」——入口已定位，本轮**没做**

### 7.1 26.3 原版就是「prepare 里建 pass，再带 pass 执行」（javap -c 实测）

PictureInPictureRenderer.prepare(...)（26.3 原版）自己做完了全套，**包括建 RenderPass**：

~~~
 36..107  prepareTexturesAndProjection(...)        // 建 RGBA8 + D32 纹理、清屏、setOrtho、setProjectionMatrix
110..146  RenderSystem.getModelViewStack().pushMatrix()
121..170  PoseStack: translate(w/2, translateY, 0) / scale(s, s, -s)
173..181  renderToTexture(state, poseStack, this.submitNodeStorage)      <-- 提交几何体的钩子
184..189  FeatureRenderDispatcher.prepareFrame(this.submitNodeStorage)   -> PreparedFrame
194..221  device.createCommandEncoder().createRenderPass("Picture in picture",
              textureView, Optional.empty(), depthTextureView, OptionalDouble.empty())
228..230  RenderSystem.bindDefaultUniforms(pass)
233..237  FeatureRenderDispatcher.renderAllFeatures(pass, preparedFrame) // 带 pass 执行全部 phase
240..284  pass.close()
284..323  preparedFrame.close()
324..328  popMatrix()
330..335  blitTexture(state, guiRenderState)
~~~

FeatureRenderDispatcher.renderAllFeatures(RenderPass, PreparedFrame) 是 **public static**，javap 里它的体就是：

~~~
executeSolid(pass) -> executeTranslucent(pass) -> executeTranslucentAfterTerrain(pass)
  -> executeSeeThrough(pass) -> executeAlwaysOnTop(pass)
~~~

（注意：**不含** executeOutline / executeWaterMask，这两条由调用方按 hasAnyOutline() / hasAnyWaterMask()
单独执行；Create 老代码用的是 solid/translucent/**outline**/translucentAfterTerrain/alwaysOnTop。）

### 7.2 两条可行路线（都需要方法体级 ASM 重写 + 真机 A/B）

**Route 1（更贴原版语义，推荐）——把 prepare 委托给 super，把提交搬进 renderToTexture**

1. SceneRenderer.prepare(SceneRenderState,…) 的方法体改成 return super.prepare(state, guiRenderState, dispatcher, scale)；
2. renderToTexture(SceneRenderState, PoseStack, SubmitNodeCollector)（现在是空方法）改成 Create 原流程的**提交部分**：
   设 useUiLightmap=false + Lighting.updateBuffer/setupFor → renderScene(mc, collector, this.matrices, scene, partialTicks, w, h, slide, flash)
   → 动态变换（QuadParticleFeatureRenderer.TYPE 的 DynamicTransformsHolder.ponder$updateTransforms）→ resetParticles → 恢复灯光；
3. 原版 prepare 会自己建 pass、调 renderAllFeatures、blit **它自己的纹理**；Create 那套 GpuTexture/TEXTURES
   可以整体不用（renderToTexture 收到的 PoseStack 是原版算好中心/缩放的，是否直接用它、还是用 this.matrices 保持
   26.2 的内部成像假设，需要实测两版对比）。

风险：语义等价性**未验证**（原版 PoseStack 的 translate/scale 与 Create 内部成像的叠加重数）、
QuadParticleFeatureRendererMixin 对 RenderBitsBridge 的依赖是否还需要、Ponder 粒子/OIT 行为。

**Route 2（更小步）——在现有 prepare 里自建 pass，替换那 5 个 execute**

~~~
GpuTexture t = (GpuTexture) 局部 5;                       // 已 prepare 过：纹理已建、已清、ortho 已设
RenderPass pass = RenderSystem.getDevice().createCommandEncoder().createRenderPass(
        () -> "Ponder", t.textureView(), Optional.empty(), t.depthTextureView(), OptionalDouble.empty());
RenderSystem.bindDefaultUniforms(pass);
FeatureRenderDispatcher.renderAllFeatures(pass, frame);    // 全 phase 带 pass 执行
if (frame.hasAnyOutline()) frame.executeOutline(pass);
pass.close();
~~~

这条路线**不用改方法分工**，只把「5 个无参 execute」换成「1 个 pass + renderAllFeatures + close」，
且 GpuTexture 已经有 textureView() / depthTextureView() 公开访问器（javap 实测）。
落地形态建议：把这小段做成 SceneRenderer 里的**新增 private static helper**，5 处调用点里第 1 处换成
invokestatic helper(PreparedFrame)（aload 13; invokestatic 恰好也是 5 字节，仍可等长替换），其余 4 处 aload;pop。
代价：invokedynamic lambda（() -> "Ponder"）要 ASM 生成，或改用已有的 supplier 变通；
RenderBitsBridge 的两个 static override 也可以拿来做参数来源（GpuTexture.prepare 已经在设）。

**本轮不做的理由**：两条路线都是**方法体重写**（不是几十字节的等长替换），且**正确性只能靠真机看画面**。
在「用户现在一开 Ponder 就崩」的前提下，先交付零风险的「不崩」，把渲染作为独立任务（需要 Lead 决定优先级、
interact-probe 出 A/B 画面证据）。

---

## 8. 风险 / 回滚

**风险（已评估）**

| 风险 | 评估 |
|---|---|
| 补丁引入 VerifyError | **已排除**：JVM 校验器实测通过（§4.1），且有反向对照证明冒烟有效 |
| 崩溃被推迟到 prepare 后面几行 | **已排除**（静态）：crash 之后的 12 个调用点全部能解析（链接审计 0 missing）；仍以 A/B 为准 |
| prepareFrame 后不 execute 直接 close 的副作用 | 低：PreparedFrame 是 dispatcher 复用的实例，close 清 groups；不执行不会留下 GPU 资源 |
| GpuTexture/TEXTURES 缓存按 state.id() 增长 | 与补丁无关（原逻辑就有；同一 PiP id 复用） |
| 其它 Ponder 入口（JEI 提示、物品栏悬停等） | 走同一 prepare 路径 ⇒ 同样修好；但**未逐一实测** |

**回滚**

- 候选件是**独立文件**，mods-stable 未动 ⇒ 不 promote 就等于没发生。
- 若 promote 后回滚：换回 .bak-ponder-crash（promote 时对当前件做备份，建议名）+ 重启客户端即可；
  没有数据/存档层改动。

---

## 9. 未实测声明（**别把本文当 A/B 结果**）

- **游戏内行为一律未实测**：本文所有「修后应该怎样」都是**静态推断**，包括「Ponder 面板能开」「场景区是清屏色」。
- 已实测的只有：字节级 diff、JVM 类加载/校验、代码级链接审计、对照用例的 VerifyError。
- 真正的结论以 task-18 的 mods-baseline vs mods-candidate A/B 为准（§6 口径）。

---

## 10. 下一步（按性价比）

1. **task-18 A/B**（必须）：跑 §6 口径；通过后 Lead 决定是否 promote + 备份名 .bak-ponder-crash。
2. **渲染恢复**（可选、独立任务）：按 §7 Route 1 或 Route 2 做，需要真机画面 A/B；
   建议先 Route 2（改动面小、失败可秒回滚到本候选）。
3. **顺手收口**：docs/HANDOFF.md §7.1 的「Ponder 几何体提交 ❌」条目更新为「⚠ 不再崩；几何体仍不画（§fix-ponder-crash §7 有入口）」。
4. 若真机 A/B 发现「开了 Ponder 又崩在别处」：按 docs/api-landmines.md 的流程先 scan_landmines.py，
   再用 g31/smoke/PonderAudit（ASM 代码级审计）扫 com/zurrtum/create/client/ponder/** 的其余类，找下一个缺失成员。


---

## 11. 附：client/ponder/** 全包代码级审计（183 class / 2,168 refs）

用 g31/smoke/PonderAudit（@all 模式）对整个 Ponder 包做了一次链接审计：**member_missing=5**。
逐条核对后 **没有新发现**，全部是「已知地雷 / 已知修复 / classpath 版本遮蔽」：

| 缺失成员 | 出处 | 判定 |
|---|---|---|
| SubmitNodeCollector.submitBreakingBlockModel(PoseStack,List,int) | WorldSectionElementImpl.renderFirst（landmines #5） | **已知地雷**（26.3 是 4 参：+boolean）——A/B 若打开「世界剖面」类场景可能仍崩 |
| ClipboardManager.setClipboard(Window,String) | PonderUI.mouseClicked（landmines #11，3 处） | **已知地雷**（26.3 只有 setClipboard(String)）——Ponder 里点「复制/分享」类按钮会崩 |
| InputConstants.isKeyDown(Window,int) | PonderTooltipHandler | **已修**（R406 sky262crashfix mixin 运行期补回；裸 classpath 审计会误报） |
| ImmutableSet.toImmutableSet() | PonderTagRegistry | 疑似 classpath 版本遮蔽（classpath 里 guava-20.0.jar 排在 33.x 之前），**未核** |
| MutableObject.get() | PonderScene | 疑似 classpath 版本遮蔽（commons-lang3 多版本），**未核** |

⇒ 结论：**task-15 修的 prepare/execute 路径是这个包唯一的「一开面板就崩」点**；剩下两个真地雷都要
「鼠标点复制」或「世界剖面场景」才触发，属于另一个族（要不要修见 landmines #5 / #11，建议单独立项）。


---

## 12. R409 / task-23 续修：FeatureRenderDispatcher.renderAllFeatures(SubmitNodeStorage) 已删（5 个 GUI 画中画渲染器）

> **状态：候选件已构建 + 静态/装载证据链 PASS；游戏内 A/B 未实测（task-18 复验）。**
> 两个候选：**CORRECT**（恢复画中画渲染，优先测）与 **SAFE**（画中画空白但不崩，兜底）。
> 基线 = **已 promote 的 R408 create-fly** 56f1d716… / 19,639,203 B（其中已含 §1–§11 的 SceneRenderer 修复）。

### 12.0 为什么还有第二处

interact-probe 的 r408 A/B（保持 PonderUI 60 tick）显示：基线崩 executeSolid（§1 那处，已消失），
但 r408 件**第一帧又崩在下一个已删 API**：

~~~
java.lang.NoSuchMethodError: void net.minecraft.client.renderer.feature.FeatureRenderDispatcher.renderAllFeatures(SubmitNodeStorage)
  at com.zurrtum.create.client.catnip.gui.render.ItemTransformElementRenderer.prepare(ItemTransformElementRenderer.java:94)
  at net.minecraft.client.gui.render.GuiRenderer.preparePictureInPictureState(GuiRenderer.java:315)
~~~

26.3 把 renderAllFeatures 改成了 **public static renderAllFeatures(RenderPass, PreparedFrame)**（javap 实测，
它的体 = executeSolid → executeTranslucent → executeTranslucentAfterTerrain → executeSeeThrough → executeAlwaysOnTop），
**没有 1 参 (SubmitNodeStorage) 重载**。create-fly 里仍有 **5 个** GUI 画中画渲染器调旧 API：

| class | 旧调用所在方法 | javap offset |
|---|---|---|
| catnip/gui/render/ItemTransformElementRenderer | prepare(...) | 429 |
| catnip/gui/render/BlockTransformElementRenderer | prepare(...) | 367 |
| catnip/gui/render/EntityBlockRenderer | prepare(...) | 519 |
| catnip/gui/render/PartialElementRenderer | prepare(...) | 255 |
| foundation/gui/render/GuiBlockRenderer | 自己的 renderAllFeatures(FeatureRenderDispatcher) | 39 |

### 12.1 正确修法（26.3 原版写法，javap 逐条对齐）

26.3 原版 PictureInPictureRenderer.prepare 就是这么做的（§7.1）：prepareFrame(storage) →
createRenderPass(supplier, colorView, Optional.empty(), depthView, OptionalDouble.empty()) →
RenderSystem.bindDefaultUniforms(pass) → FeatureRenderDispatcher.renderAllFeatures(pass, frame) → pass.close()。

这 5 个渲染器的**目标纹理已有现成来源**：它们都先调 GpuTexture.prepare(Projection, ProjectionMatrixBuffer)，
后者会把 dev/eriksonn/aeronautics/compat/RenderBitsBridge.outputColorTextureOverride / outputDepthTextureOverride
设成自己的 color/depth view（GpuTexture.clear 再置空；QuadParticleFeatureRendererMixin 已经读这两个字段）。
所以新增一个 **javac 编译**的小 helper（不是手写 ASM），把 26.3 的调用序列一次性补齐：

~~~java
public static void render(FeatureRenderDispatcher dispatcher, SubmitNodeStorage storage) {
    GpuTextureView color = RenderBitsBridge.outputColorTextureOverride;
    GpuTextureView depth = RenderBitsBridge.outputDepthTextureOverride;
    FeatureRenderDispatcher.PreparedFrame frame = dispatcher.prepareFrame(storage);
    if (color == null || depth == null) { frame.close(); return; }        // 防御：无目标就释放
    RenderPass pass = RenderSystem.getDevice().createCommandEncoder()
        .createRenderPass(LABEL, color, Optional.empty(), depth, OptionalDouble.empty());
    RenderSystem.bindDefaultUniforms(pass);
    FeatureRenderDispatcher.renderAllFeatures(pass, frame);
    pass.close();
    frame.close();
}
public static void drain(FeatureRenderDispatcher dispatcher, SubmitNodeStorage storage) {
    dispatcher.prepareFrame(storage).close();     // SAFE 模式：排空提交队列，不建 pass
}
~~~

调用点改法（**等长、栈形不变**）：把 invokevirtual FeatureRenderDispatcher.renderAllFeatures:(L...SubmitNodeStorage;)V
换成 invokestatic GpuFrameRunner.render:(L...FeatureRenderDispatcher;L...SubmitNodeStorage;)V。
调用点栈上原本就是 [dispatcher, storage]，helper 形参顺序一致；invokevirtual / invokestatic 都是 3 字节
⇒ 指令偏移、StackMapTable、LineNumberTable 全不动（只有 opcode + CP 索引变，CP 新条目追加在尾部）。

**新增 1 个 class entry**：com/zurrtum/create/client/catnip/gui/render/GpuFrameRunner.class（3,069 B，
javac 25.0.1 编译，sha256 6e0cbe0489a995bad02d37b79750943a6dfe5de9749733910b1558473e36cd33）。
这是本轮**唯一的结构性变化**（entry 14,336 → 14,337），理由：把 40+ 条指令内联进 5 个类太脆，
而 javac 产出的字节码（含 lambda/帧/CP）由编译器保证正确；其余 entry 逐字节不动。

### 12.2 交付件（两个候选，先测 CORRECT）

| 项 | 路径 | size | SHA-256 |
|---|---|---|---|
| 基线（R408 promote，只读） | work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar | 19,639,203 B | 56f1d71699179bd045fb78aef4559d66e67656c3c5d3ea1e95c169ea456460df |
| **CORRECT（优先 A/B）** | work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix2.jar | 19,640,880 B | d57fdbbf2e7779ab380734995b647df1cabf1f755ebaf9386eadeb2d231aa3df |
| SAFE（兜底） | work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix2-nop.jar | 19,640,886 B | 1ba69f497ba4010d5b6eb860cd2cc608d26fb98682904627b40344367cdf6ae1 |

- 基线声明：基于 **R408 promote 件 56f1d716… / 19,639,203 B**（mtime 20:29:32），_build_ponderfix2.py 硬校验；
  并断言其中 SceneRenderer.class = 02069fb4…（§4 的 task-15 输出）⇒ 补丁确实 rebase 在最新件上。
- mods-stable / watch **本轮未写**（只在读）。
- **promote 约定（Lead 2026-10-18 定的）**：A/B 通过后先测 CORRECT，崩了退 SAFE；promote 时把选中件重命名成
  create-fly-26.2-6.0.9-2-26.3-patched.jar，**当前 R408 件备份为 .bak-r409**；Ponder 场景几何体本轮不做（task-15 的 nop 保留）。

### 12.3 证据链（g31/out/evidence/p2_*）

| 证据 | 结论 |
|---|---|
| p2_jar_audit.txt | entry 14,336→**14,337**（+1 = GpuFrameRunner）；**内容变化 entry 恰好 5 个**（上表 5 个渲染器）；其余 **14,331/14,336** 个原始 entry 的 raw deflate 流逐字节相同；testzip()=None |
| p2_<class>_old/new.txt + 构建日志 | 每个类 javap -p -c **恰好 1 条指令变化**（invokevirtual → invokestatic），偏移不变（429/367/519/255/39） |
| 同上 | 常量池**旧条目全部保留**（只追加 6 条）；StackMapTable / LineNumberTable **按块多重集完全相同**（2 个/9 个块等） |
| p2_<class>_clsdiff.txt | 成员数 SAME（12/12、13/13、8/8…），changed methods **1 / N** |
| p2_smoke_report.txt / p2_smoke_verdict.txt | 类加载（Class.forName(initialize=true)，强制 JVM 全类校验）+ 代码级链接审计：**基线每个类缺 1 个成员**（正是 renderAllFeatures(SubmitNodeStorage)），**两个候选每个类都缺 0**；新类 GpuFrameRunner 自身 init OK + 缺 0。**16/16 PASS** |

### 12.4 降级（SAFE 候选 / 万一 CORRECT 不能用）

| 项 | 修前（r408） | CORRECT | SAFE |
|---|---|---|---|
| 打开 Ponder | 第一帧崩 renderAllFeatures | 不崩 | 不崩 |
| GUI 画中画（物品/方块/实体预览） | 崩，看不到 | 恢复渲染（**未实测**） | **空白**（纹理只有清屏色） |
| Ponder 场景几何体 | 画不出来（§1 起既有） | **仍然画不出来**（SceneRenderer 还是 §3 的 nop；本轮不动） | 同左 |
| 提交节点队列 | — | 每帧执行后释放 | prepareFrame(...).close() 排空，不累积 |

### 12.5 A/B 口径（task-18 / interact-probe）

staging（已建好，硬链接，其余 70 jar 与 mods-stable 逐字节相同）：

- g31/stage/mods-baseline = 当前 mods-stable（create-fly 56f1d716…）
- g31/stage/mods-candidate = CORRECT（d57fdbbf…）
- g31/stage/mods-candidate-nop = SAFE（1ba69f49…）
- g31/stage/manifest-r409.json

**复跑上次的动作即可（保持 PonderUI 60 tick）**：

| 判定 | baseline | candidate (CORRECT) | candidate-nop |
|---|---|---|---|
| crash-report 新增 | 1 个，renderAllFeatures(SubmitNodeStorage) @ ItemTransformElementRenderer.prepare | **0 个** | 0 个 |
| latest.log grep renderAllFeatures | 命中 | 不命中 | 不命中 |
| Ponder 面板 | 第一帧崩 | 打开、可交互 | 打开、可交互 |
| 画中画内容 | — | 物品/方块预览**应能看到**（本轮目标） | 空白 |
| 场景区动画 | — | 仍空白（§1 既有损失） | 仍空白 |

若 CORRECT 崩在 createRenderPass / bindDefaultUniforms / renderAllFeatures(RenderPass,...) 等新调用上：
把 crash-report 发 ponder-26，直接用 SAFE 候选过 A/B（同一份地基，只是 helper 方法换成 drain）。

### 12.6 本轮不修（下一轮）

- SceneRenderer 的场景几何体渲染（§7 的两条路线；现在有了 GpuFrameRunner 的 pass 骨架，
  可加一个 renderFrame(PreparedFrame) 重载 + 把 §3 的 5 个 nop 站点之一改成 3 字节 invokestatic，
  即能让 Ponder 场景真正画出来——但那是新的行为改动，需单独 A/B）。
- WorldSectionElementImpl.renderFirst 的 submitBreakingBlockModel(3 参)（landmines #5）。
- PonderUI.mouseClicked 的 ClipboardManager.setClipboard(Window,String)（landmines #11）。


---

## 13. R410 / task-25：让 Ponder 场景几何体真正画出来（SceneRenderer 第一处 nop 站点改成 renderFrame）

> **状态：候选件已构建 + 静态/装载证据链 PASS；游戏内 A/B 未实测（interact-probe 截图判「画面是否有内容」）。**
> 基线 = **当前 live create-fly D57FDBBF… / 19,640,880 B**（= R409 已 promote 的 task-23 CORRECT 件；
> 用户实机已确认「思索界面能进、但不显示演示动画」）。
> 候选 = **ponderfix3**：只叠 2 个 entry 变化 —— 新增 GpuFrameRunner.renderFrame(PreparedFrame) + SceneRenderer.prepare 第一处 nop 站点改回真调用。

### 13.1 本次改动

1. GpuFrameRunner 新增 **public static void renderFrame(PreparedFrame frame)**：
   与 render(dispatcher, storage) 相同的 pass 创建/执行序列（createRenderPass 用 RenderBitsBridge 已发布的
   color/depth view → bindDefaultUniforms → static renderAllFeatures(pass, frame) → hasAnyOutline/hasAnyWaterMask
   补执行 → pass.close()），但**不 close frame**（frame 归 SceneRenderer.prepare 的 try/finally 所有）。
2. SceneRenderer.prepare(SceneRenderState, …) 的**第一处** task-15 nop 站点（javap offset 268..270）
   aload 13; pop; nop; nop（5 字节）→ aload 13; invokestatic GpuFrameRunner.renderFrame(PreparedFrame)V（同样 5 字节）。
   其余 4 个 nop 站点（271/276/281/286）保持 no-op（无害；static renderAllFeatures 一次覆盖 solid/translucent/
   translucentAfterTerrain/seeThrough/alwaysOnTop，outline/waterMask 由 helper 按 hasAny* 补）。

⇒ 结果：prepare 里 prepareFrame(...) 拿到的场景帧**真的被带 pass 执行**到 Create 自己的 GpuTexture
（GpuTexture.prepare 已清屏 + 设 ortho + 发布 bridge views），随后既有的 BlitRenderState 把它 blit 到 GUI ⇒
Ponder 场景几何体应重新可见。

### 13.2 交付件

| 项 | 路径 | size | SHA-256 |
|---|---|---|---|
| 基线（live R409，只读） | work/run26/mods-stable/create-fly-26.2-6.0.9-2-26.3-patched.jar | 19,640,880 B | d57fdbbf2e7779ab380734995b647df1cabf1f755ebaf9386eadeb2d231aa3df |
| **候选（ponderfix3）** | work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix3.jar | 19,641,125 B | f4bed96e357dbb941b6daa400fee01fbbbf8f0b17a4dc2b6d3116324a469bcba |
| SceneRenderer.class（新） | 同上 jar 内 | 14,118 B | bccbedd6549a8241…（完整值见 g31/out/evidence/p3_jar_audit.txt） |
| GpuFrameRunner.class（新） | 同上 jar 内 | 3,513 B | 47d80457eb70823d53f6d7f8060768f63756742e39a0e3ad0543dd66ee80af61 |

- 基线声明（硬校验）：_build_ponderfix3.py 断言 live 件 = D57FDBBF… / 19,640,880 B、entries 14,337、
  其中 SceneRenderer.class = 02069fb4…（task-15 输出）、GpuFrameRunner.class = 6e0cbe04…（task-23 helper）
  ⇒ 补丁确实叠在已 promote 的 R409 上。
- promote 时建议备份名 **.bak-r410**。

### 13.3 证据链（g31/out/evidence/p3_*）

| 证据 | 结论 |
|---|---|
| p3_jar_audit.txt | entries **14,337 → 14,337**（集合不变）；**内容变化 entry 恰好 2 个**（SceneRenderer + GpuFrameRunner）；其余 **14,335/14,337** 个 entry raw deflate 逐字节相同；testzip()=None |
| p3_SceneRenderer_old/new.txt + 构建日志 | javap -p -c **恰好 4 行 diff**：删 268: pop / 269: nop / 270: nop，在 **offset 268** 加 invokestatic GpuFrameRunner.renderFrame:(PreparedFrame)V；266 的 aload 保留 |
| 同上 | **266..271 之外的指令 offset 全部不变**（构建脚本逐条断言）；常量池**旧条目全部保留**（+6 新）；StackMapTable / LineNumberTable **按块多重集完全相同**（2 / 10 块） |
| p3_SceneRenderer_clsdiff.txt | 成员 15=15 SAME，changed methods **1 / 15**（只有 prepare） |
| p3_GpuFrameRunner_old/new.txt | 旧方法 render/drain 保留，**新增 renderFrame**；类 3,069 → 3,513 B |
| p3_smoke_report.txt / p3_smoke_verdict.txt | 类加载（Class.forName initialize=true 强制全类校验）+ 代码级链接审计：baseline/candidate 的 SceneRenderer、GpuFrameRunner 均 init OK；两个候选类 **member_missing=0 / owner_not_found=0**（含 hasAnyOutline/executeOutline/hasAnyWaterMask/executeWaterMask/createRenderPass/bindDefaultUniforms 等新引用） |

### 13.4 A/B 口径（task-18 / interact-probe）

staging（已建好，硬链接；manifest-r410.json）：

- g31/stage/mods-baseline = 当前 live R409（D57FDBBF…）——Ponder 界面能进、**场景空白**
- g31/stage/mods-candidate-p3 = ponderfix3（f4bed96e…）——**场景应有几何体动画**
- 旧 stage/mods-candidate（== live R409，已不是 A/B 臂）与 stage/mods-candidate-nop（R408 时代 SAFE）已标 stale；
  P3 的退路就是**不 promote**（live R409 本来就不崩）。

判定（**截图对比** + 日志）：

| 判定 | baseline（live R409） | candidate-p3 |
|---|---|---|
| 打开 Ponder / 保持 60 tick | 不崩 | **不崩**（若崩，把 crash-report 发 ponder-26） |
| 场景区域画面 | 空白/纯清屏色 | **应有方块/装置几何体**（场景平台影子、装置动画） |
| UI/文字/翻页 | 正常 | 正常（不应受影响） |
| 其它 Create GUI 的画中画（物品/方块预览） | 正常（R409 已修） | 应保持正常（render 路径只多了 outline/waterMask 补执行） |

若画面**有内容但位置/缩放不对**：记录现象（截图 + 是否偏移/过大过小）——那是 §13.5 的已知不确定项，
需要再对投影/模型视图做一轮；**不要把「有内容但偏」当崩溃**。

### 13.5 已知不确定（未实测，声明在此）

1. **投影/模型视图假设**：Create 的 GpuTexture.prepare 设了 Projection.setupOrtho(-1000,1000,w,h) 并
   RenderSystem.setProjectionMatrix；helper 的 bindDefaultUniforms(pass) 取的就是这份状态 ⇒ 应与 26.2 一致，
   但 26.2 的 execute* 内部到底用哪份投影无法从字节码反推，若画面偏移/比例不对即此原因。
2. **phase 覆盖差异**：26.2 Create 调的是 solid/translucent/outline/translucentAfterTerrain/alwaysOnTop；
   现在 = static renderAllFeatures（solid/translucent/translucentAfterTerrain/seeThrough/alwaysOnTop）+ hasAny* 时补
   outline/waterMask。多出的 seeThrough 一般对不透明场景无影响，透明度排序可能有细微差异。
3. **粒子**：QuadParticleFeatureRendererMixin 读 RenderBitsBridge 的 override，pass 生命周期与它一致（都在 prepare 内），
   预期正常；未实测。
4. 场景几何体首次出现可能受 GpuTexture 缓存 key（state.id()）影响：同一 PiP id 复用纹理；本函数内 GpuTexture.prepare
   在 268 之前已发布 bridge views ⇒ 逻辑上不会为 null；helper 仍有 null 防御。

**回滚**：候选不 promote 即无事；若 promote 后要回：换回 .bak-r410（= 当前 live R409 件）+ 重启客户端。


---

## 14. R410 续：Ponder 场景「画出来了但投影/缩放不对」——ponderfix4 诊断矩阵（task-25 follow-up）

> **状态：4 个诊断变体已建 + 证据链 PASS；p4-solid / p4-nodepth 已实跑（见 §14.5），p4-projtex / p4-phases 待跑。**
> 背景：P3（ponderfix3 f4bed96e…）A/B 结果 = 两臂 0 崩溃、PonderUI 正常，P3 场景区**有几何且在动**
> （多帧 diff 1.54/2.92/3.84），但看起来是「从底部两侧向中心收拢的大暗面 + 少量亮斑」，看不出平台/齿轮
> ⇒ 渲染循环通了，**投影/缩放/放置不对**。**P3 不 promote**（live R409 本来不崩）；本节产物只用于定位。

### 14.1 诊断矩阵（每个变体只改 GpuFrameRunner 一个 entry）

| 变体 | size | SHA-256 | 变量 |
|---|---|---|---|
| work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix4-solid.jar | 19,641,997 B | 7229db3ac036c352abf4ecb1e4ed54fc3368f1990840c31d2121513f7a85873d | color+depth pass，**只执行 frame.executeSolid(pass)** |
| …-ponderfix4-nodepth.jar | 19,642,987 B | 946d9b3f9bd2b94ee8eafd1863d5d3d06ca3a766e6bd8e903fe8776cd2d3ce16 | **color-only pass（无 depth）**，全 phase |
| …-ponderfix4-projtex.jar | 19,643,303 B | 3c15c8dd89d60a013b1077569d28576238e3a79a1c5d275cf5da52a8eec52dec | 全 phase + 执行前按**纹理尺寸**重建 ortho(0..texW,0..texH) |
| …-ponderfix4-phases.jar | 19,643,044 B | 4ec346eb56cec735570b295b1b31927796623e6fdeae70416389b72c81680241 | 全 phase + **反射 dump 提交内容**（submits 按类计数 + groupsByPhase） |

> 注：solid/nodepth 的 helper 在加反射方法后重新编译过，所以 SHA 变化（行为与首轮等价；首轮截图/日志对应的旧 SHA：
> solid 7229db3a… / nodepth c37ecefd…）。最新件以本表为准。

- 三个都基于 P3（= live R409 + SceneRenderer 第一处 nop→renderFrame），**只替换 helper 一个 entry**：
  entries 14,337 不变、changed entry 恰好 1 个、其余 14,336 个 raw deflate 逐字节相同、testzip 通过（p4_jar_audit.txt）。
- staging：g31/stage/mods-p4-solid / mods-p4-nodepth / mods-p4-projtex（各 71 jar，其余与 mods-stable 逐字节相同）；
  baseline = g31/stage/mods-baseline（live R409）；manifest-p4.json。
- **每个变体每秒往日志写一行**（logger=sky262ponder）：
  [sky262 ponder] mode=.. tex=WxH guiScale=.. win=WxH projType=.. frameEmpty=.. outline=.. waterMask=..

### 14.2 本次新查清的字节码事实（诊断依据）

1. **场景坐标空间**（PonderScene$SceneTransform.apply，javap）：
   translate(width/2, height/2, 200+offset) → 固定旋转（X -35, Y 55, X 35）→ rotate(xRotation,yRotation)
   → **scale(30·scaleFactor, −30·scaleFactor, 30·scaleFactor)** → translate(基座偏移)。
   ⇒ 场景是在**面板像素空间**（0..width, 0..height，中心在 width/2,height/2）里画出来的，
   **投影必须 ortho(0..width,0..height)**，否则就会整体缩放/偏移。
2. **GpuTexture.prepare** 设的正是 ortho(zNear=-1000, zFar=1000, width, height, invertY=true)，
   而 GpuTexture.create(state.width(), state.height(), guiScale) 建的纹理是 **width×guiScale × height×guiScale**。
3. **pass 默认 viewport = 纹理尺寸**（CommandEncoder.createRenderPass 5 参默认 RenderArea=(0,0,纹理宽,纹理高)）。
   ⇒ 若「ortho(width,height) ← viewport(width·scale,height·scale)」成立，就是超采样，本应正确；
   若实际 viewport 不是纹理尺寸，就会产生 **≈guiScale 倍的放大** —— 与「巨大暗三角、看不出装置」吻合。
4. 平台影是 ShadowRenderState（CustomGeometryRenderer，半透明黑 alpha 0x66，位置 z≈4），
   走 translucentCustomGeometry phase（RenderType.hasBlending），由 executeTranslucent 执行 ⇒
   **p4-solid 会把它去掉**，从而把「solid 几何对不对」与「透明层/深度问题」分离。

### 14.3 判读表（interact-probe 跑完后按此定 -ponderfix5）

| p4-solid 截图 | p4-nodepth | 结论 | 下一步 |
|---|---|---|---|
| 平台/压床/齿轮**正确可见** | — | 几何与投影都对；问题是**透明层/暗面把场景盖住**或 z 顺序 | 修 renderFrame：调整执行顺序（solid→translucent 分层 + 深度状态），或让 shadow 不再盖住场景 |
| 仍巨大暗形/空白 | nodepth 后正确 | **深度附件/z 问题** | 弃 depth 附件，或改深度清/比较 |
| 仍巨大暗形 | nodepth 仍巨大暗形 | **投影/缩放问题**；看 projtex 是否变「小/偏」 | 按日志 tex/guiScale 反推正确 ortho（或显式 RenderArea / 自建投影） |
| 崩溃 | — | 记录 crash-report，该变体排除 | 从剩下变体继续 |

日志数字用法：tex / guiScale ⇒ width=tex/guiScale；win ⇒ 窗口像素；projType 应为 ORTHOGRAPHIC；
frameEmpty=false 且 outline/waterMask 有值 ⇒ 提交确实进了对应 phase。

### 14.4 交付纪律

- 只读 live（D57FDBBF…）；本轮未写 mods-stable / watch；P3 不 promote。
- 判「真正修好」= 用 create:mechanical_press 截图能辨认平台+装置 + 0 crash + UI 正常；
  三个变体只用于定位，**不会直接作为交付件**；定出原因后出 -ponderfix5（同样 1~2 个 entry 级改动）再走 A/B。


### 14.5 p4 实跑结果（interact-probe，2026-10-18 21:10–21:12，create:mechanical_press）

**日志（两个变体一致，每秒一条）：**

~~~
[sky262 ponder] mode=1 tex=1281x720 guiScale=3 win=1280x720 projType=ORTHOGRAPHIC frameEmpty=false outline=false waterMask=false
[sky262 ponder] mode=2 tex=1281x720 guiScale=3 win=1280x720 projType=ORTHOGRAPHIC frameEmpty=false outline=false waterMask=false
~~~

**截图判读：**

| 变体 | 场景区 | 结论 |
|---|---|---|
| p4-solid（只 executeSolid） | **完全空白**（只剩模糊世界背景 + UI） | **solid phase 没有任何可见几何**；平台/装置/结构都不在 solid phase（或没提交） |
| p4-nodepth（全 phase、无深度） | 与 P3 相同的**大块暗面**（斜边、多帧变化） | 可见的东西来自**非 solid phase**（translucentCustomGeometry 等）；去掉深度不改变它 |

⇒ 两个关键事实：
1. **投影不是问题**：projType=ORTHOGRAPHIC，tex=1281×720 而 win=1280×720（面板 width=1281/3≈427、height=240），
   ortho(427,240) 对 viewport(1281,720) 恰好是 **3× 超采样**，与 §14.2 的推导一致。
   ⇒ 巨大的暗面不是「guiScale 倍放大」造成的，而是**它本来就画成了那样**（见下一条）。
2. **看不到平台/齿轮的原因是 geometry 没进 solid phase**（或压根没提交）——
   p4-solid 空白说明 solid phase 里没有可见的 world-section 结构。
   而 WorldSectionElementImpl.renderFirst 的字节码显示：平台/结构走 SuperByteBuffer.submit(PoseStack, collector)
   （→ SuperByteBufferRenderState.submit → 大概率是 submitCustomGeometry，phase 由 RenderType.hasBlending() 决定），
   所以**平台块很可能被归进了 translucent 类 phase**，或被 submit 的 render state 判空/丢弃。

**下一步（p4-phases，反射 dump）**：直接打印
  submits={Submit 类名: 数量}、phases={FeatureRenderPhase 类名#组数}
⇒ 若 submits 里有大量 CustomFeatureRenderer$Submit / 没有 BlockModelFeatureRenderer$Submit 或 ModelFeatureRenderer$Submit，
   且 phases 里 main 是 TranslucentFeatureRenderPhase/translucentCustomGeometry，则确认「结构被当成半透明画」，
   -ponderfix5 就应改为「把结构按 solid 执行 / 或让 executeTranslucent 也带正确深度/顺序」，而不是动投影。


### 14.6 p4 全矩阵结果（interact-probe，2026-10-18 21:10–21:28）+ 追踪件 ponderfix4b-trace

| 变体 | 结果 |
|---|---|
| p4-solid（只 executeSolid） | 0 crash；日志 projType=ORTHOGRAPHIC tex=1281x720 guiScale=3；**场景区全空**（与空白基线等价） |
| p4-nodepth（全 phase、无 depth） | 0 crash；与 P3 相同的**大暗面**，无平台/压床 |
| p4-projtex（pass 内重建 ortho） | **崩**：IllegalStateException: Close the existing render pass before performing additional commands @ FrontendCommandEncoder.writeToBuffer ← ProjectionMatrixBuffer.writeBuffer ← GpuFrameRunner.renderFrame:79 ⇒ 在 render pass 打开时写投影 buffer，违反 pass 生命周期；**该方向作废** |
| p4-phases（反射 dump，简单名） | 0 crash；submits={Submit=3} 后稳定 {Submit=1}；phases=SimpleFeatureRenderPhase#1（1~3 组）。**没有 Block/Model/Translucent 分相**；画面仍暗 |

⇒ p4 结论（与 Lead 判读一致）：
1. **投影/深度不是问题**（projType=ORTHOGRAPHIC、tex≈win、p4-solid 与 p4-nodepth 都证明可见暗面与 depth 无关）。
2. **完整方块/装置从未进入任何 FeatureRenderPhase**：只有极少量泛型 Submit（且日志用的是简单类名，
   CustomFeatureRenderer$Submit 与 BlockModelFeatureRenderer$Submit 都显示成 Submit，无法区分）。
3. 可见暗面 = 被塞进 SimpleFeatureRenderPhase 的那 1~3 个泛型 Submit（很可能是场景地板/背景层）。

### 14.7 追踪件：ponderfix4b-trace（只加日志，不改渲染）

| 项 | 值 |
|---|---|
| 路径 | work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix4b-trace.jar |
| size / SHA-256 | 19,643,877 B / a13504252e178a6ebdb5673525c32975a6bca945f70600c8a39cafaa8d22126c |
| 基线 | P3（f4bed96e…）；相对 P3 只变 **3 个 entry**：GpuFrameRunner（MODE 6 详细日志）+ WorldSectionElementImpl + EntityBlockLayer |
| staging | work/run26/port/g31/stage/mods-p4b-trace（71 jar，其余与 mods-stable 逐字节相同） |

新增日志（logger=sky262ponder）：
- TRACE WorldSectionElementImpl.renderFirst called —— 结构提交入口是否被调用；
- TRACE EntityBlockLayer.submit rt=... blend=... outline=... —— SBB 结构层的 RenderType 及分类；
- submits={**全限定**类名: 数量} renderTypes=[RenderType 字符串 + blend/outline] phases={相位类#组数{各 group 的 featureType}}。

判读树（拿到日志后定 -ponderfix5）：
- **renderFirst 没被调** ⇒ 查 Ponder 元素遍历/可见性/异常吞没（renderScene 的 forEachVisible 路径加 try/catch 日志）；
- **renderFirst 被调、EBL.submit 的 rt 是 solid/cutout（blend=false）但 p4-solid 仍空** ⇒ 问题在 CustomFeatureRenderer
  绘制该管线这一层（staged buffer / 管线绑定 / vertex format），下一步 dump 该 group 的 draw；
- **EBL.submit 的 rt 是 translucent（blend=true）** ⇒ 结构被当半透明画，-ponderfix5 = 在 renderFrame 里把该相位
  按 solid 顺序/深度重建，或改分类判定（不动投影）。


### 14.8 p4b-trace 结果（关键）+ ponderfix4c-trace2（rebase 到 live R412）

p4b-trace（a1350425…）实跑（mechanical_press，200 tick，0 crash）：
- TRACE WorldSectionElementImpl.renderFirst = **10 次**（结构提交入口确实被调用）；
- TRACE EntityBlockLayer.submit = **0 次**（结构 SBB 层一次都没提交）；
- 每帧唯一提交：CustomFeatureRenderer$Submit=1，RenderType = ponder:gui（blend=true，useLightmap=false），













### 14.21 A/B 结果（ponderfix5b PASS）—— Ponder 场景几何恢复

staging work/run26/port/g31/stage/mods-p4n-ponderfix5（create-fly 595b5eb8… + live 其它件），
interact-probe 用全新存档、三场景各 PonderUI 200 tick、tick 120/180 截图：

| 场景 | 结果 |
|---|---|
| create:mechanical_press | 白色棋盘平台 + 动力冲压机（活塞+齿轮）+ 大齿轮组 + 红石物品高亮，3D 透视正常 |
| create:gearbox | 白平台 + 十字齿轮箱 + 四根轴 + 右侧解说文本 |
| create:cogwheel | 白平台 + 齿轮组 |

- 三次都 P_SCREEN=PonderUI、PROBE_OK、**0 crash-report**；UI/文字/物品栏正常（无黑箱、无错位）；
- 本版 helper MODE=0 不再输出 trace 日志，视觉判据已足够；
- 截图：g33/ponder-press-fixed.png / ponder-gearbox-fixed.png / ponder-cogwheel-fixed.png
  （原始 g33/evidence/pf5-{press,gear,cog}-shot-{0,1}.png）；我本人复核过 press 截图（1280x720），
  确认白平台+冲压机+齿轮+文字，与参照图 g33/ref-user-ponder-normal-3d.png 一致。

⇒ **用户「思索界面里的 3D 演示动画没显示」这条已解决**；候选可 promote（Lead 执行）。
promote 用件：work/run26/port/g31/out/create-fly-26.2-6.0.9-2-26.3-patched-ponderfix5b.jar
（19,648,330 B / 595b5eb832f86c9a54eaf9b9225c51ebf2753463ba9fb47180095fecd710da82；base live 43C4A441…；
changed=180 = 178 nbt + 2 class）。promote 必须「临时文件 + os.replace 原子替换目录项」，
先备份 .bak-r417，改完复跑标题+进世界+Ponder。

已知残余风险（本族记录）：
1) 旧版实体/方块实体 NBT 若也遇到 26.3 键名变化，个别场景的 BE 数据可能降级（不影响几何显示）；
2) Ponder 粒子/文字路径本来就正常（R409 起），本次只补世界方块数据 + 场景帧渲染；
3) 未涉及 sublevel chunked 渲染（属 task-28，另族）。
