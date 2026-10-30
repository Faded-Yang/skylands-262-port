#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 tools/create_bridge_table.json（桥接表）。改这里，别手改 JSON。"""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "create_bridge_table.json"
INST = "com/mojang/serialization/codecs/RecordCodecBuilder$Instance"
APP = "Lcom/mojang/datafixers/kinds/App;"

rows = []

# 1) BlockBehaviour$Properties.isViewBlocking(StatePredicate) -> StateArgumentPredicate<AABB>
rows.append({
    "owner": "net/minecraft/world/level/block/state/BlockBehaviour$Properties",
    "name": "isViewBlocking",
    "desc": "(Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;",
    "bridge": "dev/eriksonn/aeronautics/compat/BlockPropertiesBridge",
    "new_desc": "(Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;Lnet/minecraft/world/level/block/state/BlockBehaviour$StatePredicate;)Lnet/minecraft/world/level/block/state/BlockBehaviour$Properties;",
    "opcode": "virtual",
    "note": "26.3: StatePredicate -> StateArgumentPredicate<AABB>",
})

# 2) DFU 10 删了 Instance.group(App...) -> 用 CodecGroupBridge 还原 Products.PN
for n in (1, 2, 3, 4, 5, 6, 8, 12, 15):
    rows.append({
        "owner": INST,
        "name": "group",
        "desc": "(" + APP * n + ")Lcom/mojang/datafixers/Products$P%d;" % n,
        "bridge": "dev/eriksonn/aeronautics/compat/CodecGroupBridge",
        "new_desc": "(Lcom/mojang/serialization/codecs/RecordCodecBuilder$Instance;" + APP * n
                    + ")Lcom/mojang/datafixers/Products$P%d;" % n,
        "opcode": "interface",
        "note": "DFU10 removed Instance.group; group = Products.PN tuple",
    })

# 3) PoseStack.mulPose(Quaternionfc) -> rotate(Quaternionfc)：240 处 / 86 类
#    26.3 只改了四元数版；mulPose(Matrix4fc) 与 mulPose(Transformation) 还在，别一起改
POSE = "com/mojang/blaze3d/vertex/PoseStack"
rows.append({
    "owner": POSE,
    "name": "mulPose",
    "desc": "(Lorg/joml/Quaternionfc;)V",
    "bridge": "dev/eriksonn/aeronautics/compat/PoseStackBridge",
    "new_desc": "(L" + POSE + ";Lorg/joml/Quaternionfc;)V",
    "opcode": "virtual",
    "note": "26.3: mulPose(Quaternionfc) -> rotate(Quaternionfc)",
})

# 4) Inventory.placeItemBackInInventory(ItemStack) -> (ItemStack, Prediction)：64 处 / 44 类
INV = "net/minecraft/world/entity/player/Inventory"
STACK = "Lnet/minecraft/world/item/ItemStack;"
rows.append({
    "owner": INV,
    "name": "placeItemBackInInventory",
    "desc": "(" + STACK + ")V",
    "bridge": "dev/eriksonn/aeronautics/compat/InventoryBridge",
    "new_desc": "(L" + INV + ";" + STACK + ")V",
    "opcode": "virtual",
    "note": "26.3 多了 Prediction 参数；桥接取 PREDICTED",
})

OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("wrote %s: %d entries" % (OUT, len(rows)))
