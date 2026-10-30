#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐新增 mod 带来的 22 条中文缺口（dungeons_arise 14 / mss 7 / modmenu 1）。"""
import json
import os
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-stable"

ZH = {
"dungeons_arise": {
 "advancement.dungeons_arise.find_kisegi_sanctuary.title": "与魔同悲",
 "advancement.dungeons_arise.find_kisegi_sanctuary.desc": "找到 Kisegi 圣所",
 "advancement.dungeons_arise.find_mining_complex.title": "喂饱机器",
 "advancement.dungeons_arise.find_mining_complex.desc": "找到采矿复合体",
 "enchantment.dungeons_arise.purification": "净化",
 "enchantment.dungeons_arise.purification.desc": "有几率抵消所有来袭的中毒与凋零效果，并释放一股能量冲击，伤害附近的敌人。",
 "enchantment.dungeons_arise.voltaic_shot": "电光射击",
 "enchantment.dungeons_arise.voltaic_shot.desc": "为箭矢充注电能，使其沿直线飞行并引发爆炸。",
 "enchantment.dungeons_arise.discharge": "放电",
 "enchantment.dungeons_arise.discharge.desc": "攻击敌人会累积速度，但速度过高时会以剧烈爆炸的形式释放，同时伤害受害者和攻击者。",
 "enchantment.dungeons_arise.lolths_curse": "罗丝的诅咒",
 "enchantment.dungeons_arise.lolths_curse.desc": "攻击敌人时有几率恢复生命，但蜘蛛可能从它们体内涌出。伤害节肢生物会将伤害反弹给持有者。",
 "enchantment.dungeons_arise.ensnaring": "诱捕",
 "enchantment.dungeons_arise.ensnaring.desc": "伤害敌人时有几率施加更强的缓慢效果，并召唤尖牙攻击其周围的所有怪物。",
},
"mss": {
 "modmenu.nameTranslation.mss": "MSS - Moog 的翱翔结构",
 "modmenu.summaryTranslation.mss": "大量原版风格的浮空岛，遍布战利品、怪物与地牢，等你探索！",
 "modmenu.descriptionTranslation.mss": (
   "Moog 的翱翔结构为你的 Minecraft 世界带来生机、乐趣与多样性：添加大量带有精巧建筑与更多内容的浮空岛！"
   "探索用原版方块与实体打造的全新结构，沿途发现战利品、敌人与村民。本模组兼容任意整合包，甚至可以只装在服务端！"),
 "mss.releases": "GitHub 发布页",
 "mss.kofi": "Ko-fi 赞助",
 "mss.curseforge": "CurseForge",
 "mss.modrinth": "Modrinth",
},
"modmenu": {
 "option.modmenu.show_libraries.with_config": "含配置项",
},
}

JARS = {
 "dungeons_arise": "DungeonsArise-2.1.68-26.3.jar",
 "mss": "MoogsSoaringStructures-2.2.0-26.3.jar",
 "modmenu": "modmenu-21.0.0.jar",
}

for ns, kv in ZH.items():
    jar = os.path.join(BASE, JARS[ns])
    if not os.path.exists(jar):
        print("  ★ 找不到", jar); continue
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
    shutil.copy2(jar, jar + ".bak-zh-r378")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as w:
        for n, b in data.items():
            w.writestr(n, b)
    print("  %-36s %d -> %d 条（新增 %d）" % (ns, before, len(cur), added))
print("完成")
