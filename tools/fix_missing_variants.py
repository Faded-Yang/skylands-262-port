import itertools, json, os, sys, zipfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Users/95959/OneDrive/Desktop/Work/skylands-262")
DOMAINS = {"facing": ["down", "up", "north", "south", "west", "east"], "axis": ["x", "y", "z"],
           "face": ["floor", "wall", "ceiling"], "waterlogged": ["false", "true"], "powered": ["false", "true"],
           "open": ["false", "true"], "lit": ["false", "true"], "inverted": ["false", "true"],
           "north": ["false", "true"], "south": ["false", "true"], "east": ["false", "true"],
           "west": ["false", "true"], "up": ["false", "true"], "down": ["false", "true"],
           "bottom": ["false", "true"], "top": ["false", "true"], "x": ["false", "true"], "z": ["false", "true"],
           "layers": [str(n) for n in range(1, 9)], "orientation": [str(n) for n in range(1, 9)],
           "type": ["bottom", "top", "double"], "half": ["bottom", "top"], "large": ["false", "true"],
           "rotation": [str(n) for n in range(0, 16)], "size": [str(n) for n in range(1, 4)],
           "large": ["false", "true"], "railing_left": ["false", "true"], "railing_right": ["false", "true"],
           "hinge": ["left", "right"], "half": ["lower", "upper"]}
def props_from(d):
    keys = {}
    for k in d.get("variants", {}) if isinstance(d.get("variants"), dict) else {}:
        for pair in k.split(","):
            if "=" in pair:
                a, b = pair.split("=", 1)
                a = a.strip()
                keys.setdefault(a, set()).add(b.strip())
    for part in d.get("multipart", []):
        w = part.get("when", {})
        for a, b in w.items():
            if a in ("OR", "AND") or not isinstance(b, str):
                continue
            keys.setdefault(a, set()).add(b)
    return keys
def covered_variants(d, combo):
    for k in d.get("variants", {}):
        parts = tuple(sorted(x.replace(" ", "") for x in k.split(",") if "=" in x))
        if parts == combo:
            return True
    return False
def covered_multipart(d, combo_map):
    for part in d.get("multipart", []):
        w = part.get("when", {})
        ok = True
        for a, b in w.items():
            if a in ("OR", "AND"):
                ok = False
                break
            if b in ("true", "false") and combo_map.get(a) != b:
                ok = False
                break
            elif b not in ("true", "false") and combo_map.get(a) != str(b):
                ok = False
                break
        if ok:
            return True
    return False
def default_model(d, ns, bid):
    for part in d.get("multipart", []):
        ap = part.get("apply", {})
        if isinstance(ap, dict) and "model" in ap:
            return ap["model"]
    for v in d.get("variants", {}).values() if isinstance(d.get("variants"), dict) else []:
        if isinstance(v, dict) and "model" in v:
            return v["model"]
    return None
def fix(res_dir, ns):
    res = Path(res_dir)
    filled = 0
    for p in sorted(res.glob(f"assets/{ns}/blockstates/*.json")):
        bid = p.name[:-5]
        d = json.loads(p.read_bytes())
        keys = props_from(d)
        # R520: domain source = block CLASS kind (not observed json values)
        def class_domains(bid, present):
            out = {}
            if bid.endswith("_stairs"):
                cand = {"facing": ["north", "east", "south", "west"], "half": ["bottom", "top"],
                        "waterlogged": ["false", "true"]}
                for k in cand:
                    if k in present:
                        out[k] = cand[k]
                if "shape" in present:
                    out["shape"] = sorted(present["shape"])
                return out
            if bid.endswith("_wall"):
                for k, v in (("up", ["false", "true"]), ("waterlogged", ["false", "true"]),
                             ("north", ["none", "low", "tall"]), ("south", ["none", "low", "tall"]),
                             ("east", ["none", "low", "tall"]), ("west", ["none", "low", "tall"])):
                    if k in present:
                        out[k] = v
                return out
            if bid.endswith("_bars") or bid.endswith("_window_pane"):
                for k in ("north", "south", "east", "west", "waterlogged"):
                    if k in present:
                        out[k] = ["false", "true"]
                return out
            if bid.endswith("_ladder"):
                if "facing" in present:
                    out["facing"] = ["north", "east", "south", "west"]
                if "waterlogged" in present:
                    out["waterlogged"] = ["false", "true"]
                return out
            # custom generated classes: OUR property objects decide the domain
            for k in present:
                if k == "facing":
                    out[k] = ["down", "up", "north", "south", "west", "east"]
                elif k == "axis":
                    out[k] = ["x", "y", "z"]
                elif k == "face":
                    out[k] = ["floor", "wall", "ceiling"]
                elif k == "hinge":
                    out[k] = ["left", "right"]
                elif k == "half":
                    out[k] = ["bottom", "top"] if bid.endswith("_trapdoor") else ["lower", "upper"]
                elif k in ("layers", "orientation"):
                    out[k] = [str(n) for n in range(1, 9)]
                elif k in DOMAINS:
                    out[k] = DOMAINS[k]
            return out
        domains = class_domains(bid, keys)
        props = list(domains)
        if not props:
            continue
        model = default_model(d, ns, bid)
        if model is None:
            continue
        total = 1
        for k in props:
            total *= len(domains[k])
        if total > 2000:
            continue
        if isinstance(d.get("variants"), dict):
            for vals in itertools.product(*[domains[k] for k in props]):
                combo = tuple(sorted(k + "=" + v for k, v in zip(props, vals)))
                if covered_variants(d, combo):
                    continue
                d["variants"][",".join(combo)] = {"model": model}
                filled += 1
            p.write_text(json.dumps(d, indent=2) + chr(10), encoding="utf-8")
        elif isinstance(d.get("multipart"), list):
            for vals in itertools.product(*[domains[k] for k in props]):
                cmap = dict(zip(props, vals))
                if covered_multipart(d, cmap):
                    continue
                when = {k: cmap[k] for k in props}
                d["multipart"].append({"when": when, "apply": {"model": model}})
                filled += 1
            p.write_text(json.dumps(d, indent=2) + chr(10), encoding="utf-8")
    print(f"FIX {ns}: filled {filled} variant/parts in {res}")
    return filled
if __name__ == "__main__":
    target = sys.argv[1]
    ns = sys.argv[2]
    fix(target, ns)
