# fix-creative-pages —— 创造物品栏翻页键（task-27 / R410→R411）

> **状态：R411 收敛候选已出，静态证据 PASS，未启动游戏实测（A/B 由 interact-probe 跑）。**
> 基线 = live `create-fly-26.2-6.0.9-2-26.3-patched.jar`（19,640,880 B，SHA-256 `d57fdbbf2e7779ab380734995b647df1cabf1f755ebaf9386eadeb2d231aa3df`）。
> 用户参照图：`work\run26\port\g33\ref-user-creative-page-arrows.png`（左上 `<`、居中 `5 / 5`、右上 `>`，独立一行在标签页行上方）。
> 交付件未修改；backup 在 `g43\backup\`。

---

## 0. 结论（R411 收敛方案）

1. **分页引擎本来就在跑：Fabric API 的 `fabric-creative-tab-api-v1`**。基线创造界面已经有两枚 **10×12 小按钮**
   （类名 `net.fabricmc.fabric.impl.client.creativetab.FabricCreativeGuiComponents$CreativeModeTabButton`，
   位于 GUI `(287,56)` / `(297,56)`，即搜索框右侧），它就是 Fabric API 的分页引擎 UI。
   **用户看不到/不当成翻页键**，是因为它太小、且不是参照图那种大箭头 + 页码。
2. **Create 自带的分页栈（`CreativeModeTabMixin`/`CreativeModeTabsMixin`/`CreativeModeInventoryScreenMixin`）在我们的 Fabric 包里从未启用**：
   Create 的 `MixinPlugin.getMixins()` 只在 **fabric-api 不存在时**才动态加入 common 分页；
   client 分页 mixin 只在 `isModLoaded("fabric-creative-tab-api-v1")` 时加入——基线 widget dump 里只有 Fabric 的
   `CreativeModeTabButton`、没有 Create 的 `ItemGroupButtonWidget` ⇒ **实际未应用**。
   ⇒ 不需要再注册 Create 那三件（R410 候选那样会变成第二套引擎，与 Fabric 的页过滤互相打架——已实测到 4 套 UI）。
3. **R411 方案 = 只做 UI 适配层**：保留唯一引擎（Fabric API），用我们的 mixin
   - 画参照图布局：左上 `<` / 居中 `x / y` / 右上 `>`（GUI 像素坐标见 §2.2）；
   - 按钮/按键直接调用 Fabric API：`switchToPreviousPage/switchToNextPage/switchToPage`；
   - **隐藏 Fabric 原来的两枚小按钮**（`visible=false`），不再出现两套；
   - 暴露 4 个确定性 hook 供探针自动验证（§4）。
4. **页数 1/3 是正确的**：Fabric 的 `getPageCount() = ceil((tabs().size() - COMMON_TABS 中应显示的数量)/10)`。
   当前 `tabs=24`，COMMON_TABS={search,inventory,hotbar,op_blocks}，非 OP 时 op_blocks 不显示 ⇒ 24-3=21 ⇒ ceil(2.1)=**3 页**。
   上次文档写「1/2」是我算错了（把 4 个 common 都算进 tabs），以探针实测 `1/3` 为准。
5. 其它两条「分页条」不是创造标签页分页，**不要动**：
   - 右上 `1/78`：**JEI 的物品列表分页**（`mezz/jei/gui/PageNavigation`；78×45≈3510 = 探测到的 3510 个物品），正常；
   - 左侧中部 `1/1`：按类扫描不属于 fabric-api / Create / aeronautics，是某个第三方 overlay（本轮不动）。

> ⚠ 更正我 R410 文档里的一个错误结论：曾写「26.3 的 `selectedTab` 不在 clinit 初始化、旧 mixin 注入点会 NPE」。
> **实测 javap：`CreativeModeInventoryScreen.<clinit>` 末尾（offset 327-330）就是 `selectedTab = CreativeModeTabs.getDefaultTab()`**，
> 所以旧 mixin 不会 NPE；它没生效的原因是上面第 2 条（从未注册/动态加入条件不成立）。

---

## 1. 基线三处分页 UI 的归属（R411 查明）

| 位置 | 外观 | 归属 | 处置 |
|---|---|---|---|
| 搜索框右侧 | 两枚 10×12 小按钮 `<`/`>` | **Fabric API** `fabric-creative-tab-api-v1`（基线已有、active 状态正常） | **保留引擎，隐藏这两枚小按钮**，换成大箭头 |
| 右上 | `◀ 1/78 ▶` 灰条 | **JEI** 物品列表翻页（`mezz/jei/gui/PageNavigation`） | 不动（不是标签页） |
| 左侧中部 | `◀ 1/1 ▶` | 未归属（不是 fabric-api / Create / aeronautics 的类；第三方 overlay） | 不动 |

（Create 自带的 `FabricCreativeGuiComponents.ItemGroupButtonWidget` 在基线里**不存在**，见 §0.2。）

---

## 2. R411 候选

| 项 | 值 |
|---|---|
| 文件 | `work\run26\port\g43\out\create-fly-26.2-6.0.9-2-26.3-patched-pagefix.jar` |
| size | **19,644,945 B**（原 19,640,880 B） |
| SHA-256 | `ae62d84a4529a155c07a6551c2c2140c7d9a7f2048c2a0d0baec171d992546a8` |
| 基线 | `d57fdbbf…`（backup 在 `g43\backup\`，SHA 复核一致） |

改动（`python g43\_verify.py` → **PASS**，输出 `g43\out\_static_verify.txt`）：

| 变化 | entry / 内容 |
|---|---|
| 改 1 个 entry | `create.client.mixins.json`：`client` 数组 67 → 68，加 `CreativeModeInventoryScreenPageMixin` |
| 新增 1 个 entry | `com/zurrtum/create/client/mixin/CreativeModeInventoryScreenPageMixin.class` |

其余 **14,336 个 entry 逐字节不变、顺序不变**；zip CRC 全过；不注册 Create 的分页 common mixin（无第二套引擎）。

### 2.1 新 client mixin（`g43\aero\src\…\CreativeModeInventoryScreenPageMixin.java`）

- `Mixin(CreativeModeInventoryScreen.class)`，extends `AbstractContainerScreen<…ItemPickerMenu>`（为拿 `leftPos/topPos/imageWidth/font/children()`）
- `init`（`EditBox.setTextColor(I)V` shift AFTER）：建两枚 vanilla `Button`（`<`/`>`），调 Fabric API 翻页；
- `extractRenderState` TAIL：
  * 每帧把 Fabric 的 `CreativeModeTabButton` 实例 `visible=false`（类名精确匹配，避免依赖 impl 类）；
  * 刷新我们按钮的 `active/visible`（首页左灰、末页右灰、只有 1 页时整行隐藏）；
  * `centeredText(font, "current / total", leftPos+imageWidth/2, topPos-46, 0xFFFFFFFF)`
- `keyPressed` HEAD：266(PageUp)/267(PageDown) → Fabric 的 prev/next；
- 自动验证 hook（mixin 方法合并进 target，public）：
  `sky262$setPage(int)`、`sky262$page()`、`sky262$pageCount()`、`sky262$visibleTabNames()`
  （最后一个按 Fabric 的 `getPage(tab)` + `getCurrentPage()` 过滤 `CreativeModeTabs.tabs()`，返回显示名 List，便于 A/B diff）

### 2.2 参照图坐标反推（GUI 像素；图 1219×1335、scale≈5.69，195 GUI 宽 → 1110 px）

| 元素 | 参照图位置 | GUI 坐标 |
|---|---|---|
| `<` 按钮 | 左上 x≈30..170, y≈20..130 | x=`leftPos`, y=`topPos-52`, 24×20 |
| `>` 按钮 | 右上 x≈1010..1140 | x=`leftPos+imageWidth-24`, 同 y/尺寸 |
| 页码 | 顶部水平居中 y≈70 | `centeredText(..., leftPos+imageWidth/2, topPos-46)` |
| 标签页行 | 按钮行下方（32 px） | 原版 top tab row（`topPos-32..topPos`） |

（按图反推的近似；A/B 截图 1~2 px 偏差属正常。）

### 2.3 历史候选（已作废，仅留档）

- R410a `14455df9…`：注册 Create 三件分页 mixin（第二套引擎）+ 小按钮 UI ⇒ A/B 实测与 Fabric 分页并存成「一屏 4 套」，**作废**；
- R410b `cff1caf2…`：改用参照图坐标，但仍带 Create 第二套引擎与页数算法（1/3 虽数值巧合正确）⇒ **作废**。
- R411（本件 `ae62d84a…`）= 只做 UI、单引擎。

---

## 3. 静态证据（已跑，PASS）

`python work\run26\port\g43\_verify.py` → `out/_static_verify.txt`：

- 条目审计：顺序保留 + 只追加 1 个 class；原 entry 只有 1 个（client 配置）变；`testzip=None`
- 配置 diff：`client` 67→68，新增 `CreativeModeInventoryScreenPageMixin`，其余 key 不变
- **注入目标存在性**（26.3 javap 实测 True）：`init()`、`extractRenderState(GuiGraphicsExtractor,int,int,float)`、
  `keyPressed(KeyEvent)`；`@At` 目标 `EditBox.setTextColor(I)V` 在 `init` Code 里
- **Fabric API 方法存在性**（`fabric-creative-tab-api-v1-5.0.22` 26.3 构建，javap True）：
  `switchToPage/switchToNextPage/switchToPreviousPage/getCurrentPage/getPageCount/getPage/getTabsOnPage/hasAdditionalPages`
- 注解核对：`@Mixin(CreativeModeInventoryScreen)`、`injects=[init, extractRenderState, keyPressed]`、`At=[HEAD,INVOKE,TAIL]`；
  4 个 `sky262$*` hook 均在 class 里
- 类加载冒烟：`URLClassLoader`（候选 jar 首位 + `g21/_javac.py cp_parts()` 375 项）加载
  PageMixin / Fabric API 接口 / `FabricCreativeGuiComponents` / `CreativeModeTabButton` / target 类，无 VerifyError ⇒ `PAGING_SMOKE_OK`

> 仍未证明「注入在运行期成功」——只能由真启动 A/B 验证（见 §4）。

---

## 4. 给 interact-probe 的 A/B 口径（含自动化入口）

staging（硬链接，不写 `mods-stable`/`watch`，71 jar 同名）：

- 基线：`work\run26\port\g43\stage\mods-baseline`（create-fly = live `d57fdbbf…`）
- 候选：`work\run26\port\g43\stage\mods-candidate`（create-fly = `…-pagefix.jar` 改回原名 `ae62d84a…`）
- 重建：`python work\run26\port\g43\_mkstage.py baseline|candidate <dir>`

### 4.1 视觉（按参照图对照截图）

候选预期：
1. GUI 左上角上方 `<` 按钮（24×20，x=leftPos, y=topPos-52），右上角上方 `>`（right 对齐）；
2. 中间顶部居中白色像素字 **`1 / 3`**；
3. **Fabric 原来的两枚 10×12 小按钮应消失**（被 `visible=false`）；JEI 的 `1/78` 与左侧 `1/1` **保持不变**；
4. 点 `>`：页码 → `2 / 3`、tab 行内容变化、`>` 在第 3 页变灰；点 `<` 可回；PageDown/PageUp 同样有效。

### 4.2 确定性验证（不依赖合成点击）

在已打开的 `CreativeModeInventoryScreen` 上反射调用（候选件才有，基线没有）：

```text
Object screen = net.minecraft.client.Minecraft.getInstance().screen;   // 需先按 E 打开
Class<?> c = screen.getClass();
Method setPage = c.getMethod("sky262$setPage", int.class);
Method page = c.getMethod("sky262$page");
Method count = c.getMethod("sky262$pageCount");
Method names = c.getMethod("sky262$visibleTabNames");
int total = (int) count.invoke(screen);            // 期望 3
List<?> page0 = (List<?>) names.invoke(screen);    // 当前页 tab 显示名
boolean ok = (boolean) setPage.invoke(screen, 1);
List<?> page1 = (List<?>) names.invoke(screen);
int now = (int) page.invoke(screen);               // 期望 1
boolean back = (boolean) setPage.invoke(screen, 0);
```

判据：`ok==true`、`now==1`、`page0 != page1`（tab 名列表变化）、`back==true`；同时截图应与 page 号一致。
（这正是上一轮「点击不可靠」的替代入口；hook 直接走 Fabric API 引擎，不经过鼠标。）

### 4.3 基线控制（更新版）

基线没有 `sky262$*` hook；基线的「用户可见」翻页只有搜索框右侧 10×12 小按钮（且点击在上一轮合成路径下未验证）。
**新的控制判据**：候选必须同时满足
(a) 出现参照图大箭头 + `1 / 3`；
(b) Fabric 小按钮消失；
(c) `sky262$setPage(1)` 后 `visibleTabNames()` 变、`page()==1`；
(d) 0 crash。
若 (a) 不出现 ⇒ 注入未生效，回看 mixin 是否被 create 的 client config 加载（client 配置 plugin `shouldApplyMixin` 恒 true）。

---

## 5. 风险 / 未解决

1. **未实测**：mixin 是否 apply、@At 是否命中只能靠启动验证；静态已证目标存在。
2. **硬依赖 fabric-api 模块类**：mixin 直接引用 `FabricCreativeModeInventoryScreen`；若该模块被移除，mixjn 类加载会失败。本包 fabric-api 0.163.0+26.3 是交付必需，风险可接受。
3. **隐藏 Fabric 小按钮**依赖类名精确匹配 `…$CreativeModeTabButton`；若改模块版本名变了，小按钮会重新出现（不会崩，只是双 UI）。可改成按「有我们的按钮时隐藏一切位于 (287..307,56..68) 的 widget」。
4. **页数随 tab 增长**：`1/3` 由 Fabric 算法导出（24 tab）；增加 mod 后自然增长，无需改代码。
5. 左侧 `1/1` 第三方面板未归属，本轮不碰；若它其实也是创造页分页，需要单独查。

---

## 6. 复现命令

```powershell
cd C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\port\g43

python _recon.py                 # 旧 mixin/页组件/26.3 屏幕 javap
python _pager_ownership.py       # 三处 pager 的 jar 归属扫描
python _fabric_pager_detail.py   # fabric-api 分页算法 + 注入点
python _build_mixins.py          # 编译 R411 UI 适配 mixin
python _build_candidate.py       # 打候选 -> out/…-pagefix.jar
python _verify.py                # 静态审计 + 目标存在性 + 冒烟 -> out/_static_verify.txt
python _mkstage.py baseline|candidate <dir>
```

产物：`g43\out\…-pagefix.jar`（`ae62d84a…`）、`out\_static_verify.txt`、`stage\mods-{baseline,candidate}`、`backup\`。

---

## 7. 回滚 / 下一步

- 回滚：`g43\backup\create-fly-26.2-6.0.9-2-26.3-patched.jar`（`d57fdbbf…`）放回 `mods-stable` 同名槽；交付件本轮未动。
- 下一步：A/B 通过（§4 判据 a-d）→ Lead promote（`.bak-r412`）；若 (c) 不成立（Fabric 引擎不翻页），再回到「替换引擎」方案（风险大，需单独立项）。


---

## 8. R411b（pagefix2）—— 末页 `>` 仍 active 的小修

> 基线 = **已 promote 的 R411 live** `ae62d84a…`。本件只替换 1 个 class entry。

| 项 | 值 |
|---|---|
| 文件 | `work\run26\port\g43\out\create-fly-26.2-6.0.9-2-26.3-patched-pagefix2.jar` |
| size | **19,645,003 B**（R411 = 19,644,945 B） |
| SHA-256 | `43c4a4411682b7cd01d7253ea464c0bc68b086a6f7ffa9a4b6b9753b4ab8bc99` |
| 相对 R411 的唯一变化 | `com/zurrtum/create/client/mixin/CreativeModeInventoryScreenPageMixin.class`（其它 14,337 entry 逐字节不变、顺序不变） |

### 8.1 根因（不是 `<=` 边界写错）

- `sky262$refreshPageWidgets()` 的边界条件本来就是对的：`next.active = show && currentPage + 1 < pageCount`
  ⇒ `page=2 / pageCount=3` 时 3<3 = false；
- 真正的问题是**刷新时机**：原来只在 `extractRenderState` TAIL 刷新 active，
  而 A/B 用反射 `sky262$setPage(2)` 之后**同一帧内**立刻读 widget 状态 ⇒ 读到的是上一页遗留的 `active=true`
  （截图 `3/3` 与 widget 读数可能存在一帧错位）；
- 修法：在 `sky262$setPage`、两枚按钮的 onPress、`keyPressed` 的 PageUp/PageDown 分支里**同步调用**
  `sky262$refreshPageWidgets()`（`extractRenderState` TAIL 的刷新保留）。
  ⇒ 无论调用方何时读，active 立即正确；末页点 `>` 时 `switchToNextPage()` 本返回 false，因此点击无效果。

### 8.2 静态证据

`python work\run26\port\g43\_verify2.py` → `out/_static_verify_pagefix2.txt`（PASS）：
entry 顺序相同、**只有 1 个 entry 变**且等于编译产物（sha `479acd4797cb06b3…`）、zip OK、
4 个 `sky262$*` hook 在、`refreshPageWidgets` 同步调用点 **7 处**（setPage + 2 lambdas + 2 key branches + render TAIL）。

### 8.3 给 interact-probe 的补测（只验末页）

staging：`work\run26\port\g43\stage2\mods-baseline`（= promote 后的 R411 ae62d84a）/
`stage2\mods-candidate`（= pagefix2 43c4a441）；重建 `python g43\_mkstage2.py baseline|candidate <dir>`。

1. 打开创造界面 → 反射 `sky262$setPage(2)`（或连点两次 `>`）→ 页码 `3 / 3`；
2. 读 widget：`Button$Plain{msg=>, active=false}`（应置灰）、`<` active=true；
3. 截图 `3/3`；再点一次 `>`（或 `sky262$setPage(3)`）→ `page()` 仍 2、ret=false、无 crash；
4. 抽查 `1/3`、`2/3` 的 active 状态未被改坏。
