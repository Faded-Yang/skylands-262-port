# 如何复现/维护这个 26.3 移植（工程指南）

> 面向想继续维护这套整合包或搬运其它 mod 的人。所有路径相对仓库根目录。

## 0. 环境

- Minecraft **26.3**（官方未混淆 jar）+ **Fabric Loader 0.19.5** + **Java 25**；
- 构建脚本用 Python 3.10（`work/`、`tools/`），不依赖 Gradle/Loom；
- 反编译用 `tools/decompile.py`（Vineflower），参考源码树 `work/refs/mc26.3`、`work/refs/create-fly`。

## 1. 交付件结构

- 交付目录：`work/run26/mods-stable/*.jar`（97 个 jar），由 `启动浮岛世界.bat` 同步到游戏目录；
- 自研/重写件命名：`sky262-*`（如 quests、offroad、toolgun、createdeco、design-n-decor 等）；
- 官方/上游件保持原名（如 `create-fly-26.2-6.0.9-2-26.3-patched.jar`）。

## 2. 手写 jar 的构建（javac 流程）

26.3 是未混淆 jar，所以可以直接对 26.3 jar + fabric-api 编译，不需要 loom/映射：

```text
1) 准备 classpath：26.3.jar、fabric-loader、fabric-api、（可选）create-fly / 目标 mod jar；
2) javac --release 25 -cp <cp> -d <out> <src...>；
3) 拷贝 assets/data/fabric.mod.json/mixin 配置；
4) 用 tools/pack_jar.py 打包（自动写目录条目，否则 lang 不会被加载）；
5) 断言：解 jar 检查 blockstates/items/models/lang 完整性。
```

常踩的坑（详见 `docs/HARD-RULES.md`、`docs/api-landmines.md`）：

- `BlockBehaviour.Properties` / `Item.Properties` **必须先 setId**；
- 模型引用必须带命名空间；`item/` 贴图不能用于方块模型（方块需 `block/` 下的贴图）；
- 手写 jar **必须包含目录条目**，否则 `ClientLanguage` 枚举不到 `assets/<ns>/lang/`；
- 26.3 **一次解析所有 mod lang**：任意一个 lang JSON 非法（缺逗号、控制字符）⇒ 全部 mod lang 失效；打包前用 `tools/lang_audit.py` 审计；
- 旧版 `recipe/advancement` 数据会直接让 registry 加载失败；只带与已注册内容一致的 data；
- 自研方块类必须 `@Override useItemOn/useWithoutItem`（26.3 双入口），并注意 `InteractionResult.TryEmptyHandInteraction` 语义。

## 3. 数据驱动装饰包（createdeco / Design-n-Decor）

```text
1) 解原包，按 id 列表生成方块类（kind → 原版类或自定义属性类）：
   - slab/wall/stairs/pillar/bars/pane/ladder → 原版类（注意 protected 构造器需子类）；
   - 其它带属性方块 → 生成 Custom_<id>（属性集合 = blockstate 键，布尔/枚举/整型）；
2) 解析每个 blockstate 的 variants/multipart，收集模型引用 + 递归 parent 闭包，从原包/create/mc 三处取模型；
3) tools/fix_missing_variants.py：按「方块类属性域」做笛卡尔积补齐缺失变体（幂等）；
4) 断言：每个 blockstate 的每个 variant/multipart model 存在（含 parent）problems=0；ids 只增不减；lang 值为字符串；
5) tools/pack_jar.py 打包 + 冻结 staging `*-final` + MCP 抽验。
```

## 4. 验证（MCP-first）

游戏内客户端 mod `sky262-mcp` 在进世界后开 WebSocket `127.0.0.1:25576`：

```powershell
node tools/mcp_fabric_client.mjs player.getState
node tools/mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ create:cogwheel"}'
node tools/mcp_fabric_client.mjs world.getBlock '{"x":0,"y":64,"z":0}'
node tools/mcp_fabric_client.mjs player.useBlock '{"x":0,"y":70,"z":0,"face":"up"}'
node tools/mcp_fabric_client.mjs screenshot.take --out shots
```

启动用 `tools/launch26/launch.py`（内置全局单实例锁，避免两局并发抢 GPU/端口；`--watch-title` 做标题回归）。

## 5. 当前已知边界

- 装饰类只做「注册 + 放置 + 近似形状」，多数无方块实体/交互；
- natures_spirit 世界生成仍在数据层调试（编译已 0 错误）；
- 柴油发电机只做了装饰/水泥/管道 43 方块，机器与流体未做；
- 矿石挖掘/中央厨房/切片机等为 reduced 范围（注册 + 部分行为），细节见 `docs/DELIVERY.md`。