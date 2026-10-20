# fix-fluidstack-maxamount（create-fly 26.3 Optional cast）

> P0 链条：ponder `experience/basic`（crushing_wheel）在 1.0.5 修好 SOF 后，下一 tick 撞 FluidStack ClassCastException。

## 现象
- `CEITransfer.insertMillibuckets → FluidInventory.insert → FluidStack.getMaxAmount`：
  `ClassCastException: class java.util.Optional cannot be cast to class java.lang.Integer`；
- 影响所有 `FluidInventory.insert` 路径（CEI transfer、流体机器），不只 ponder。

## 根因
- create-fly 26.3 补丁的 `FluidStack.getMaxAmount` 仍 `(Integer) getOrDefault(...)`；运行期 `getOrDefault` 返回 `Optional`（组件缺失/包装值）时 cast 失败。

## 止损（crashfix 1.0.6）
- `FluidStackMaxAmountGuardMixin`：`getMaxAmount` HEAD 用安全转换，兼容 `Integer` / `Optional<Integer>` / 缺失值，返回默认 `Integer.MAX_VALUE`；
- 在 1.0.5 基础上加，保留 isKeyDown bridge + ClientLevel/ThreadLocal 守卫；
- 件：`g70/out/sky262crashfix-1.0.6.jar`，**9,668 B，SHA256 `41864f485ce256f95c1a0bf3e3e764eeb56ceb3166a10fcd049bd396c795d4fd`**；staging `g70/stage/ponder-fluid-final`（base live 114）。

## 备注
- 备选是 create-fly lane 直接改 1 行；若 create-fly 出件，本 Mixin 可作废；
- `FluidStack.getName` 还有 2 处同类 cast 风险，若后续崩再补。