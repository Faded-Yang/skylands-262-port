# port-fluids-263 —— CEI / DragonsPlus 在 26.3 create-fly 的流体注册（B1 收口）

> 日期：2026-10-20 ｜ base = live 98 jar（create-fly 6.0.9-2，17FD0C33…）
> 结论：**CEI 流体注册已是 26.3 正确写法且已在 live**；DP 当前源码相对 live 只差 fabric.mod.json 元数据（无功能变更）⇒ 不重出 DP。

## 1. 26.3 create-fly 的 FluidEntry 形态

com.zurrtum.create.infrastructure.fluids.FluidEntry：

    public class FluidEntry {
       public FlowableFluid flowing = new FluidEntry.Flowing();
       public FlowableFluid still   = new FluidEntry.Still();
       @Nullable public BucketItem bucket;
       @Nullable public FluidBlock block;
    }

要点：
- 构造器已创建 Still/Flowing 实例，并已绑定 Fluid 的 intrusive holder；
- 不要再 new FluidEntry.Still() / 反射构造 —— 会得到「未绑定 holder 的流体实例」，并触发 IllegalAccessError: FluidEntry$Still；
- 注册顺序：先 still、后 flowing，各自用 ResourceKey.create(Registries.FLUID, id)；
- 桶与流体块由后续注册阶段通过 entry.bucket / entry.block 挂回。

## 2. 标准写法（CEI CEIFluids，已在 live 72880D90…）

    Identifier id = CEICommon.asResource("experience");
    Identifier flowingId = id.withPrefix("flowing_");
    ResourceKey<Fluid> sourceKey = ResourceKey.create(Registries.FLUID, id);
    ResourceKey<Fluid> flowingKey = ResourceKey.create(Registries.FLUID, flowingId);

    FluidEntry internal = new FluidEntry();
    internal.still   = (FlowableFluid) Registry.register(BuiltInRegistries.FLUID, sourceKey, internal.still);
    internal.flowing = (FlowableFluid) Registry.register(BuiltInRegistries.FLUID, flowingKey, internal.flowing);
    EXPERIENCE = new CDPFluidEntry(id, internal.still, internal.flowing,
            () -> internal.bucket, () -> internal.block);

DP CDPFluids.registerPair(String path) 同构：循环 DyeVariantRegistry.all() 注册 16 个 dye 对，再注册 dragon_breath。

## 3. 注册时序

1. create 的 registry plugin 先跑，建立流体注册基础设施；
2. CEI CEIFluids.register()（experience）；
3. DP CDPFluids.register()（16 dye + dragon_breath，依赖 CEI API 类）；
4. 方块/物品注册阶段 attachBlock / attachBucket；
5. 最后 initialize() 向 OpenPipeEffectHandler.REGISTRY 注册 still/flowing handler。

顺序错误会抛 IllegalStateException("… was not registered by CreateRegisterPlugin")。

## 4. 已知坑（本轮踩到）

| 坑 | 现象 | 结论 |
|---|---|---|
| 新 FluidEntry.Still() | IllegalAccessError: failed to access class FluidEntry$Still | 26.3 私有内部类 ⇒ 只用 new FluidEntry() 自带实例 |
| 重复构造流体 | holder 未绑定 / registry 冲突 | 一个 id 一个实例，still/flowing 只注册一次 |
| DP fabric.mod.json 的 create 版本下限 | 启动弹 Incompatible mods found!：DP 要求 create >=6.0.9-4，live 是 6.0.9-2 | DP 源码相对 live 只差此项元数据（842cc060… vs 01FAFE34…，条目 diff 仅 fabric.mod.json）⇒ 保持 live DP（下限 >=6.0.9-1），不要为此升级 create-fly |

## 5. 验证方法（MCP）

    node tools/mcp_fabric_client.mjs chat.send '{"message":"/setblock ~ ~ ~ create_enchantment_industry:experience"}'
    node tools/mcp_fabric_client.mjs world.getBlock '{"x":...,"y":...,"z":...}'

判定：block 读回 create_enchantment_industry:experience、0 crash、0 registry error；截图留档。

## 6. 结论

- CEI 流体 = 已在 live 的 26.3 正确实现（本轮重编译+重打包 sha 相等，确认无待修）；
- DP 无功能变更，继续用 live 01FAFE34…；
- create-fly 保持 6.0.9-2，不升级（版本链风险 > 收益）。
