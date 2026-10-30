# 所有长按交互方块：清单与逐块状态（task-38）

> 用户要求：所有需要长按交互的部件都要修好+验证，不能只算油门杆/组装器。
> 以油门杆（ThrottleLeverBlock / ThrottleLeverHandler）为基准：已 active 时 useWithoutItem 返回 InteractionResult.FAIL，
> 不重复 startHold、不重复 SUCCESS（因此不会重复手部 swing，也不会重置进度）。

## 1. 枚举结果（javap 超类 + 常量池引用扫描：aeronautics / sable / create-fly）

BlockHoldInteraction 子类（全部在 aeronautics，sable/create-fly 为 0）：

| 交互类 | 方块 / 载体 | useWithoutItem 当前写法 | 状态 |
|---|---|---|---|
| ThrottleLeverHandler | simulated:throttle_lever | `!isActive()` 才 startHold+SUCCESS，否则 FAIL | 基准，本来就正常 |
| PhysicsAssemblerGUIHandler | simulated:physics_assembler | 原：无条件 startHold+SUCCESS | R429 已修（active 时 FAIL），已验证 fraction 单调 |
| ClientHandleHandler | simulated:handle（手摇曲柄） | 待逐行核对（HandleBlock.useWithoutItem） | 待查/待修 |
| SteeringWheelHandler | simulated:steering_wheel | 待逐行核对（SteeringWheelBlock.useWithoutItem） | 待查/待修 |

说明：用户反馈「模拟拉杆和手摇曲柄交互动画没问题」可作基准参考，但代码层仍要确认它们是否也走无条件 startHold；
若它们已像油门杆一样判断 isActive，则无需改；否则按同模式补 FAIL 分支。

## 2. 已落地的通用护栏（R429，holdfix3）

- HoldInteractionManager.start：active == 传入 interaction 实例 -> 直接 return（不 stop/start 重置）；
- BlockHoldInteraction.startHold：isActive() 且同 blockPos -> 直接 return；
- PhysicsAssemblerBlock.useWithoutItem：clientSide/isLocalPlayer 且 manager 已 active -> 返回 FAIL。
这三条是通用护栏，对所有子类生效；差异只在各 Block.useWithoutItem 是否重复 startHold/返回 SUCCESS。

## 3. 下一步（本轮未完成）

1. 逐行核对 HandleBlock / SteeringWheelBlock 的 useWithoutItem（javap 字节码或源码），按油门杆模式对齐（active 时 FAIL、不重复 startHold）；
2. 出 holdfix4（base live aeronautics CC3FC28E），只改需要的 Block 类；-Xverify:all；staging g52/stage/mods-aero-holdfix4；
3. probe 清单验证（每块：按住 60 tick -> fraction 单调、无清零、release 停止、手部不反复；throttle/handle 为基准对照）：
   - simulated:throttle_lever（基准）
   - simulated:physics_assembler（R429 已验）
   - simulated:handle
   - simulated:steering_wheel
4. 手部动画验收：26.3 反射读不到 player.swinging/getAttackAnim，只能实机或逐帧连拍；默认以 fraction 单调 + release 停止为程序判据，肉眼动画交用户实机确认。

## 4. 相关任务

- A（真实鼠标 release/drag）：R428 holdinput 已 promote，用户实机验。
- B（sublevel 组装器真实右键）：pick 已修（v7 world 坐标），剩余 = 服务端 plot 方块解析（Lead 拍板优先补服务端代理）。
