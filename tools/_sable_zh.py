#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 Sable 的 128 条 UI/命令文本译成简体中文，写回 jar 的 assets/sable/lang/zh_cn.json。"""
import json
import os
import shutil
import sys
import zipfile

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ZH = {
"menu.savingSubLevels": "正在保存子维度",
"commands.sable.helper.missing_sub_level_container": "找不到此维度的子维度容器！",
"commands.sable.helper.missing_physics_system": "找不到此维度的子维度物理系统！",
"commands.sable.sub_level": "子维度",
"commands.sable.sub_levels": "%s 个子维度",
"commands.sable.physics.global": "全局",
"commands.sable.physics.local": "局部",
"commands.sable.spawn.success": "已生成 %s",
"commands.sable.spawn.clone.success": "已克隆子维度",
"commands.sable.physics.impulse.angular.success": "已对 %s 的 %s 施加 %s 角冲量",
"commands.sable.physics.impulse.linear.success": "已对 %s 的 %s 施加 %s 线冲量",
"commands.sable.physics.rotation.add.success": "已对 %s 的 %s 增加 %s 旋转",
"commands.sable.physics.rotation.set.success": "已将 %s 的旋转设为 %s",
"commands.sable.physics.translation.add.success": "已对 %s 的 %s 增加 %s 位移",
"commands.sable.physics.translation.set.success": "已将 %s 的位移设为 %s",
"commands.sable.joint.missing_sublevel_target": "找不到连接所需的子维度",
"commands.sable.joint.success": "成功创建连接",
"commands.sable.sub_level.set_name.success_singular": "已将子维度命名为 %s",
"commands.sable.sub_level.set_name.success_multiple": "已将 %s 个子维度命名为 %s",
"commands.sable.sub_level.get_name.success": "子维度名称为 %s",
"commands.sable.sub_level.get_name.failure_unnamed": "子维度没有名称",
"commands.sable.sub_level.clear_name.success_singular": "已清除子维度名称",
"commands.sable.sub_level.clear_name.success_multiple": "已清除 %s 个子维度的名称",
"commands.sable.sub_level.teleport_with_orientation.success": "已将 %s 传送到 %.2f, %.2f, %.2f，朝向 %.2f, %.2f",
"commands.sable.sub_level.teleport.success": "已将 %s 传送到 %.2f, %.2f, %.2f",
"commands.sable.sub_level.remove.success": "已移除 %s",
"commands.sable.sub_level.assemble.no_blocks": "无法组装子维度：没有找到有效的方块",
"commands.sable.sub_level.assemble.connected.too_many_blocks": "无法组装子维度：方块太多（上限 %s）",
"commands.sable.sub_level.shatter.no_blocks": "无法打碎成子维度：没有找到有效的方块",
"commands.sable.sub_level.shatter.connected.too_many_blocks": "无法打碎成子维度：方块太多（上限 %s）",
"commands.sable.sub_level.shatter.region.success": "已将含 %s 个方块的区域打碎为新的子维度",
"commands.sable.sub_level.shatter.connected.success": "已将 %s 个相连方块打碎为新的子维度",
"commands.sable.sub_level.shatter.range.success": "已将含 %s 个方块的范围打碎为新的子维度",
"commands.sable.sub_level.shatter.radius.success": "已将含 %s 个方块的半径打碎为新的子维度",
"commands.sable.sub_level.shatter.sub_level.success": "已将 %s 打碎为 %s 个新子维度",
"commands.sable.sub_level.shatter.sub_level.only_single_blocks": "无法打碎单方块子维度",
"commands.sable.sub_level.assemble.region.success": "已将 %s 个方块的区域组装为新的子维度",
"commands.sable.sub_level.assemble.connected.success": "已将 %s 个相连方块组装为新的子维度",
"commands.sable.sub_level.assemble.radius.success": "已将含 %s 个方块的半径组装为新的子维度",
"commands.sable.sub_level.assemble.range.success": "已将含 %s 个方块的范围组装为新的子维度",
"commands.sable.physics.paused.success": "已将物理暂停设为 %s",
"commands.sable.physics.paused_toggled.success": "已切换物理暂停为 %s",
"commands.sable.place_schematic.failure": "找不到蓝图！",
"commands.sable.place_schematic.success": "已放置蓝图！",
"commands.sable.fail.not_inside_sub_level": "位置在子维度绘图区之外",
"commands.sable.fail.no_sub_levels": "没有找到子维度",
"commands.sable.fail.unmodified": "没有子维度被修改",
"commands.sable.fail.no_axis_for_rotation": "没有可用于旋转的轴",
"commands.sable.info.count": "找到 %s 个子维度：",
"commands.sable.info.name": "%s：",
"commands.sable.info.name.tooltip": "序列化指针：%s",
"commands.sable.info.position": "    位置：%.2f %.2f %.2f",
"commands.sable.info.orientation": "    朝向：%.2f %.2f %.2f %.2f",
"commands.sable.info.linear_velocity": "    线速度：%.2f %.2f %.2f",
"commands.sable.info.angular_velocity": "    角速度：%.2f %.2f %.2f",
"commands.sable.info.mass": "    质量：%.2f",
"commands.sable.info.world_bounds": "    世界边界：%.2f x %.2f x %.2f",
"commands.data.sub_level.get": "%s 在子维度 %s 上，经缩放因子 %s 之后为 %s",
"commands.data.sub_level.modified": "已修改 %s 的子维度辅助数据",
"commands.sable.forceload.add.count": "已为 %s 个子维度添加强制加载票据",
"commands.sable.forceload.remove.count": "已移除 %s 个子维度的强制加载票据",
"commands.sable.forceload.query.none": "在 %s 中没有找到强制加载票据",
"commands.sable.forceload.query.count": "在 %s 中为 %s 个子维度找到 %s 个强制加载票据：",
"commands.sable.forceload.sub_level_name": "%s：",
"commands.sable.forceload.ticket": "    %s",
"argument.sable.body.selector.all": "所有子维度",
"argument.sable.body.selector.nearest": "最近的子维度",
"argument.sable.body.selector.random": "随机子维度",
"argument.sable.body.selector.viewed": "正在查看的子维度",
"argument.sable.body.selector.latest": "最新的子维度",
"argument.sable.body.selector.tracking": "正在跟踪的子维度",
"argument.sable.body.selector.inside": "内部的子维度",
"argument.sable.body.static_world": "静态世界",
"argument.sable.sub_level.modifier.distance": "到子维度的距离",
"argument.sable.sub_level.modifier.x": "x 坐标",
"argument.sable.sub_level.modifier.y": "y 坐标",
"argument.sable.sub_level.modifier.z": "z 坐标",
"argument.sable.sub_level.modifier.dx": "x 到 x+dx 之间的子维度",
"argument.sable.sub_level.modifier.dy": "y 到 y+dy 之间的子维度",
"argument.sable.sub_level.modifier.dz": "z 到 z+dz 之间的子维度",
"argument.sable.sub_level.modifier.vx": "x 速度",
"argument.sable.sub_level.modifier.vy": "y 速度",
"argument.sable.sub_level.modifier.vz": "z 速度",
"argument.sable.sub_level.modifier.speed": "子维度速度",
"argument.sable.sub_level.modifier.mass": "子维度重量",
"argument.sable.sub_level.modifier.volume": "子维度包围盒体积",
"argument.sable.sub_level.modifier.width": "子维度包围盒的 X 轴尺寸",
"argument.sable.sub_level.modifier.height": "子维度包围盒的 Y 轴尺寸",
"argument.sable.sub_level.modifier.length": "子维度包围盒的 Z 轴尺寸",
"argument.sable.sub_level.modifier.limit": "返回的子维度数量上限",
"argument.sable.sub_level.modifier.name": "子维度名称",
"argument.sable.sub_level.modifier.sort": "按距离排序子维度",
"argument.sable.unexpected_end_of_input": "输入意外结束",
"argument.sable.single_sub_level_required": "只允许一个子维度，但所提供的选择器允许多个",
"argument.sable.invalid_selector": "无效的子维度选择器",
"argument.sable.invalid_uuid": "无效的 UUID",
"argument.sable.cannot_find_sub_level": "找不到子维度",
"argument.sable.sub_level.expected_end_of_modifier": "预期修饰符结束",
"argument.sable.sub_level.expected_positive_integer": "预期一个正整数",
"argument.sable.sub_level.expected_positive_decimal": "预期一个正小数",
"argument.sable.sub_level.expected_positive_range": "预期一个正数范围",
"argument.sable.sub_level.expected_sorting": "预期排序类型为 nearest 或 furthest",
"inspector.sable.sub_level_container.title": "子维度容器",
"attribute.name.player.sub_level_punch_strength": "推击强度",
"attribute.name.player.sub_level_punch_cooldown": "推击冷却",
"options.sable_menu": "子维度设置...",
"options.physics_steps": "物理步数",
"options.physics_steps_template": "每秒 %s 步",
"options.physics_steps.tooltip": "物理模拟每秒执行的步数。数值越高精度越高，但性能开销显著增加。",
"sub_level.toast.checkLog": "详情请查看日志",
"sub_level.toast.loadFailure": "加载子维度失败：%s",
"sub_level.toast.saveFailure": "保存子维度失败：%s",
"sub_level.toast.physicsFailure": "子维度物理异常：%s",
"sub_level.toast.attemptingRecovery": "正在尝试恢复",
"camera_type.sub_level_view": "进入装置视角",
"camera_type.sub_level_view_unlocked": "进入解锁装置视角",
"force_group.sable.gravity": "重力",
"force_group.sable.drag": "阻力",
"force_group.sable.levitation": "悬浮",
"force_group.sable.balloon_lift": "气球升力",
"force_group.sable.propulsion": "推进力",
"force_group.sable.lift": "升力",
"force_group.sable.magnetic_force": "磁力",
"schematic.sable.mirror_not_supported": "无法镜像包含子维度的蓝图！",
"death.attack.fall.from_sublevel": "%1$s 从 %2$s 摔落",
"sable.create.mechanical_arm.points_removed_sublevel_and_range": "%1$s 个已选交互点因超出范围或未锚定被移除。",
"sable.create.remove.points_removed_sublevel": "%1$s 个已选交互点因未锚定被移除",
}

JAR = r"C:\Users\95959\OneDrive\Desktop\Work\skylands-262\work\run26\mods-full\sable-fabric-26.3.jar"
PATH = "assets/sable/lang/zh_cn.json"

z = zipfile.ZipFile(JAR)
names = z.namelist()
data = {n: z.read(n) for n in names}
z.close()

src = json.loads(data["assets/sable/lang/en_us.json"].decode("utf-8", "replace"))
missing = [k for k in src if k not in ZH]
extra = [k for k in ZH if k not in src]
print("en_us 条数:", len(src), " 译文条数:", len(ZH))
print("未翻译:", len(missing), missing[:5])
print("多余(会保留但不使用):", len(extra), extra[:5])

# 保留已有的 zh_cn（如果有），叠加我们的译文
cur = {}
if PATH in data:
    try:
        cur = json.loads(data[PATH].decode("utf-8", "replace"))
    except Exception:
        cur = {}
before = len(cur)
cur.update(ZH)
data[PATH] = (json.dumps(dict(sorted(cur.items())), indent=2, ensure_ascii=False) + "\n").encode("utf-8")

shutil.copy2(JAR, JAR + ".bak-zh-sable")
with zipfile.ZipFile(JAR, "w", zipfile.ZIP_DEFLATED) as w:
    for n, b in data.items():
        w.writestr(n, b)
print("写入 %s：%d -> %d 条" % (PATH, before, len(cur)))
print("jar 已更新:", os.path.getsize(JAR) // 1024, "KB")
