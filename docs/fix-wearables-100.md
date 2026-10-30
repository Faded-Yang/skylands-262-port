# 喷气背包/飞行护目镜 可穿戴（R-wearables）

> 静态结论来自 `docs/audit-doors-equipment-100.md`：jetpack/aviators 原先只有普通 Item，无 EQUIPPABLE。

## 实现

### create_jetpack
- `JetpackMod.item(...)`：`Item.Properties` 增加 `DataComponents.EQUIPPABLE`；
  `Equippable.builder(EquipmentSlot.CHEST).setAsset(ResourceKey.create(EquipmentAssets.ROOT_ID, create_jetpack:<id>)).setSwappable(true).setDamageOnHurt(false)`；
- 新增 `assets/create_jetpack/equipment/{jetpack,netherite_jetpack}.json`（`layers.humanoid`）；
- 新增 `textures/entity/equipment/humanoid/{jetpack,netherite_jetpack}.png`（64×32，由现有背面 16×16 图标放到躯干背区，简化版；后续可换正式背甲 UV）；
- `Item#use` 右键推进逻辑原样保留（THRUST 60 tick / 音效 / 同步），穿在胸甲槽不影响手持右键。

### aeronautics aviators_goggles
- `AviatorsGogglesItem` 构造器追加 `EQUIPPABLE` HEAD 组件，asset = `aeronautics:aviators_goggles`；
- 新增 `assets/aeronautics/equipment/aviators_goggles.json`（`layers.humanoid`）；
- 纹理直接复用原 jar 的 `textures/models/armor/aviators_goggles_layer_1.png`（64×32），复制到 `textures/entity/equipment/humanoid/aviators_goggles.png`；
- aero 其余 entries/classes 不变，保留 `309e81b2` 拉杆事件修复（base = live `489bda3f`）。

## 候选

| jar | SHA-256 | size |
|---|---|---|
| `sky262-jetpack-1.0.0.jar` | `a1d5fe30879d8f0bcfefb166542c4c2878aa8afb4b3573baeee0e7e6a8ffaddd` | 18,359 B |
| `aeronautics-fabric-0.1.0-port.26.3.jar` | `e1ea9a1b5d8d5c88624cd07e36460e71d04d2573cbdf8d37e6a782f79a57494d` | 31,606,214 B |

- staging：`work/run26/port/g144/stage-final/mods-candidate`（116 jar = live 116，两件同名替换）；
- 逐 entry diff：仅上述 2 class + 4 个 jetpack 资源 / 1 个 aero class + 2 个 aero 资源，新增条目无删除。

## 验证
- `/item replace entity @s armor.chest with create_jetpack:jetpack` → 胸部出现背包层；
- 手持 jetpack 右键仍推进；穿胸甲时 `getAttribute`/`EQUIPPABLE` 槽为 CHEST；
- `/item replace entity @s armor.head with aeronautics:aviators_goggles` → 头部层显示；
- 0 crash、0 registry error。

## 已知简化
- jetpack 背甲层是程序生成的 64×32 简化图（非原版背甲 UV 精修）；功能可穿戴优先，视觉后续可替换正式层。

## 穿戴状态推进（2026-10-21 追加）

- 问题：穿戴后空手右键不触发 Item#use，喷气背包无推进；
- 方案：新增 C2S ThrustPayload（空 payload）+ JetpackClient 客户端 tick：
  - 条件：getItemBySlot(CHEST) 是 jetpack、主手空、options.keyUse.isDown()、无 GUI；
  - 每 10 tick 发一次 ThrustPayload，服务端 ServerPlayNetworking 接收后调用 JetpackMod.triggerThrust（与手持右键共用 THRUST 60 tick / 雪粒子 / 同步）；
  - 手持 jetpack 右键路径保留：JetpackItem#use 仍直接调用 triggerThrust；
- fabric.mod.json 增加 client entrypoint skylands262.jetpack.JetpackClient；
- 候选：g156/stage-final/mods-candidate/sky262-jetpack-1.0.0.jar，SHA 11a738db6ab0135de4e5966616d8e6c9b3907d96920a1ecb131482caa131fad3，staging 116 jar；
- probe：穿 jetpack → 空手长按右键 → y 持续上升；卸下后空手右键不推；手持右键仍推。
