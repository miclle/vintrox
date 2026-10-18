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
    return {'status':'static concept check only / 未实测', 'body_mm':{'width':float(doc.Parameters.Width), 'height':float(doc.Parameters.Height), 'depth':float(doc.Parameters.Depth)}, 'physical_objects':len(objects), 'checked_hardware':len(components), 'intersections':clashes, 'rear_cable_lane_intersections':lane_hits, 'minimum_gap_to_rear_lane_mm':round(rear_lane_gap,3), 'hardware_envelopes':envelopes, 'errors':errors, 'excluded':'外观控件/格栅与壳体的设计接触；CD操作提示；壳体板件互接。后部线束区已检查硬件侵入，未验证真实线缆/安装/热/声学/电气/加工。'}
