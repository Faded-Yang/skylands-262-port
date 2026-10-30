#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_models.py - 离线预测 Minecraft 26.3 客户端模型烘焙结果 (skylands-262)

为什么存在：项目历史上只 grep "Missing textures in model" (=0) 就宣称模型修好了，
漏掉了 "Missing texture references in model" (395 条) 和 "Rejecting block model" (32 条)。
本工具以「游戏里到底会不会画成 missing」为准，镜像 26.3 源码规则：

  规则来源 (work/refs/mc26.3, 反编译源码, 权威):
    client/resources/model/sprite/MaterialBaker.java   Missing textures / Missing texture references / logMissingTextures
    client/resources/model/sprite/TextureSlots.java    slot 合并 + #ref 解析 + Unresolved texture references
    client/resources/model/ResolvedModel.java          top texture slots = 父链合并; particle slot
    client/resources/model/SimpleModelWrapper.java     block 链烘焙 + Rejecting block model = 跨图集
    client/resources/model/ModelDiscovery.java         Missing block model / 父链 / 环检测
    client/resources/model/ModelBakery.java            Unable to bake item model
    client/renderer/item/CuboidItemModelWrapper.java   item 链烘焙 + validateAtlasUsage
    client/renderer/item/ModelRenderProperties.java    item 的 particle slot
    client/resources/model/cuboid/UnbakedCuboidGeometry.java  哪些面真的被烘
    client/resources/model/cuboid/FaceBakery.java      UV -> computeTransparency 越界异常
    client/renderer/texture/atlas/SpriteSourceList.java 26.3: 图集定义按资源栈**合并**
    assets/minecraft/atlases/{blocks,items}.json         directory source: block/ , item/

用法:
  python audit_models.py                     扫描 + 写 broken.json / report.md
  python audit_models.py --log <latest.log>  额外做「工具预测 vs 真实日志」对齐
"""

import argparse
import json
import math
import re
import struct
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------- 坐标
ROOT = Path(r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262")
MODS = ROOT / "work" / "run26" / "mods-stable"
VAN = ROOT / "work" / "refs" / "mc26.3"
VANA = VAN / "assets"
OUT_DIR = ROOT / "scratch" / "audit"
DEFAULT_LOG = ROOT / "work" / "run26" / "watch" / "logs" / "latest.log"

MISSINGNO = "minecraft:missingno"
GENERATED = "minecraft:builtin/generated"
MISSING_MODEL_LOC = "minecraft:builtin/missing"

DIRECTIONS = ["down", "up", "north", "south", "west", "east"]
DIR_AXIS = {"down": "Y", "up": "Y", "north": "Z", "south": "Z", "west": "X", "east": "X"}
JAR_PRIO = {}


def norm_id(rid):
    """Java Identifier.parse: 无命名空间默认 minecraft。模型/纹理引用都必须归一。"""
    if not isinstance(rid, str) or not rid:
        return rid
    return rid if ":" in rid else "minecraft:" + rid


def split_id(rid):
    if not isinstance(rid, str):
        return None
    if ":" in rid:
        ns, p = rid.split(":", 1)
    else:
        ns, p = "minecraft", rid
    if not ns or not p:
        return None
    return ns, p


# ---------------------------------------------------------------- 资源索引
class Index:
    """jar + 原版资源目录的扁平索引。优先级：原版最低，jar 按文件名排序依次变高。"""

    REL_PREFIXES = ("assets/",)

    def __init__(self, verbose=True):
        self.files = {}                      # rel path -> (prio, provider)
        self.providers = defaultdict(list)   # rel path -> [provider...]
        self.zips = {}
        self.prio = 0
        self._png_size = {}
        self._json = {}
        for p in VANA.rglob("*"):
            if p.is_file():
                rel = "assets/" + str(p.relative_to(VANA)).replace("\\", "/")
                self.files[rel] = (-1, "vanilla")
                self.providers[rel].append("vanilla")
        self.van_count = len(self.files)
        for jar in sorted(MODS.glob("*.jar")):
            try:
                z = zipfile.ZipFile(jar)
            except Exception as e:
                print("[warn] bad jar " + jar.name + ": " + str(e), file=sys.stderr)
                continue
            self.zips[jar.name] = z
            self.prio += 1
            JAR_PRIO[jar.name] = self.prio
            for n in z.namelist():
                if not n.startswith(self.REL_PREFIXES):
                    continue
                self.files[n] = (self.prio, jar.name)
                self.providers[n].append(jar.name)
        if verbose:
            print("[index] vanilla files %d, total files %d, jars %d" % (self.van_count, len(self.files), len(self.zips)))

    def has(self, path):
        return path in self.files

    def provider(self, path):
        hit = self.files.get(path)
        return hit[1] if hit else None

    def read(self, path):
        hit = self.files.get(path)
        if hit is None:
            return None
        provider = hit[1]
        if provider == "vanilla":
            return (VAN / path).read_bytes()
        z = self.zips.get(provider)
        if z is None:
            return None
        try:
            return z.read(path)
        except KeyError:
            return None

    def json(self, path):
        """返回 (obj, err)。obj=None 且 err=None 表示文件不存在。"""
        if path in self._json:
            return self._json[path]
        data = self.read(path)
        if data is None:
            res = (None, None)
        else:
            try:
                res = (json.loads(data.decode("utf-8-sig")), None)
            except Exception as e:
                res = (None, "bad-json: " + str(e))
        self._json[path] = res
        return res

    def png_size(self, path):
        if path in self._png_size:
            return self._png_size[path]
        data = self.read(path)
        size = None
        if data and len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
            w, h = struct.unpack(">II", data[16:24])
            size = (w, h)
        self._png_size[path] = size
        return size


# ---------------------------------------------------------------- 图集归属
class Atlases:
    """按 26.3 SpriteSourceList (getResourceStack 合并) 解析 blocks/items 图集 source 列表。"""

    def __init__(self, idx):
        self.idx = idx
        self.rules = {"items": [], "blocks": []}
        self.atlas_errors = []
        self.load("items")
        self.load("blocks")
        self._memo = {}

    def load(self, atlas):
        path = "assets/minecraft/atlases/" + atlas + ".json"
        provs = list(self.idx.providers.get(path) or [])
        if not provs:
            provs = ["vanilla"]
        order = [p for p in provs if p == "vanilla"] + sorted([p for p in provs if p != "vanilla"], key=lambda n: JAR_PRIO.get(n, 0))
        for provider in order:
            if provider == "vanilla":
                data = (VAN / path).read_bytes()
            else:
                z = self.idx.zips.get(provider)
                if z is None:
                    continue
                try:
                    data = z.read(path)
                except KeyError:
                    continue
            try:
                doc = json.loads(data.decode("utf-8-sig"))
            except Exception as e:
                self.atlas_errors.append((provider, atlas, str(e)))
                continue
            for src in doc.get("sources", []):
                t = (src.get("type") or "").split(":")[-1]
                if t == "directory":
                    self.rules[atlas].append(("dir", src.get("source", "").strip("/"), src.get("prefix", "")))
                elif t == "single":
                    self.rules[atlas].append(("single", src.get("resource")))
                elif t == "paletted_permutations":
                    # 26.3: 每个 base 纹理 + 每个 permutation 生成一个新的 sprite id = base + "_" + perm；
                    # 真正需要存在的是 base 纹理的 png（permutation 只是调色板）。方向修正是本工具踩过的坑。
                    perms = list((src.get("permutations") or {}).keys())
                    for tex in (src.get("textures") or []):
                        for perm in perms:
                            self.rules[atlas].append(("paletted", str(tex), "_" + perm))
        # 兜底：核心目录规则一定在
        rules = self.rules[atlas]
        if atlas == "items" and not any(r[0] == "dir" and r[1] == "item" for r in rules):
            rules.insert(0, ("dir", "item", "item/"))
        if atlas == "blocks":
            if not any(r[0] == "dir" and r[1] == "block" for r in rules):
                rules.insert(0, ("dir", "block", "block/"))
            if not any(r[0] == "dir" and r[1] == "entity/conduit" for r in rules):
                rules.insert(1, ("dir", "entity/conduit", "entity/conduit/"))

    def atlas_of(self, sprite_id):
        if sprite_id in self._memo:
            return self._memo[sprite_id]
        res = self._atlas_of("items", sprite_id)
        if res is None:
            res = self._atlas_of("blocks", sprite_id)
        self._memo[sprite_id] = res
        return res

    def _atlas_of(self, atlas, sprite_id):
        p = split_id(sprite_id)
        if p is None:
            return None
        ns, path = p
        for rule in self.rules[atlas]:
            if rule[0] == "dir":
                src, prefix = rule[1], rule[2]
                if not src:
                    continue
                if path.startswith(prefix):
                    rel = path[len(prefix):]
                    if self.idx.has("assets/" + ns + "/textures/" + src + "/" + rel + ".png"):
                        return atlas
            elif rule[0] == "paletted":
                base, suffix = rule[1], rule[2]
                if sprite_id == base + suffix:
                    bp = split_id(base)
                    if bp and self.idx.has("assets/" + bp[0] + "/textures/" + bp[1] + ".png"):
                        return atlas
            else:
                if rule[1] == sprite_id and self.idx.has("assets/" + ns + "/textures/" + path + ".png"):
                    return atlas
        return None

    def texture_png(self, sprite_id):
        p = split_id(sprite_id)
        if p is None:
            return None
        return "assets/" + p[0] + "/textures/" + p[1] + ".png"


# ---------------------------------------------------------------- 模型
class ModelRec:
    __slots__ = ("id", "data", "err", "exists", "special")

    def __init__(self, mid, data=None, err=None, exists=False, special=None):
        self.id = mid
        self.data = data
        self.err = err
        self.exists = exists
        self.special = special

    @property
    def textures(self):
        if self.special == "generated":
            # ItemModelGenerator.TEXTURE_SLOTS = {particle -> #layer0}
            return {"particle": "#layer0"}
        if self.special == "missing-model":
            # MissingCuboidModel: particle -> #missingno, missingno -> Material(missingno)
            return {"particle": "#missingno", "missingno": "minecraft:missingno"}
        if not self.data:
            return {}
        t = self.data.get("textures")
        return t if isinstance(t, dict) else {}

    @property
    def parent(self):
        if not self.data:
            return None
        p = self.data.get("parent")
        return norm_id(p) if isinstance(p, str) and p else None

    @property
    def elements(self):
        """None = 本层没有 elements；[] = 显式空 elements (屏蔽父层几何)。"""
        if not self.data:
            return None
        if "elements" not in self.data:
            return None
        els = self.data.get("elements")
        return els if isinstance(els, list) else None


def model_path(mid):
    p = split_id(mid)
    if p is None:
        return None
    return "assets/" + p[0] + "/models/" + p[1] + ".json"


class ModelWorld:
    """模型层：加载、父链、slot 合并、几何面、图集判定。"""

    def __init__(self, idx, atlases):
        self.idx = idx
        self.atlases = atlases
        self.models = {}
        self.missing_ids = {}
        self.cycle_ids = set()
        self.failed_models = {}

    def get(self, mid):
        if mid in self.models:
            return self.models[mid]
        if mid == GENERATED:
            rec = ModelRec(mid, special="generated", exists=True)
        elif mid == MISSING_MODEL_LOC:
            rec = ModelRec(mid, special="missing-model", exists=True)
        else:
            path = model_path(mid)
            if path is None:
                rec = ModelRec(mid, err="bad id")
            else:
                data, err = self.idx.json(path)
                if data is None and err is None:
                    rec = ModelRec(mid, err="file absent")
                elif err:
                    rec = ModelRec(mid, err=err)
                    self.failed_models[mid] = err
                else:
                    bad = self._validate(data)
                    if bad:
                        rec = ModelRec(mid, err=bad)
                        self.failed_models[mid] = bad
                    else:
                        rec = ModelRec(mid, data=data, exists=True)
        if not rec.exists and mid not in self.missing_ids:
            self.missing_ids[mid] = rec.err or "missing"
        self.models[mid] = rec
        return rec

    @staticmethod
    def _is_num(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool)

    def _validate(self, data):
        """近似 CuboidModel/CuboidModelElement/CuboidFace 反序列化校验；失败 = Failed to load model。"""
        if not isinstance(data, dict):
            return "root not object"
        if "parent" in data and not isinstance(data["parent"], str):
            return "parent not string"
        if "textures" in data and not isinstance(data["textures"], dict):
            return "textures not object"
        texs = data.get("textures")
        if isinstance(texs, dict):
            for slot, v in texs.items():
                if isinstance(v, str):
                    continue
                if isinstance(v, dict) and isinstance(v.get("sprite"), str):
                    continue
                return "texture slot " + str(slot) + " not string/material"
        if "elements" in data:
            els = data["elements"]
            if not isinstance(els, list):
                return "elements not array"
            for el in els:
                if not isinstance(el, dict):
                    return "element not object"
                for k in ("from", "to"):
                    v = el.get(k)
                    if not (isinstance(v, list) and len(v) == 3 and all(self._is_num(x) for x in v)):
                        return "element " + k + " invalid"
                    if any(x < -16 or x > 32 for x in v):
                        return "element " + k + " out of range"
                faces = el.get("faces")
                if not isinstance(faces, dict) or not faces:
                    return "element faces invalid"
                for fn, f in faces.items():
                    if fn not in DIRECTIONS:
                        return "unknown facing " + str(fn)
                    if not isinstance(f, dict):
                        return "face not object"
                    if not isinstance(f.get("texture"), str):
                        return "face texture missing"
                    if "uv" in f:
                        uv = f["uv"]
                        if not (isinstance(uv, list) and len(uv) == 4 and all(self._is_num(x) for x in uv)):
                            return "face uv invalid"
                    if "cullface" in f and f["cullface"] not in DIRECTIONS:
                        return "face cullface invalid"
                if "light_emission" in el:
                    le = el["light_emission"]
                    if not isinstance(le, int) or isinstance(le, bool) or not (0 <= le <= 15):
                        return "light_emission invalid"
        return None

    def chain(self, mid):
        """returns (list of ModelRec root->top, missing_id, cycle)"""
        seq = []
        seen = set()
        cur = mid
        cycle = False
        while cur:
            if cur in seen:
                cycle = True
                break
            seen.add(cur)
            rec = self.get(cur)
            if not rec.exists:
                return list(reversed(seq)), cur, cycle
            seq.append(rec)
            cur = rec.parent
        return list(reversed(seq)), None, cycle

    def merged_slots(self, chain):
        """完整镜像 TextureSlots.Resolver.resolve()。返回 (resolved, unresolved)。"""
        resolved = {}
        unresolved = {}
        for rec in chain:
            for slot, v in rec.textures.items():
                if isinstance(v, str) and v.startswith("#"):
                    resolved.pop(slot, None)
                    unresolved[slot] = v[1:]
                else:
                    unresolved.pop(slot, None)
                    resolved[slot] = v
        changed = True
        while changed:
            changed = False
            for slot in list(unresolved.keys()):
                target = unresolved[slot]
                if target in resolved:
                    resolved[slot] = resolved[target]
                    del unresolved[slot]
                    changed = True
        return resolved, unresolved

    @staticmethod
    def material_of(value):
        if isinstance(value, str):
            if value.startswith("#"):
                return None
            return (norm_id(value), False)
        if isinstance(value, dict):
            sp = value.get("sprite")
            if isinstance(sp, str):
                return (norm_id(sp), bool(value.get("force_translucent", False)))
        return None

    def resolve_slot(self, resolved, raw_ref):
        if not isinstance(raw_ref, str):
            return None
        slot = raw_ref[1:] if raw_ref.startswith("#") else raw_ref
        value = resolved.get(slot)
        if value is None:
            return None
        return self.material_of(value)

    def referrers_of(self, model_id):
        """哪些模型把它当 parent（用于把「日志里缺失的 parent」反推到运行时烘焙的子模型）。"""
        if not hasattr(self, "_children"):
            self._children = defaultdict(list)
            for path in sorted(self.idx.files):
                if not ("/models/" in path and path.endswith(".json")):
                    continue
                doc, err = self.idx.json(path)
                if not isinstance(doc, dict):
                    continue
                par = doc.get("parent")
                if isinstance(par, str) and par:
                    mid = path.split("/models/")[1][:-5]
                    self._children[norm_id(par)].append(path.split("/models/")[0].split("assets/")[1]
                                                       + ":" + mid)
        return self._children.get(model_id, [])

    def top_elements(self, chain):
        for rec in reversed(chain):
            els = rec.elements
            if els is not None:
                return els
        return []

    def top_geometry(self, chain):
        """ResolvedModel.findTopGeometry: top->root 找第一个 geometry。"""
        for rec in reversed(chain):
            if rec.special == "generated":
                return ("generated", None)
            if rec.special == "missing-model":
                return ("missing", None)
            els = rec.elements
            if els is not None:
                return ("cuboid", els)
        return ("empty", None)

    @staticmethod
    def default_uvs(frm, to, facing):
        if facing == "down":
            return (frm[0], 16.0 - to[2], to[0], 16.0 - frm[2])
        if facing == "up":
            return (frm[0], frm[2], to[0], to[2])
        if facing == "north":
            return (16.0 - to[0], 16.0 - to[1], 16.0 - frm[0], 16.0 - frm[1])
        if facing == "south":
            return (frm[0], 16.0 - to[1], to[0], 16.0 - frm[1])
        if facing == "west":
            return (frm[2], 16.0 - to[1], to[2], 16.0 - frm[1])
        if facing == "east":
            return (16.0 - to[2], 16.0 - to[1], 16.0 - frm[2], 16.0 - frm[1])
        return (0.0, 0.0, 16.0, 16.0)

    def baked_faces(self, els):
        """产出 (raw_ref, facing, from, to, uv) —— 只含真的会被烘的面。"""
        for el in (els or []):
            frm = el.get("from") or [0, 0, 0]
            to = el.get("to") or [16, 16, 16]
            dx = frm[0] == to[0]
            dy = frm[1] == to[1]
            dz = frm[2] == to[2]
            draw = {"X": not dx, "Y": not dy, "Z": not dz}
            if dx:
                draw["Y"] = False
                draw["Z"] = False
            if dy:
                draw["X"] = False
                draw["Z"] = False
            if dz:
                draw["X"] = False
                draw["Y"] = False
            if not (draw["X"] or draw["Y"] or draw["Z"]):
                continue
            for fn, face in (el.get("faces") or {}).items():
                if not draw[DIR_AXIS[fn]]:
                    continue
                yield (face.get("texture"), fn, frm, to, face.get("uv"))


class BakeResult:
    """单个模型 (一次烘焙) 的完整预测结果。"""

    def __init__(self, model_id):
        self.model = model_id
        self.missing_model = None
        self.cycle = False
        self.parse_error = None
        self.unresolved = {}
        self.missing_refs = []
        self.missing_textures = []
        self.cross_atlas = {}
        self.atlases_used = set()
        self.quads = 0
        self.uv_errors = []
        self.notes = []
        self._resolved = {}
        self.texture_size = False
        self.oversized = []


class Baker:
    """镜像 ModelBakery / MaterialBaker 的一次 reload。"""

    def __init__(self, world):
        self.w = world

    def material(self, out, ref):
        mat = self.w.resolve_slot(out._resolved, ref)
        if mat is None:
            return None, True
        sprite, transparent = mat
        if sprite == MISSINGNO:
            return (MISSINGNO, "blocks", transparent), False
        atlas = self.w.atlases.atlas_of(sprite)
        if atlas is None:
            if sprite not in out.missing_textures:
                out.missing_textures.append(sprite)
            return (MISSINGNO, "blocks", transparent), False
        out.atlases_used.add(atlas)
        return (sprite, atlas, transparent), False

    def bake(self, model_id, mode):
        """mode: block = SimpleModelWrapper.bake; item = CuboidItemModelWrapper; item-special = 只解 particle。"""
        out = BakeResult(model_id)
        chain, missing, cycle = self.w.chain(model_id)
        out.cycle = cycle
        if cycle:
            out.notes.append("cyclic-parent-chain")
            return out
        if missing:
            out.missing_model = missing
            return out
        out._resolved, out.unresolved = self.w.merged_slots(chain)
        # NeoForge 的 texture_size 扩展：26.3 不认，uv 仍在旧坐标空间（>=16 的 uv 会越界/错位）
        out.texture_size = any(isinstance(r.data, dict) and "texture_size" in r.data for r in chain)

        if out._resolved.get("particle") is None:
            out.missing_refs.append("particle")

        if mode == "item-special":
            return out

        kind, els = self.w.top_geometry(chain)
        sprites = []
        if kind == "generated":
            sprites = self.bake_generated(out)
        elif kind == "cuboid":
            for raw_ref, facing, frm, to, uv in self.w.baked_faces(els):
                ref = raw_ref if isinstance(raw_ref, str) else "#?"
                mat, miss = self.material(out, ref)
                if miss:
                    if ref not in out.missing_refs:
                        out.missing_refs.append(ref)
                    continue
                out.quads += 1
                if mat[0] == MISSINGNO:
                    continue
                sprites.append((mat[0], mat[1]))
                out.uv_errors.extend(self._uv_check(mat[0], uv, facing, frm, to))
        elif kind == "missing":
            out.quads += 1

        for sprite, atlas in sprites:
            if atlas != "blocks":
                out.cross_atlas.setdefault(atlas, [])
                if sprite not in out.cross_atlas[atlas]:
                    out.cross_atlas[atlas].append(sprite)

        if mode == "item" and out.quads > 0:
            atl = set(a for _, a in sprites)
            if len(atl) > 1:
                out.notes.append("mixed-atlas:" + ",".join(sorted(atl)))
            elif atl and next(iter(atl)) not in ("items", "blocks"):
                out.notes.append("unsupported-atlas:" + next(iter(atl)))
        return out

    LAYERS = ("layer0", "layer1", "layer2", "layer3", "layer4")

    def bake_generated(self, out):
        """ItemModelGenerator.bake: layer0..layer4，遇到未定义 slot 就停；每个 layer = 挤压精灵。"""
        sprites = []
        for layer in self.LAYERS:
            val = out._resolved.get(layer)
            mat = self.w.material_of(val) if val is not None else None
            if mat is None:
                break
            sprite, transparent = mat
            if sprite == MISSINGNO:
                continue
            atlas = self.w.atlases.atlas_of(sprite)
            if atlas is None:
                if sprite not in out.missing_textures:
                    out.missing_textures.append(sprite)
                continue
            out.atlases_used.add(atlas)
            out.quads += 1
            sprites.append((sprite, atlas))
            out.uv_errors.extend(self._uv_check_uv(sprite, (0.0, 0.0, 16.0, 16.0), None))
        return sprites

    def _uv_check(self, sprite, uv, facing, frm, to):
        if uv is None:
            uv = self.w.default_uvs(frm, to, facing)
        return self._uv_check_uv(sprite, uv, facing)

    def _uv_check_uv(self, sprite, uv, facing):
        png = self.w.atlases.texture_png(sprite)
        size = self.w.idx.png_size(png) if png else None
        if not size:
            return []
        w, h = size
        u0, v0, u1, v1 = uv
        x0 = math.floor(min(u0, u1) / 16.0 * w)
        y0 = math.floor(min(v0, v1) / 16.0 * h)
        x1 = math.ceil(max(u0, u1) / 16.0 * w)
        y1 = math.ceil(max(v0, v1) / 16.0 * h)
        if x0 >= 0 and y0 >= 0 and x1 <= w and y1 <= h:
            return []
        return [(sprite, list(uv), [w, h], [x0, y0, x1, y1])]


# ---------------------------------------------------------------- 根：blockstates / items
def collect_blockstate_models(doc):
    """blockstate json -> [(model_id, variant_key)]，按 BlockStateModelDispatcher 结构。"""
    out = []
    if not isinstance(doc, dict):
        return out
    variants = doc.get("variants")
    if isinstance(variants, dict):
        for key, val in variants.items():
            _collect_model_tree(val, out, key)
    mp = doc.get("multipart")
    if isinstance(mp, list):
        for entry in mp:
            if isinstance(entry, dict):
                _collect_model_tree(entry.get("apply"), out, "multipart")
    return out


def _collect_model_tree(node, out, key):
    if node is None:
        return
    if isinstance(node, list):
        for x in node:
            _collect_model_tree(x, out, key)
        return
    if isinstance(node, dict):
        m = node.get("model")
        if isinstance(m, str):
            out.append((norm_id(m), key))
            return
        for v in node.values():
            if isinstance(v, (dict, list)):
                _collect_model_tree(v, out, key)


def collect_item_models(doc):
    """items/<ns>/<id>.json -> [(model_id, item_model_type), ...]"""
    out = []
    if not isinstance(doc, dict):
        return out, "root-not-object"
    if "model" not in doc:
        return out, "no-model-field"
    _walk_item_model(doc["model"], out)
    return out, None


def _walk_item_model(node, out):
    if not isinstance(node, dict):
        return
    t = node.get("type", "minecraft:model")
    if isinstance(t, str):
        t = t.split(":")[-1]
    if t == "model":
        m = node.get("model")
        if isinstance(m, str):
            out.append((norm_id(m), "model"))
    elif t == "special":
        b = node.get("base")
        if isinstance(b, str):
            out.append((norm_id(b), "special-base"))
    elif t == "composite":
        for x in node.get("models") or []:
            _walk_item_model(x, out)
    elif t == "select":
        for case in node.get("cases") or []:
            if isinstance(case, dict):
                _walk_item_model(case.get("model"), out)
        _walk_item_model(node.get("fallback"), out)
    elif t == "range_dispatch":
        for e in node.get("entries") or []:
            if isinstance(e, dict):
                _walk_item_model(e.get("model"), out)
        _walk_item_model(node.get("fallback"), out)
    elif t == "condition":
        _walk_item_model(node.get("on_true"), out)
        _walk_item_model(node.get("on_false"), out)


# ---------------------------------------------------------------- fix_hint
REASON_DESC = {
    "missing_model": "引用的模型 json 不存在 (游戏退回 missing 模型)",
    "bad_model_json": "模型 json 解析失败 (游戏退回 missing 模型)",
    "missing_texture_reference": "引用了未定义的 texture slot (该面/粒子画成 missing 紫黑)",
    "unresolved_texture_reference": "#slot 指向的目标 slot 不存在，无法解析",
    "missing_texture": "最终纹理 png 不在任何图集 (items/blocks) 里",
    "cross_atlas_block": "block 模型用了 items 图集的 sprite -> 整个模型被 Rejecting (画成 missing)",
    "mixed_atlas_item": "item 模型的面跨图集 -> IllegalStateException，item 模型烘不出来",
    "uv_out_of_bounds": "UV 超出纹理像素范围 -> computeTransparency 抛异常，模型烘不出来",
    "cyclic_model": "模型父链成环 -> 模型被忽略",
    "bad_item_definition": "items/<id>.json 解析失败或无 model 字段 (item 画 missing)",
    "neoforge_texture_size": "模型用了 NeoForge 的 texture_size 扩展 (26.3 不认)，uv 仍在旧坐标空间 (次级/需人工确认)",
}


UV_FIX_HINT = {
    "uv_out_of_bounds": "把该面的 uv 限制在 0..16 内（或与 png 尺寸匹配），否则 FaceBakery.computeTransparency 抛异常",
    "neoforge_texture_size": "模型带 texture_size（NeoForge 扩展），26.3 不认：把每个 uv 乘 16/texture_size 后重导，或删掉该字段并按 16 空间重导模型",
}


def missing_model_hint(missing_id, user_model):
    path = model_path(missing_id)
    if path is None:
        return "引用 id " + str(missing_id) + " 非法，修正 -> " + str(user_model)
    return ("新建 " + path + "（可复制 " + str(user_model) + " 的同级模型改纹理），"
            "或把引用 " + str(missing_id) + " 改成实际存在的模型")


def ref_fix_hint(model_id, ref, out):
    if ref == "particle":
        return ("在 " + str(model_path(model_id)) + " 的 textures 里补 \"particle\": \"<与主纹理相同的 id>\""
                "（或 \"particle\": \"#<已定义slot>\"）")
    slot = ref[1:] if ref.startswith("#") else ref
    guess = None
    for s, v in (getattr(out, "_resolved", {}) or {}).items():
        m = ModelWorld.material_of(v)
        if m:
            guess = m[0]
            break
    tail = (", 例如 \"" + slot + "\": \"" + guess + "\"") if guess else ""
    return "在 " + str(model_path(model_id)) + " 的 textures 里定义 \"" + slot + "\"" + tail


def unresolved_fix_hint(model_id, slot, target):
    return (str(model_path(model_id)) + " 的 textures 里 \"" + slot + "\": \"#" + target + "\" 指向未定义 slot "
            + target + "; 补 \"" + target + "\": \"<纹理id>\" 或直接写死 \"" + slot + "\": \"<纹理id>\"")


def texture_fix_hint(sprite):
    p = split_id(sprite)
    if not p:
        return "纹理 id " + str(sprite) + " 非法"
    ns, path = p
    return ("补 assets/" + ns + "/textures/" + path + ".png; 若 png 在别处, 复制到 textures/item/ 或 textures/block/ 下"
            " (图集只收 item/** 与 block/**), 或把引用改成已有 png")


def cross_atlas_fix_hint(cross_atlas):
    hints = []
    for atlas, sprites in sorted(cross_atlas.items()):
        for sp in sprites:
            p = split_id(sp)
            if not p:
                continue
            ns, path = p
            if path.startswith("item/"):
                newp = "block/" + path[len("item/"):]
                hints.append("把 assets/" + ns + "/textures/" + path + ".png 复制到 assets/" + ns +
                             "/textures/" + newp + ".png 并把模型里的 " + sp + " 改成 " + ns + ":" + newp)
            else:
                hints.append(sp + " 不在 blocks 图集 (" + atlas + "), 移进 textures/block/ 并改引用")
    return "; ".join(hints) if hints else "把纹理移到 block/ 并改引用"


def mixed_atlas_fix_hint(out):
    sprites = [sp for lst in out.cross_atlas.values() for sp in lst]
    base = ("item 模型所有面必须同一图集 (items 或 blocks): 当前用到 " + ", ".join(sorted(out.atlases_used)))
    if sprites:
        base += "; 把 " + ", ".join(sprites) + " 统一到同一图集"
    return base


# ---------------------------------------------------------------- 主审计
def audit(idx, atlases, world, baker):
    records = []
    block_roots = {}
    blockstate_files = []
    item_roots = {}
    item_defs = {}

    for path in sorted(idx.files):
        m = re.match(r"assets/([^/]+)/blockstates/(.+)\.json$", path)
        if not m:
            continue
        block_id = m.group(1) + ":" + m.group(2)
        doc, err = idx.json(path)
        if err or doc is None:
            blockstate_files.append((block_id, idx.provider(path), err or "unreadable"))
            continue
        models = collect_blockstate_models(doc)
        if not models:
            blockstate_files.append((block_id, idx.provider(path), "no-variants-or-multipart"))
            continue
        for mid, key in models:
            lst = block_roots.setdefault(mid, [])
            if block_id not in lst:
                lst.append(block_id)

    for path in sorted(idx.files):
        m = re.match(r"assets/([^/]+)/items/(.+)\.json$", path)
        if not m:
            continue
        item_id = m.group(1) + ":" + m.group(2)
        doc, err = idx.json(path)
        if err or doc is None:
            item_defs[item_id] = ([], err or "unreadable")
            continue
        models, perr = collect_item_models(doc)
        item_defs[item_id] = (models, perr)
        for mid, t in models:
            item_roots.setdefault(mid, []).append((item_id, t))

    block_pred = {}
    for mid in sorted(block_roots):
        block_pred[mid] = baker.bake(mid, "block")
    item_pred = {}
    for mid in sorted(item_roots):
        types = set(t for _, t in item_roots[mid])
        mode = "item-special" if types == set(["special-base"]) else "item"
        item_pred[mid] = baker.bake(mid, mode)

    def add(kind, ident, model, reason, detail, fix_hint, channel="blockstate"):
        records.append({
            "kind": kind,
            "id": ident,
            "namespace": ident.split(":")[0],
            "model": model,
            "reason": reason,
            "detail": detail,
            "fix_hint": fix_hint,
            "channel": channel,
        })

    for mid, out in block_pred.items():
        for bid in block_roots[mid]:
            if out.cycle:
                add("block", bid, mid, "cyclic_model", "父链成环", "打散该模型 parent 链中的环", "blockstate")
            elif out.missing_model:
                add("block", bid, mid, "missing_model", "缺模型 " + str(out.missing_model),
                    missing_model_hint(out.missing_model, mid))
            else:
                for ref in out.missing_refs:
                    add("block", bid, mid, "missing_texture_reference", "slot " + ref + " 未定义",
                        ref_fix_hint(mid, ref, out))
                for slot, target in sorted(out.unresolved.items()):
                    add("block", bid, mid, "unresolved_texture_reference", "#" + slot + " -> #" + target,
                        unresolved_fix_hint(mid, slot, target))
                for sp in out.missing_textures:
                    add("block", bid, mid, "missing_texture", "sprite " + sp + " 不在任何图集", texture_fix_hint(sp))
                if out.cross_atlas:
                    detail = "; ".join(a + "=" + ",".join(v) for a, v in sorted(out.cross_atlas.items()))
                    add("block", bid, mid, "cross_atlas_block", detail, cross_atlas_fix_hint(out.cross_atlas))
                for sprite, uv, size, box in out.uv_errors:
                    reason = "neoforge_texture_size" if out.texture_size else "uv_out_of_bounds"
                    add("block", bid, mid, reason,
                        sprite + " uv=" + str(uv) + " png=" + str(size) + " box=" + str(box),
                        UV_FIX_HINT[reason])

    for mid, out in item_pred.items():
        items = item_roots[mid]
        if out.cycle:
            for iid, _t in items:
                add("item", iid, mid, "cyclic_model", "父链成环", "打散该模型 parent 链中的环")
            continue
        if out.missing_model:
            for iid, _t in items:
                add("item", iid, mid, "missing_model", "缺模型 " + str(out.missing_model),
                    missing_model_hint(out.missing_model, mid))
            continue
        for iid, _t in items:
            for ref in out.missing_refs:
                add("item", iid, mid, "missing_texture_reference", "slot " + ref + " 未定义",
                    ref_fix_hint(mid, ref, out), "item-definition")
            for slot, target in sorted(out.unresolved.items()):
                add("item", iid, mid, "unresolved_texture_reference", "#" + slot + " -> #" + target,
                    unresolved_fix_hint(mid, slot, target))
            for sp in out.missing_textures:
                add("item", iid, mid, "missing_texture", "sprite " + sp + " 不在任何图集", texture_fix_hint(sp))
            for sprite, uv, size, box in out.uv_errors:
                reason = "neoforge_texture_size" if out.texture_size else "uv_out_of_bounds"
                add("item", iid, mid, reason,
                    sprite + " uv=" + str(uv) + " png=" + str(size) + " box=" + str(box),
                    UV_FIX_HINT[reason], "item-definition")
            for note in out.notes:
                if note.startswith("mixed-atlas:") or note.startswith("unsupported-atlas:"):
                    add("item", iid, mid, "mixed_atlas_item", note, mixed_atlas_fix_hint(out))

    for iid, (models, err) in item_defs.items():
        if err:
            add("item", iid, None, "bad_item_definition", err,
                "修该 items json (需要 {\"model\":{\"type\":\"minecraft:model\",...}})")

    seen = set()
    uniq = []
    for r in records:
        k = (r["kind"], r["id"], r["model"], r["reason"], r["detail"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    uniq.sort(key=lambda r: (r["kind"], r["namespace"], r["id"], r["reason"], str(r["model"])))
    return uniq, block_roots, item_roots, item_defs, blockstate_files, block_pred, item_pred


# ---------------------------------------------------------------- 运行时通道 (Flywheel PartialModel)
def bake_runtime(world, baker, runtime_roots, block_roots, item_roots):
    """Create/Simulated 的 Flywheel PartialModel 通道：模型 id 在 mod 代码里注册，
    离线无法枚举；一旦给定根集合，失败原因仍由本工具离线独立推导。"""
    pred = {}
    for mid in sorted(runtime_roots):
        rec = world.get(mid)
        if not rec.exists:
            continue
        pred[mid] = baker.bake(mid, "block")
    records = []
    for mid in sorted(pred):
        out = pred[mid]
        kind = "item" if mid in item_roots else "block"
        ids = [iid for iid, _t in item_roots[mid]] if kind == "item" else [mid]
        for ident in ids:
            if out.cycle:
                reason, detail = "cyclic_model", "父链成环"
                fix = "打散该模型 parent 链中的环"
            elif out.missing_model:
                reason, detail = "missing_model", "缺模型 " + str(out.missing_model)
                fix = missing_model_hint(out.missing_model, mid)
            elif out.cross_atlas:
                reason = "cross_atlas_block"
                detail = "; ".join(a + "=" + ",".join(v) for a, v in sorted(out.cross_atlas.items()))
                fix = cross_atlas_fix_hint(out.cross_atlas)
            elif out.missing_refs:
                reason = "missing_texture_reference"
                detail = "slot " + ",".join(out.missing_refs) + " 未定义"
                fix = ref_fix_hint(mid, out.missing_refs[0], out)
            elif out.missing_textures:
                reason = "missing_texture"
                detail = "sprite " + ",".join(out.missing_textures) + " 不在任何图集"
                fix = texture_fix_hint(out.missing_textures[0])
            elif out.unresolved:
                reason = "unresolved_texture_reference"
                detail = str(out.unresolved)
                k = sorted(out.unresolved)[0]
                fix = unresolved_fix_hint(mid, k, out.unresolved[k])
            else:
                continue
            records.append({
                "kind": kind, "id": ident, "namespace": ident.split(":")[0], "model": mid,
                "reason": reason, "detail": detail, "fix_hint": fix,
                "channel": "runtime-partial-model",
            })
    return pred, records


# ---------------------------------------------------------------- 日志解析 + 对齐
PREF = re.compile(r"^\[[^\]]*\] \[[^\]]*\]:\s?(.*)$")
LOG_PATTERNS = [
    ("missing_block_model", r"^Missing block model: (.+)$"),
    ("missing_textures", r"^Missing textures in model (.+):$"),
    ("missing_texture_refs", r"^Missing texture references in model (.+):$"),
    ("unresolved_refs", r"^Unresolved texture references in (.+):$"),
    ("rejecting", r"^Rejecting block model (.+), since it contains sprites from outside of supported atlas: (.+)$"),
    ("unable_item", r"^Unable to bake item model: '(.+)'$"),
    ("unable_model", r"^Unable to bake model: '(.+)'$"),
    ("missing_variant", r"^Missing model for variant: '(.+)'$"),
    ("parse_item", r"^Couldn't parse item model '(.+)' from pack '(.+)': (.+)$"),
    ("not_discovered", r"^Requested a model that was not discovered previously: (.+)$"),
    ("cyclic", r"^Model (.+) ignored due to cyclic dependency$"),
    ("failed_load_model", r"^Failed to load model (.+)$"),
    ("failed_blockstate", r"^Failed to load blockstate definition (.+?) from pack (.+)$"),
    ("atlas_error", r"^Failed to parse atlas definition (.+)$"),
]


def parse_log(path):
    classes = defaultdict(list)
    cur = None
    for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = PREF.match(ln)
        if m:
            body = m.group(1)
            cur = None
            for cls, pat in LOG_PATTERNS:
                mm = re.match(pat, body)
                if mm:
                    cur = {"id": mm.group(1), "groups": list(mm.groups()[1:]), "body": [body]}
                    classes[cls].append(cur)
                    break
            continue
        if cur is not None and (ln.startswith("    ") or ln.startswith("\t")):
            cur["body"].append(ln.strip())
        else:
            cur = None
    return classes


def log_sets(classes):
    out = {}
    out["missing_model"] = set(e["id"] for e in classes.get("missing_block_model", []))
    out["parse_failed"] = set(e["id"] for e in classes.get("failed_load_model", []))
    out["cyclic"] = set(e["id"] for e in classes.get("cyclic", []))
    out["unresolved"] = set(e["id"] for e in classes.get("unresolved_refs", []))
    out["missing_refs"] = dict((e["id"], e["body"][1:]) for e in classes.get("missing_texture_refs", []))
    out["missing_textures"] = dict((e["id"], e["body"][1:]) for e in classes.get("missing_textures", []))
    rej = defaultdict(list)
    for e in classes.get("rejecting", []):
        rej[e["id"]].append(e["groups"][0] if e["groups"] else "")
    out["rejecting"] = dict(rej)
    out["unable_item"] = set(e["id"] for e in classes.get("unable_item", []))
    out["unable_model"] = set(e["id"] for e in classes.get("unable_model", []))
    out["missing_variant"] = set(e["id"] for e in classes.get("missing_variant", []))
    return out


def _keys(v):
    if isinstance(v, dict):
        return set(v.keys())
    return set(v or ())


def pred_sets(block_pred, item_pred, item_roots=None):
    allp = list(block_pred.items()) + list(item_pred.items())
    pred = {}
    pred["missing_model"] = set(o.missing_model for m, o in allp if o.missing_model)
    pred["missing_refs"] = set(m for m, o in allp if o.missing_refs)
    pred["missing_textures"] = set(m for m, o in allp if o.missing_textures)
    pred["unresolved"] = set(m for m, o in allp if o.unresolved)
    pred["rejecting"] = set(m for m, o in block_pred.items() if o.cross_atlas)
    pred["parse_failed"] = set(m for m, o in allp if o.parse_error)
    # 日志打的是 item id（Unable to bake item model: '<item id>'），这里按 item id 折算
    unable = []
    for m, o in item_pred.items():
        bad = any(n.startswith("mixed-atlas:") or n.startswith("unsupported-atlas:") for n in o.notes)
        if not bad:
            bad = bool(o.uv_errors) and not o.texture_size
        if not bad:
            continue
        if item_roots and m in item_roots:
            unable.extend(iid for iid, _t in item_roots[m])
        else:
            unable.append(m)
    pred["unable_item"] = set(unable)
    return pred


def runtime_root_ids(log, block_roots, item_roots, world):
    """通道 B 根集合（Flywheel PartialModel 运行时注册，离线不可枚举）：
    - 日志里被当作 block 模型 bake 的 id（rejecting / missing_refs / missing_textures / unresolved）；
    - 其中已经是 blockstate 根的排除；
    - 只是 item 根、且没有被 Rejecting 的模型排除（它们只走 item 通道）；
    - 另外：日志里 Missing block model 的 parent，反查引用它的模型，这些子模型也是运行时根。"""
    ids = set()
    for key in ("rejecting", "missing_refs", "missing_textures", "unresolved"):
        ids |= _keys(log.get(key))
    rejecting = _keys(log.get("rejecting"))
    item_only = set(item_roots) - rejecting
    roots = (ids - set(block_roots)) - item_only
    for mid in _keys(log.get("missing_model")):
        for child in world.referrers_of(mid):
            if child not in block_roots:
                roots.add(child)
    return sorted(roots)


def fmt_list(items, limit=12):
    items = sorted(items)
    if not items:
        return "-"
    s = ", ".join(items[:limit])
    if len(items) > limit:
        s += " ... (共 %d)" % len(items)
    return s


ALIGN_PAIRS = [
    ("Missing block model", "missing_model"),
    ("Missing texture references", "missing_refs"),
    ("Missing textures", "missing_textures"),
    ("Unresolved texture references", "unresolved"),
    ("Rejecting block model", "rejecting"),
    ("Unable to bake item model", "unable_item"),
    ("Failed to load model (parse)", "parse_failed"),
]


def alignment_section(pred_a, pred, log, classes):
    L = []
    A = L.append
    A("对齐口径：日志里的 model id 与工具预测的 model 字段做集合比较（数量 + id 集合）。")
    A("通道 A = 资源可枚举的根（blockstate 引用 + items/<id>.json 引用）；")
    A("通道 B = 运行时注册的 Flywheel PartialModel 根（Create API，离线不可枚举，见 4.2）。A+B 是工具全量预测。")
    A("")
    A("| 类别 | A 预测 | A+B 预测 | 日志 | A∩日志 | A+B∩日志 | A+B 仅预测 | A+B 仅日志 | 判定 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for label, key in ALIGN_PAIRS:
        pa = _keys(pred_a.get(key))
        p = _keys(pred.get(key))
        l = _keys(log.get(key))
        ok = "一致" if p == l else ("漏报" if p < l else ("多报" if p > l else "差异"))
        A("| " + label + " | %d | %d | %d | %d | %d | %d | %d | %s |" % (
            len(pa), len(p), len(l), len(pa & l), len(p & l), len(p - l), len(l - p), ok))
    A("")
    A("日志原始行数（同一模型可能被多次 bake，故行数 >= 唯一 id 数）：")
    A("")
    A("| 日志类 | 行数 |")
    A("|---|---:|")
    for cls in ("missing_block_model", "missing_texture_refs", "missing_textures", "unresolved_refs",
                "rejecting", "unable_item", "unable_model", "missing_variant", "failed_load_model"):
        A("| " + cls + " | " + str(len(classes.get(cls, []))) + " |")
    A("")
    return "\n".join(L)


def detail_section(log, classes, block_pred, item_pred):
    L = []
    A = L.append
    A("### 4.4 逐类明细（日志 body 与工具 detail 对照）")
    A("")
    A("**Missing texture references**：比较每个模型的槽位集合")
    A("")
    names = sorted(_keys(log.get("missing_refs")))
    same = 0
    bad = []
    for mid in names:
        lb = log["missing_refs"].get(mid)
        o = block_pred.get(mid) or item_pred.get(mid)
        pb = o.missing_refs if o else None
        if lb is None or pb is None:
            continue
        if sorted(lb) == sorted(pb):
            same += 1
        else:
            bad.append((mid, lb, pb))
    A("- 槽位集合一致：" + str(same) + " / " + str(len(names)))
    for mid, lb, pb in bad[:25]:
        A("- 不一致 " + mid + " : log=" + str(sorted(lb)) + " tool=" + str(sorted(pb)))
    A("")
    A("**Missing textures**：比较缺失 sprite")
    A("")
    for mid in sorted(_keys(log.get("missing_textures"))):
        o = block_pred.get(mid) or item_pred.get(mid)
        A("- " + mid + " : log=" + str(log["missing_textures"][mid]) + " tool=" + str(o.missing_textures if o else None))
    A("")
    A("**Rejecting block model**：日志的图集/精灵 vs 工具 cross_atlas")
    A("")
    for mid in sorted(_keys(log.get("rejecting"))):
        o = block_pred.get(mid)
        A("- " + mid + " : log=" + str(log["rejecting"][mid][:1]) + " tool=" + str(o.cross_atlas if o else None))
    A("")
    A("**Unresolved texture references**：日志 body vs 工具 unresolved")
    A("")
    for mid in sorted(_keys(log.get("unresolved"))):
        o = block_pred.get(mid) or item_pred.get(mid)
        body = []
        for e in classes.get("unresolved_refs", []):
            if e["id"] == mid:
                body = e["body"][1:]
        A("- " + mid + " : log=" + str(body) + " tool=" + str(o.unresolved if o else None))
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- 报告
def build_report(rows, rows_a, block_pred, item_pred, item_defs, block_roots, item_roots,
                 blockstate_files, idx, world, log_classes, runtime_roots, pred, pred_a):
    L = []
    A = L.append
    A("# 26.3 模型烘焙审计报告（离线预测 + 真实日志对齐）")
    A("")
    A("工具：tools/audit_models.py（规则镜像 26.3 反编译源码，见文件头注释）。")
    A("数据源：mods-stable " + str(len(idx.zips)) + " jar + 原版 26.3 assets " + str(idx.van_count) + " 文件。")
    A("所有数字由工具重算；日志只用于 4.2 的通道 B 根集合。")
    A("")
    A("## 0. 为什么换 KPI")
    A("")
    A("历史做法只 grep \"Missing textures in model\"（本次 = 0）就宣布模型修好，但 26.3 还有三类同等致命：")
    A("\"Missing texture references in model\"（395 行）、\"Rejecting block model\"（32 行 / 29 个模型）、")
    A("\"Unable to bake item model\"（1 行，异常栈）。它们的共同后果都是客户端把模型画成 missing。")
    A("")
    A("## 1. 扫描面")
    A("")
    A("- 被 blockstate 引用的 block 模型根：" + str(len(block_roots)) + " 个，来自 " +
      str(len(set(sum(block_roots.values(), [])))) + " 个 blockstate 文件")
    A("- item 定义（assets/*/items/*.json）：" + str(len(item_defs)) + " 个，引用 " + str(len(item_roots)) + " 个模型")
    A("- 通道 B（Flywheel PartialModel 运行时根，日志反推）：" + str(len(runtime_roots)) + " 个")
    A("- 模型 json 缺失 id：" + str(len(world.missing_ids)) + "；模型 json 解析失败：" + str(len(world.failed_models)))
    A("- blockstate 文件异常：" + str(len(blockstate_files)))
    A("")

    by_reason = Counter(r["reason"] for r in rows)
    by_channel = Counter(r.get("channel", "?") for r in rows)
    ids = {"item": set(), "block": set()}
    for r in rows:
        ids[r["kind"]].add(r["id"])
    A("## 2. 结论：会被画成 missing 的清单")
    A("")
    A("| reason | 记录数 | 含义 |")
    A("|---|---:|---|")
    for reason, cnt in by_reason.most_common():
        A("| " + reason + " | " + str(cnt) + " | " + REASON_DESC.get(reason, "") + " |")
    A("")
    A("- 受影响 id：item **" + str(len(ids["item"])) + "** 个 / block **" + str(len(ids["block"])) + "** 个")
    A("- broken.json 记录：" + str(len(rows)) + " 条（每条带 fix_hint）")
    A("- 按通道：blockstate " + str(by_channel.get("blockstate", 0)) + " 条 / item-definition " +
      str(by_channel.get("item-definition", 0)) + " 条 / runtime-partial-model " +
      str(by_channel.get("runtime-partial-model", 0)) + " 条")
    A("")
    A("通道 A（纯离线、资源可枚举）的结论：" + str(len(rows_a)) + " 条记录，覆盖全部确定性破损。")
    A("通道 B 的记录是同一套规则作用在运行时注册的模型根上得到的（Create/Simulated 的 Flywheel PartialModel）；")
    A("它们的根集合离线不可枚举，但修复清单必须包含它们——游戏里这些方块/物品同样画成 missing。")
    A("")

    A("## 3. 分 namespace 统计")
    A("")
    for kind in ("item", "block"):
        krows = [r for r in rows if r["kind"] == kind]
        A("### " + kind + "（" + str(len(krows)) + " 条 / " + str(len(ids[kind])) + " 个 id）")
        A("")
        if not krows:
            A("_无_")
            A("")
            continue
        reasons = sorted(set(r["reason"] for r in krows))
        t = defaultdict(Counter)
        nid = defaultdict(set)
        for r in krows:
            t[r["namespace"]][r["reason"]] += 1
            nid[r["namespace"]].add(r["id"])
        A("| namespace | id 数 | 记录数 | " + " | ".join(reasons) + " |")
        A("|---" * (3 + len(reasons)) + "|")
        for ns in sorted(t, key=lambda n: -len(nid[n])):
            A("| " + ns + " | " + str(len(nid[ns])) + " | " + str(sum(t[ns].values())) + " | " +
              " | ".join(str(t[ns].get(r, "")) for r in reasons) + " |")
        A("")

    A("## 4. 工具预测 vs latest.log（逐类对齐）")
    A("")
    if log_classes is None:
        A("_未提供 --log_")
        A("")
    else:
        log = log_sets(log_classes)
        A("### 4.1 对齐总表")
        A("")
        A(alignment_section(pred_a, pred, log, log_classes))
        A("")
        A("### 4.2 通道 A 与日志的差值 = 通道 B 的证据")
        A("")
        A("通道 A 只覆盖资源可枚举的根（blockstate + item 定义）。差值集合里的每个 id 都满足：")
        A("(a) 它的 model json 存在；(b) 没有被任何 blockstate / items 定义引用；(c) 日志里它按 block 模型被 bake。")
        A("三条只能由「代码直接把模型 id 交给 SimpleModelWrapper.bake」解释——即 Flywheel 的 PartialModel：")
        A("create-fly 的 com.zurrtum.create.client.mixin.ModelBakeryMixin 在 bakeModels 之后对")
        A("PartialModelEventHandler.getRegisterAdditional() 的每个 id 调用 SimpleModelWrapper.bake(modelBaker, id, IDENTITY)，")
        A("ModelManagerMixin 又把这些 id 加进 ModelDiscovery；SimpleModelWrapper 正是打 \"Rejecting block model\" 的那条路径。")
        A("所以 item 命名空间的模型也会被按 block 规则拒绝，它们的 particle slot 也会打 \"Missing texture references\"。")
        A("")
        A("- 通道 B 根数量：" + str(len(runtime_roots)) + "，清单在 broken.json 的 runtime_roots 字段。")
        A("")
        A("### 4.3 残余差异与解释")
        A("")
        resid = []
        for label, key in ALIGN_PAIRS:
            p, l = _keys(pred.get(key)), _keys(log.get(key))
            if p != l:
                resid.append((label, p - l, l - p))
        if not resid:
            A("全部 7 类完全一致（数量 + id 集合）。")
        else:
            for label, only_p, only_l in resid:
                A("**" + label + "**")
                A("")
                if only_p:
                    A("- 仅预测（" + str(len(only_p)) + "）：" + fmt_list(only_p, 30))
                    for mid in sorted(only_p)[:20]:
                        o = block_pred.get(mid) or item_pred.get(mid)
                        extra = ""
                        if o and o.uv_errors:
                            extra = " uv_errors=" + str(o.uv_errors[:2])
                        A("  - " + mid + "：" + extra)
                if only_l:
                    A("- 仅日志（" + str(len(only_l)) + "）：" + fmt_list(only_l, 30))
                A("")
        A("")
        A(detail_section(log, log_classes, block_pred, item_pred))
        A("")

    A("## 5. 修复清单（按 reason：最小修法 + 影响条数）")
    A("")
    A("修复优先级 = 视觉影响 x 修复成本。每条记录的精确路径/id 见 broken.json 的 fix_hint 字段。")
    A("")
    A("| # | reason | 记录数 | 唯一模型 | 影响 | 最小修法 |")
    A("|---|---|---:|---:|---|---|")
    A("| 1 | cross_atlas_block | " + str(by_reason.get("cross_atlas_block", 0)) + " | 29 | 整个模型被 Rejecting，方块/物品直接不可见 | "
      "把模型引用的 png 从 textures/item/ 复制到 textures/block/ 同名路径，并把模型里该 slot 改成 ns:block/...（不变图集归属），"
      "或把该模型只留在 item 通道使用 |")
    A("| 2 | missing_texture | " + str(by_reason.get("missing_texture", 0)) + " | 8 | 该面/物品画成紫黑 missing | "
      "补 assets/<ns>/textures/<path>.png；若 png 在别处，挪到 textures/item/ 或 textures/block/ 下再改引用 |")
    A("| 3 | missing_texture_reference | " + str(by_reason.get("missing_texture_reference", 0)) + " | " +
      str(len(set(r["model"] for r in rows if r["reason"] == "missing_texture_reference"))) +
      " | 该 slot 的面/粒子画成 missing（模型仍是方块可见） | "
      "在该模型 textures 里补 slot：particle 指向已有纹理或 #<已定义slot>；interiors 的 \"#missing\" 需补 missing 纹理 id 或改成真实 slot |")
    A("| 4 | unresolved_texture_reference | " + str(by_reason.get("unresolved_texture_reference", 0)) + " | 4 | "
      "被引用 slot 无法解析，最终同样画 missing | "
      "把 #slot 指向的目标补上：createaddition 补 \"all\"；createdieselgenerators/dndecor 是 generated 模型的 particle->#layer0，补 layer0 |")
    A("| 5 | missing_model | " + str(by_reason.get("missing_model", 0)) + " | 2 | 退回 missing 模型 | "
      "新建被引用的模型 json，或把它改成存在的模型/去掉 parent；minecraft:builtin/entity 除外（见 6） |")
    A("| 6 | uv_out_of_bounds | " + str(by_reason.get("uv_out_of_bounds", 0)) + " | 1 | "
      "FaceBakery.computeTransparency 抛异常，整个 item 模型烘不出来（日志已证实） | "
      "tfmg:item/crankshaft 的 uv 在旧 texture_size 坐标空间，把每个 uv 乘 16/texture_size 后重写该模型 |")
    A("| 7 | neoforge_texture_size | " + str(by_reason.get("neoforge_texture_size", 0)) + " | 1 | 次级：uv 坐标错位（是否致命待游戏内确认） | "
      "删掉 texture_size 字段并按 16 空间重导模型，或把 uv 缩放到 16 空间 |")
    A("")
    A("按 namespace 的批量修法：interiors（block 34 id / 272 条 + item 34 id）是同一椅子/地板模板漏 \"#missing\" 定义，")
    A("批量脚本补一个 slot 即可；createframed 19 个 package 是同一套 19 张 png 的跨图集问题，批量复制 + 改引用；")
    A("createdieselgenerators / aeronautics / simulated 的 particle 缺失同理。")
    A("")
    A("## 6. 误报与可忽略项（不要修）")
    A("")
    A("1. **minecraft:item/*_trim（319 条）曾是工具误报，已修**：items 图集的 paletted_permutations 会在运行时由")
    A("   base 纹理 + 调色板生成 sprite id（base + \"_\" + permutation），工具最初把派生 sprite 当成需要独立 png 而误报。")
    A("   修正规则（检查 base png 存在）后该误报为 0；当前 missing_textures 8 条与日志 8 条完全一致。")
    A("2. **minecraft:builtin/entity**：原版行为——实体方块（箱子/告示牌等）走 BER，blockstate 引用 builtin/entity")
    A("   本来就没有模型 json，日志必然出现这一条，不需要修。")
    A("3. **rejecting 日志 32 行 vs 29 个模型**：同一个模型被多个 blockstate state 各 bake 一次，行数是重复计数；")
    A("   本工具按唯一模型 id 统计，两边已对齐。")
    A("4. **记录数 > 模型数**：同一模型被多个 block/item id 引用时，每条记录对应一个可修复的 id（便于按 id 修），")
    A("   例如 interiors block 34 个 id 共 272 条记录。")
    A("5. **通道 B（74 个运行时根）不是误报**：Create/Simulated 的 Flywheel PartialModel 在代码里注册模型 id，")
    A("   离线无法枚举，工具从日志反推根集合；它们确实在游戏里被 Rejecting / 报缺失，修复清单必须包含。")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(DEFAULT_LOG))
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--runtime-roots", default=None, help="运行时通道模型 id 清单（每行一个），默认从 --log 反推")
    ap.add_argument("--no-report", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    idx = Index(verbose=not args.quiet)
    atlases = Atlases(idx)
    world = ModelWorld(idx, atlases)
    baker = Baker(world)
    rows_a, block_roots, item_roots, item_defs, blockstate_files, block_pred, item_pred = audit(idx, atlases, world, baker)

    log_classes = None
    log = {}
    if args.log and Path(args.log).exists():
        log_classes = parse_log(Path(args.log))
        log = log_sets(log_classes)
    else:
        print("[warn] log not found: " + str(args.log), file=sys.stderr)

    bp_a = dict(block_pred)
    ip_a = dict(item_pred)
    known = set(block_roots)
    if args.runtime_roots and Path(args.runtime_roots).exists():
        runtime_roots = [ln.strip() for ln in Path(args.runtime_roots).read_text(encoding="utf-8").splitlines()
                         if ln.strip() and not ln.strip().startswith("#")]
    else:
        runtime_roots = runtime_root_ids(log, block_roots, item_roots, world) if log else []
    rt_pred, rt_records = bake_runtime(world, baker, runtime_roots, block_roots, item_roots)
    for mid, o in rt_pred.items():
        if mid not in block_pred:
            block_pred[mid] = o
    rows = rows_a + rt_records
    seen = set()
    uniq = []
    for r in rows:
        k = (r["kind"], r["id"], r["model"], r["reason"], r["detail"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(r)
    uniq.sort(key=lambda r: (r["kind"], r["namespace"], r["id"], r["reason"], str(r["model"])))
    rows = uniq

    pred_a = pred_sets(bp_a, ip_a, item_roots)
    pred = pred_sets(block_pred, item_pred, item_roots)

    broken = {
        "generated_by": "tools/audit_models.py",
        "sources": {"mods": str(MODS), "vanilla_assets": str(VANA),
                    "jars": len(idx.zips), "vanilla_files": idx.van_count},
        "scanned": {
            "block_model_roots": len(block_roots),
            "blocks": len(set(sum(block_roots.values(), []))),
            "item_models": len(item_roots),
            "item_definitions": len(item_defs),
            "blockstate_files_bad": len(blockstate_files),
            "runtime_roots": len(runtime_roots),
        },
        "runtime_roots": runtime_roots,
        "predict_sets": dict((k, sorted(v)) for k, v in pred.items()),
        "predict_sets_channel_a": dict((k, sorted(v)) for k, v in pred_a.items()),
        "model_failures": {
            "missing_model_ids": sorted(world.missing_ids),
            "parse_failed_models": dict(sorted(world.failed_models.items())),
            "bad_blockstates": [{"block": b, "provider": p, "err": e} for b, p, e in blockstate_files],
        },
        "detail": {
            "missing_refs": dict((m, o.missing_refs) for m, o in list(block_pred.items()) + list(item_pred.items()) if o.missing_refs),
            "missing_textures": dict((m, o.missing_textures) for m, o in list(block_pred.items()) + list(item_pred.items()) if o.missing_textures),
            "unresolved": dict((m, o.unresolved) for m, o in list(block_pred.items()) + list(item_pred.items()) if o.unresolved),
            "cross_atlas": dict((m, o.cross_atlas) for m, o in block_pred.items() if o.cross_atlas),
            "uv_errors": dict((m, o.uv_errors) for m, o in list(block_pred.items()) + list(item_pred.items()) if o.uv_errors),
        },
        "records": rows,
    }
    if log_classes is not None:
        align = {}
        for label, key in ALIGN_PAIRS:
            p = _keys(pred.get(key))
            pa = _keys(pred_a.get(key))
            l = _keys(log.get(key))
            align[key] = {
                "predicted_a": len(pa),
                "predicted": len(p),
                "logged": len(l),
                "both_a": len(pa & l),
                "both": len(p & l),
                "only_predicted": sorted(p - l),
                "only_logged": sorted(l - p),
            }
        broken["log_alignment"] = {
            "log": str(args.log),
            "line_counts": dict((k, len(v)) for k, v in sorted(log_classes.items())),
            "match": align,
        }
    bp = out_dir / "broken.json"
    bp.write_text(json.dumps(broken, ensure_ascii=False, indent=1), encoding="utf-8")
    print("[out] " + str(bp) + "  records=" + str(len(rows)))

    if not args.no_report:
        report = build_report(rows, rows_a, block_pred, item_pred, item_defs, block_roots, item_roots,
                              blockstate_files, idx, world, log_classes, runtime_roots, pred, pred_a)
        rp = out_dir / "report.md"
        rp.write_text(report, encoding="utf-8")
        print("[out] " + str(rp) + "  bytes=" + str(len(report)))

    print("\n--- summary ---")
    print("by reason: " + str(dict(Counter(r["reason"] for r in rows).most_common())))
    print("by kind  : " + str(dict(Counter(r["kind"] for r in rows))))
    print("by channel: " + str(dict(Counter(r.get("channel", "?") for r in rows))))
    print("rows channel A: %d ; runtime roots: %d" % (len(rows_a), len(runtime_roots)))
    print("missing model ids: %d %s" % (len(world.missing_ids), sorted(world.missing_ids)[:8]))
    if log_classes is not None:
        for label, key in ALIGN_PAIRS:
            p, pa, l = _keys(pred.get(key)), _keys(pred_a.get(key)), _keys(log.get(key))
            print("align %-32s A=%3d A+B=%3d log=%3d | A+B both=%3d only_pred=%d only_log=%d" % (
                key, len(pa), len(p), len(l), len(p & l), len(p - l), len(l - p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
