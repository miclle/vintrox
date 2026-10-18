"""Static checks for native VINTROX layout documents, without GUI generation."""


def physical(doc):
    return [o for group in ('Enclosure','Hardware','Details') for o in doc.getObject(group).Group]


def validate(doc):
    objects = physical(doc)
    errors = []
    for o in objects:
        if o.Shape.isNull() or not o.Shape.isValid() or not o.Shape.Solids or o.Shape.Volume <= 0:
            errors.append('无效实体: '+o.Name)
        if o.State and any(s in ('Invalid','Error') for s in o.State):
            errors.append('重计算失败: '+o.Name)
    components = doc.Hardware.Group
    shell = doc.Enclosure.Group
    clashes = []
    for i, a in enumerate(components):
        for b in list(components)[i+1:] + list(shell):
            volume = a.Shape.common(b.Shape).Volume
            if volume > 0.01:
                clashes.append({'a':a.Name, 'b':b.Name, 'volume_mm3':round(volume,3)})
    if clashes:
        errors.append('硬件包络相交或穿壳')
    w, h, depth, wall = (float(getattr(doc.Parameters, k)) for k in ('Width','Height','Depth','Wall'))
    for o in components:
        b = o.Shape.BoundBox
        if b.XMin < wall-0.01 or b.XMax > w-wall+0.01 or b.YMin < wall-0.01 or b.YMax > depth-wall+0.01 or b.ZMin < wall-0.01 or b.ZMax > h-wall+0.01:
            errors.append('硬件超出内腔: '+o.Name)
    lane_hits = []
    for o in components:
        volume = o.Shape.common(doc.CableLane.Shape).Volume
        if volume > 0.01:
            lane_hits.append({'hardware':o.Name, 'volume_mm3':round(volume,3)})
    if lane_hits:
        errors.append('硬件占用后部线束预留区')
    rear_lane_gap = min(doc.CableLane.Shape.BoundBox.YMin-o.Shape.BoundBox.YMax for o in components)
    envelopes = {o.Name:{'xyz_mm':[round(v,3) for v in (o.Shape.BoundBox.XLength,o.Shape.BoundBox.YLength,o.Shape.BoundBox.ZLength)], 'origin_mm':[round(v,3) for v in (o.Shape.BoundBox.XMin,o.Shape.BoundBox.YMin,o.Shape.BoundBox.ZMin)]} for o in components}
    styling = {}
    if doc.getObject('BlackBezel') is not None:
        corridor = doc.DisplayClearance.Shape
        occlusions = []
        for obj in list(shell) + [doc.BlackBezel]:
            volume = corridor.common(obj.Shape).Volume
            if volume > 0.01:
                occlusions.append({'part':obj.Name, 'volume_mm3':round(volume,3)})
        if occlusions:
            errors.append('显示可视区前方被遮挡')
        slot_center = doc.SlotTool.Shape.BoundBox.Center
        drive_center = doc.OpticalDrive.Shape.BoundBox.Center
        slot_offset = [round(slot_center.x-drive_center.x,6),round(slot_center.y-drive_center.y,6)]
        slot_blocked = doc.SlotTool.Shape.common(doc.ShellRight.Shape).Volume
        if any(abs(v)>1e-6 for v in slot_offset) or slot_blocked>0.01:
            errors.append('顶部槽口偏离光驱中心线或被木壳遮挡')
        overall = {}
        for axis, label in [('X','width'),('Y','depth'),('Z','height')]:
            overall[label] = round(max(getattr(o.Shape.optimalBoundingBox(False,False),axis+'Max') for o in objects)-min(getattr(o.Shape.optimalBoundingBox(False,False),axis+'Min') for o in objects),3)
        styling = {'assumed_parameters_mm':{key:float(getattr(doc.Parameters,key)) for key in ('CornerR','EdgeR','BezelR','BezelInset','BezelGap','BaseH','BaseInsetX','BaseInsetY')}, 'overall_envelope_mm':overall, 'display_corridor_occlusions':occlusions, 'slot_center_offset_xy_mm':slot_offset, 'slot_blocked_volume_mm3':round(slot_blocked,6), 'note':'总包络包含底座和突出的旋钮/RCA；木壳尺寸为布局派生；屏幕本体及排线板含用户测量/推导，其余参数仍含假设。'}
    return {'status':'static concept check only / 未实测', 'body_mm':{'width':float(doc.Parameters.Width), 'height':float(doc.Parameters.Height), 'depth':float(doc.Parameters.Depth)}, 'physical_objects':len(objects), 'checked_hardware':len(components), 'intersections':clashes, 'rear_cable_lane_intersections':lane_hits, 'minimum_gap_to_rear_lane_mm':round(rear_lane_gap,3), 'hardware_envelopes':envelopes, 'styling_checks':styling, 'errors':errors, 'excluded':'外观控件/格栅与壳体的设计接触；CD操作提示；壳体板件互接。后部线束区已检查硬件侵入，未验证真实线缆/安装/热/声学/电气/加工。'}
