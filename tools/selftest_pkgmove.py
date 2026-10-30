# -*- coding: utf-8 -*-
"""一次性自测：patch_create_pkgmove 的替换正则是否只对「完整类型名」生效。"""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("pm", "tools/patch_create_pkgmove.py")
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)

RP = "com/mojang/blaze3d/pipeline/RenderPipeline"
RPB = "com/mojang/blaze3d/pipeline/RenderPipeline$Builder"
RPS = "com/mojang/blaze3d/pipeline/RenderPipeline$Snippet"
mp = {
    RP: "com/mojang/renderpearl/api/pipeline/RenderPipeline",
    RPB: "com/mojang/renderpearl/api/pipeline/RenderPipeline$Builder",
    RPS: "com/mojang/renderpearl/api/pipeline/RenderPipeline$Snippet",
}
pat, _ = pm.make_replacer(mp)

tests = [
    RP,
    "L" + RP + ";",
    "L" + RPB + ";",
    "([L" + RP + ";L" + RPB + ";)V",
    "Lcom/mojang/blaze3d/vertex/PoseStack;",          # 必须原样不动
    RPB,
    "Ljava/util/List<L" + RP + ";>;",
    "L" + RPS + ";",
    "com/mojang/blaze3d/pipeline/RenderPipelineX",    # 前缀但不是同一个类
    "Lcom/mojang/blaze3d/pipeline/RenderPipeline$Inner;",
]

ok = True
for t in tests:
    got = pat.sub(lambda m: mp[m.group(1)], t)
    print("%-70s -> %s" % (t, got))

print()
print("PoseStack 未变:", pat.sub(lambda m: mp[m.group(1)], "Lcom/mojang/blaze3d/vertex/PoseStack;")
      == "Lcom/mojang/blaze3d/vertex/PoseStack;")
print("RenderPipelineX 未变:", pat.sub(lambda m: mp[m.group(1)], "com/mojang/blaze3d/pipeline/RenderPipelineX")
      == "com/mojang/blaze3d/pipeline/RenderPipelineX")
print("$Inner 未变:", pat.sub(lambda m: mp[m.group(1)], "Lcom/mojang/blaze3d/pipeline/RenderPipeline$Inner;")
      == "Lcom/mojang/blaze3d/pipeline/RenderPipeline$Inner;")
print("嵌套类先匹配长名:", pat.sub(lambda m: mp[m.group(1)], "L" + RPB + ";")
      == "Lcom/mojang/renderpearl/api/pipeline/RenderPipeline$Builder;")
