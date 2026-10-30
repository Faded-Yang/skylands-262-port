#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐最后 40 条中文缺口（farmersdelight 32 / chefsdelight 4 / createframed 3 / corndelight 1）。"""
import json
import os
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable"

ZH = {
"farmersdelight": {
 "block.farmersdelight.pale_oak_cabinet": "苍白橡木橱柜",
 "block.farmersdelight.poplar_cabinet": "白杨木橱柜",
 "block.farmersdelight.straw_bed": "稻草床",
 "block.farmersdelight.hay_bed": "干草床",
 "item.farmersdelight.copper_knife": "铜刀",
 "gui.jei.category.smelting.time.seconds": "%s 秒",
 "gui.jei.category.smelting.experience": "%s 经验",
 "tag.block.farmersdelight.cabinets.wooden": "木质橱柜",
 "tag.block.farmersdelight.mineable.knife": "可用刀挖掘",
 "farmersdelight.configuration.enableVanillaStrawBedRename": "重命名原版稻草床",
 "farmersdelight.configuration.enableStrawBedRename.tooltip": "启用后，原版「稻草床」将被重命名为「干草床」——因为它显然不是稻草做的。",
 "gui.farmersdelight.open_mod_page": "打开模组页面",
 "farmersdelight.configuration.open_mod_page": "打开 %s 的 CurseForge 页面",
 "tag.block.farmersdelight.does_not_survive.rich_soil": "沃土",
 "tag.block.farmersdelight.does_not_survive.rich_soil_farmland": "沃土耕地",
 "tag.block.farmersdelight.survives.rich_soil": "沃土",
 "tag.block.farmersdelight.survives.rich_soil_farmland": "沃土耕地",
 "tag.entity_type.farmersdelight.drops_leather": "掉落皮革",
 "tag.worldgen.farmersdelight.biome.has_brown_mushroom_colony": "有棕色蘑菇群",
 "tag.worldgen.farmersdelight.biome.has_red_mushroom_colony": "有红色蘑菇群",
 "tag.worldgen.farmersdelight.biome.has_wild_beetroots": "有野生甜菜根",
 "tag.worldgen.farmersdelight.biome.has_wild_cabbage": "有野生卷心菜",
 "tag.worldgen.farmersdelight.biome.wild_carrots_blacklist": "野生胡萝卜黑名单",
 "tag.worldgen.farmersdelight.biome.wild_carrots_whitelist": "野生胡萝卜白名单",
 "tag.worldgen.farmersdelight.biome.wild_onions_blacklist": "野生洋葱黑名单",
 "tag.worldgen.farmersdelight.biome.wild_onions_whitelist": "野生洋葱白名单",
 "tag.worldgen.farmersdelight.biome.wild_potatoes_blacklist": "野生马铃薯黑名单",
 "tag.worldgen.farmersdelight.biome.wild_potatoes_whitelist": "野生马铃薯白名单",
 "tag.worldgen.farmersdelight.biome.wild_rice_blacklist": "野生稻米黑名单",
 "tag.worldgen.farmersdelight.biome.wild_rice_whitelist": "野生稻米白名单",
 "tag.worldgen.farmersdelight.biome.wild_tomatoes_blacklist": "野生番茄黑名单",
 "tag.worldgen.farmersdelight.biome.wild_tomatoes_whitelist": "野生番茄白名单",
},
"chefsdelight": {
 "entity.minecraft.villager.chef": "厨师",
 "entity.minecraft.villager.cook": "厨子",
 "entity.minecraft.villager.chefsdelight.chef": "厨师",
 "entity.minecraft.villager.chefsdelight.cook": "厨子",
},
"createframed": {
 "advancement.createframed.pulp_block.title": "纸浆化",
 "advancement.createframed.pulp_block.description": "产出（也许是意外产出）一块纸浆块\n§7（隐藏进度）",
 "block.createframed.pulp_block": "纸浆块",
},
"corndelight": {
 "itemGroup.corndelight": "玉米乐事",
},
}

JARS = {
 "farmersdelight": "FarmersDelight-26.3-3.6.28+refabricated.jar",
 "chefsdelight": "chefsdelight-1.0.6-26.3.jar",
 "createframed": "createframed-1.7.3-26.3.jar",
 "corndelight": "corndelight-1.0.0-26.3.jar",
}

for ns, kv in ZH.items():
    jar = os.path.join(BASE, JARS[ns])
    if not os.path.exists(jar):
        print("  ★ 找不到", JARS[ns]); continue
    z = zipfile.ZipFile(jar)
    data = {n: z.read(n) for n in z.namelist()}
    z.close()
    path = "assets/%s/lang/zh_cn.json" % ns
    cur = {}
    if path in data:
        try:
            cur = json.loads(data[path].decode("utf-8", "replace"))
        except Exception:
            cur = {}
    before = len(cur)
    added = 0
    for k, v in kv.items():
        if k not in cur:
            added += 1
        cur[k] = v
    data[path] = (json.dumps(dict(sorted(cur.items())), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    shutil.copy2(jar, jar + ".bak-zh-final")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    print("  %-20s %d -> %d 条（新增 %d）" % (ns, before, len(cur), added))
print("完成")
