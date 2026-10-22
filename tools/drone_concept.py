"""Build the screen-scaled Drone appearance study in the FreeCAD GUI.

All non-screen dimensions are appearance assumptions. Individually named BRep features
are editable solids, not released printing parts or a fitted hardware assembly.
Objects are ungrouped with Chinese display labels and stable script identifiers.
"""
from pathlib import Path
import hashlib
import json
import math
import re
import tempfile

import FreeCAD as App
import FreeCADGui as Gui
import Part
import Import


GOLD = (0.64, 0.44, 0.105)
EDGE = (0.82, 0.64, 0.24)
DARK = (0.045, 0.061, 0.067)
METAL = (0.24, 0.29, 0.30)
SILVER = (0.57, 0.62, 0.61)
RED = (0.64, 0.055, 0.035)
WHITE = (0.85, 0.83, 0.65)
CYAN = (0.05, 0.90, 0.94)
GREEN = (0.27, 0.67, 0.19)
OLIVE = (0.25, 0.28, 0.16)

CHINESE_LABELS = {
    'MainEnclosureShell': '主机连续外壳', 'SlopedUpperArmour': '顶部斜面外罩',
    'RoofSideClosure': '顶罩侧封板', 'RearUpperClosure': '后部上封板',
    'BottomChassis': '底盘', 'ClosedBellyPan': '底部封闭托壳',
    'RearServicePanel': '后部检修盖板', 'RearStructuralFrame': '后盖外框',
    'ProjectingBrow': '前伸屏幕罩', 'BrowUnderside': '屏幕罩内衬',
    'ScreenBezel': '屏幕内框', 'BezelLip': '屏框金属压边',
    'ScreenPanel210x160x2': '显示屏本体（210×160×2 毫米）',
    'ActiveArea200x150': '屏幕可视区（200×150 毫米）',
    'PixelEyeTop': '屏幕表情眼睛上缘', 'PixelEye': '屏幕表情眼睛',
    'PixelMouth': '屏幕表情嘴部', 'PixelSmileHighlight': '屏幕表情嘴部高光',
    'ControlRail': '下部控制条外壳', 'ControlInset': '控制条内衬',
    'RedKey': '红色按键帽', 'KeyGlyph': '按键标记', 'ControlKnob': '控制旋钮',
    'KnobRing': '旋钮装饰圈', 'KnobPointer': '旋钮指示线',
    'SideClosure': '侧面封闭壳板', 'SideMechanicalBacking': '侧面机械区内衬',
    'SideGuard': '侧面保护边框', 'CyanSideTube': '青色侧灯带',
    'SpeakerBarrel': '侧音箱筒体', 'SpeakerRearSeal': '侧音箱背部封片',
    'PerforatedSpeakerFlange': '侧音箱穿孔法兰', 'SpeakerVisualCone': '侧扬声器锥盆示意',
    'SpeakerSurround': '侧扬声器悬边示意', 'SpeakerCentre': '侧扬声器中心盖',
    'SpeakerBolt': '侧音箱固定螺钉示意', 'WingEdge': '翼板金属包边',
    'WingPaint': '翼板彩色面板', 'WingStripe': '翼板斜向色条',
    'WingHubMark': '翼板圆心标记', 'HandleArm': '提手侧支臂',
    'HandlePivot': '提手连接螺钉示意',
    'VisibleWire': '侧面彩色线束示意',
    'HandleGrip': '提手握把', 'GripBand': '握把包覆带', 'TopSlotTrim': '顶部进碟口饰框',
    'TopInstrumentPanel': '顶部仪表装饰面板', 'TopMeterLatch': '顶部仪表红色拨片',
    'TopMeter': '顶部仪表刻线', 'RearCoolingFin': '后部散热鳍片示意',
    'RearCyanFrame': '后部青色灯框', 'RearRecessLiner': '后部内嵌封板',
    'RearPortRail': '后部接口装饰条', 'RearRedInsert': '后部红色饰条',
    'RearBeaconBase': '后部指示灯底座', 'RearBeaconBand': '后部指示灯环箍',
    'RearBeacon': '后部红色指示灯', 'BassNozzleShell': '低音喷口曲面外罩',
    'BassNozzleRearCollar': '低音喷口根部连接环', 'BassChamberBackplate': '低音模块背部封片',
    'BassNozzleMouthRing': '低音喷口外口环', 'BassSpeakerGasket': '低音单元密封圈示意',
    'BassVisualCone': '低音单元锥盆示意', 'BassDustCap': '低音单元防尘帽示意',
    'NozzlePetalRidge': '低音喷口叶片加强条', 'NozzlePetal': '低音喷口曲面叶片',
    'BassWarningPlaque': '低音喷口警示标牌', 'BassWarningTriangleInset': '低音喷口红色警示图案',
    'BassWarningTriangle': '低音喷口三角警示底片', 'BassNeckFastener': '低音喷口根部螺钉示意',
    'WooferMountSeat': '低音单元安装环示意',
    'WooferEnvelope_D88_Depth40': '低音单元占位（直径88×深40 毫米，隐藏）',
    'LowerPodDiaphragm': '底部小喷口封片', 'LowerPodRim': '底部小喷口口环',
    'LowerPodRib': '底部小喷口叶片', 'LowerPod': '底部小喷口外罩',
    'UnderbodyLoop': '底部回环线束示意',
    'CentralSupportSeat': '底部中央支撑座（打印结构示意）',
    'SupportSocket': '斜向光轴固定套示意',
    'SupportShaft': '底部斜向细光轴（直径6毫米假设）',
    'SupportFoot': '光轴防滑脚垫示意',
    'AntennaBase': '天线底座示意', 'Antenna': '天线外形示意', 'HoodMark': '前罩斜向标记',
    'CDInsertionStudy_D120': '光盘插入占位（直径120 毫米，隐藏）',
    'HoodEdge': '前罩金属细包边', 'HandleInset': '提手支臂内嵌面',
    'WingInnerPaint': '翼板内侧彩色面板', 'SpeakerOuterLip': '侧圆环外口压圈',
    'KeySocket': '按键嵌入底座',
    'StatusKeyFrame': '小红灯方形压框', 'StatusKeyLens': '小红灯透镜',
    'KnobBase': '旋钮底座', 'KnobFlute': '旋钮防滑细齿',
    'LowerPodPetalRidge': '底部小喷口叶片加强筋',
    'Parameters': '尺寸参数与依据', 'ConceptStatus': '设计状态与假设说明',
}


def chinese_label(name):
    """Use Chinese display labels while keeping stable script identifiers."""
    for prefix in sorted(CHINESE_LABELS, key=len, reverse=True):
        if name.startswith(prefix):
            suffix = name[len(prefix):]
            if prefix in ('PixelEye', 'PixelEyeTop'):
                suffix = '左侧' if suffix.startswith('-') else '右侧'
            elif suffix in ('-1', '+1'):
                suffix = '左侧' if suffix == '-1' else '右侧'
            else:
                for english, chinese in [('FrontLeft', '左前'), ('FrontRight', '右前'),
                                         ('RearLeft', '左后'), ('RearRight', '右后'),
                                         ('Left', '左侧'), ('Right', '右侧')]:
                    suffix = suffix.replace(english, chinese)
                suffix = re.sub(r'(\d+)$', lambda m: f'·{int(m[1])+1:02}', suffix)
            return CHINESE_LABELS[prefix]+(' — '+suffix if suffix else '')
    raise ValueError(f'Missing Chinese display label: {name}')


def vector(values):
    return App.Vector(*values)


def box(w, d, h, pos, radius=0):
    shape = Part.makeBox(w, d, h, vector(pos))
    if radius:
        shape = shape.makeFillet(min(radius, .45*min(w, d, h)), shape.Edges)
    return shape


def cylinder(radius, length, pos, axis=(0, 0, 1)):
    return Part.makeCylinder(radius, length, vector(pos), vector(axis))


def ring(outer, inner, length, pos, axis=(0, 0, 1)):
    return cylinder(outer, length, pos, axis).cut(cylinder(inner, length, pos, axis))


def profile(points, plane, origin, thickness):
    if plane == 'YZ':
        pts = [App.Vector(0, u, v) for u, v in points]
        direction = App.Vector(thickness, 0, 0)
    else:
        pts = [App.Vector(u, 0, v) for u, v in points]
        direction = App.Vector(0, thickness, 0)
    wire = Part.makePolygon(pts + [pts[0]])
    face = Part.Face(wire)
    shape = face.extrude(direction)
    shape.translate(vector(origin))
    return shape


def rounded_plate(w, h, depth, pos, radius, plane='XZ'):
    """Rounded silhouette independent of plate thickness."""
    if plane == 'XZ':
        shape = box(w, depth, h, pos)
        edges = [e for e in shape.Edges if e.BoundBox.YLength > depth-.01]
    else:
        shape = box(depth, w, h, pos)
        edges = [e for e in shape.Edges if e.BoundBox.XLength > depth-.01]
    return shape.makeFillet(radius, edges)


def rounded_frame(w, h, depth, border, pos, radius=8):
    x, y, z = pos
    outer = box(w, depth, h, pos)
    edges = [e for e in outer.Edges if e.BoundBox.YLength > depth - .01]
    outer = outer.makeFillet(radius, edges)
    inner = box(w-2*border, depth+2, h-2*border, (x+border, y-1, z+border))
    edges = [e for e in inner.Edges if e.BoundBox.YLength > depth+1.99]
    inner = inner.makeFillet(max(1, radius-border/2), edges)
    return outer.cut(inner)


def tube(points, radius):
    """Swept circular wire; decorative cable, not an electrical model."""
    points = [vector(p) for p in points]
    curve = Part.BSplineCurve()
    if (points[0]-points[-1]).Length < .01:
        curve.interpolate(points[:-1], PeriodicFlag=True)
    else:
        curve.interpolate(points)
    path = Part.Wire(curve.toShape())
    tangent = curve.tangent(curve.FirstParameter)[0]
    section = Part.Wire([Part.makeCircle(radius, points[0], tangent)])
    return path.makePipeShell([section], True, False)


def polygon_tube(points, radius):
    """Close-fitting indicator tube without spline overshoot at corners."""
    pts = [vector(p) for p in points]
    pieces = [Part.makeSphere(radius, p) for p in pts]
    for a, c in zip(pts, pts[1:]+pts[:1]):
        direction = c-a
        pieces.append(cylinder(radius, direction.Length, tuple(a), tuple(direction)))
    return pieces[0].multiFuse(pieces[1:]).removeSplitter()


def round_loft(sections):
    """Smooth solid of circular sections (axial position, radius, offset)."""
    wires = [Part.Wire([Part.makeCircle(r, App.Vector(0, offset, z))])
             for z, r, offset in sections]
    return Part.makeLoft(wires, True, False)


def sector_wire(outer, inner, z, start, stop):
    def p(radius, angle):
        a = math.radians(angle)
        return App.Vector(radius*math.cos(a), radius*math.sin(a), z)
    mid = (start+stop)/2
    return Part.Wire([
        Part.Arc(p(outer, start), p(outer, mid), p(outer, stop)).toShape(),
        Part.makeLine(p(outer, stop), p(inner, stop)),
        Part.Arc(p(inner, stop), p(inner, mid), p(inner, start)).toShape(),
        Part.makeLine(p(inner, start), p(outer, start)),
    ])


class Study:
    """Own ungrouped concept features and explicitly hidden reservations."""

    def __init__(self, doc):
        self.doc = doc
        self.items = []

    def add(self, name, shape, color, _category, material='paint', visible=True):
        if shape.isNull() or not shape.isValid() or not shape.Solids:
            raise ValueError(f'Invalid concept solid: {name}')
        obj = self.doc.addObject('Part::Feature', name)
        obj.Label = chinese_label(name)
        obj.Shape = shape
        obj.addProperty('App::PropertyString', 'EvidenceStatus', 'Design')
        obj.EvidenceStatus = '外形草模；尺寸假设；未试装/打印/声学验证'
        obj.addProperty('App::PropertyString', 'RenderMaterial', 'Design')
        obj.RenderMaterial = material
        obj.ViewObject.ShapeColor = color
        obj.ViewObject.LineColor = tuple(v*.45 for v in color)
        obj.ViewObject.DisplayMode = 'Flat Lines'
        obj.ViewObject.LineWidth = .6
        obj.Visibility = visible
        self.items.append(obj)
        return obj

    def bolt(self, name, pos, axis, radius=3.4):
        shape = cylinder(radius, 1.8, pos, axis)
        slot = box(radius*1.2, .9, 2.8, (-radius*.6, -.45, -.5))
        slot.rotate(App.Vector(), App.Vector(0, 0, 1), 25)
        slot.Placement = App.Placement(vector(pos), App.Rotation(App.Vector(0, 0, 1), vector(axis))).multiply(slot.Placement)
        return self.add(name, shape.cut(slot), SILVER, 'Details', 'metal')


def add_central_support(study):
    """Splay four smooth metal shafts from a compact assumed printed seat."""
    study.add('CentralSupportSeat', box(84, 70, 16, (-42, 55, 22), 3),
              DARK, 'Hull')
    for side, side_name in [(-1, 'Left'), (1, 'Right')]:
        for fore, fore_name in [(-1, 'Front'), (1, 'Rear')]:
            name = fore_name+side_name
            root = App.Vector(side*16, 90+fore*23, 28)
            tip = App.Vector(side*122, 90+fore*108, -97)
            direction = tip-root
            shaft = study.add('SupportShaft'+name,
                              cylinder(3, direction.Length, tuple(root), tuple(direction)),
                              SILVER, 'Hull', 'metal')
            shaft.addProperty('App::PropertyVector', 'RootCentre', 'Support')
            shaft.addProperty('App::PropertyVector', 'FootCentre', 'Support')
            shaft.addProperty('App::PropertyLength', 'AssumedDiameter', 'Support')
            shaft.RootCentre = root
            shaft.FootCentre = tip
            shaft.AssumedDiameter = 6
            study.add('SupportSocket'+name,
                      ring(6, 3, 22, tuple(root), tuple(direction)),
                      DARK, 'Hull')
            study.add('SupportFoot'+name,
                      cylinder(8, 6, (tip.x, tip.y, -100)),
                      DARK, 'Hull', 'rubber')


def build(root):
    """Create and save a separate appearance concept without changing terminal."""
    root = Path(root)
    out = root/'cad/drone-concept'
    out.mkdir(parents=True, exist_ok=True)
    if 'vintrox_drone_refined' in App.listDocuments():
        raise RuntimeError('Concept document already open; close it before rebuilding.')
    doc = App.newDocument('vintrox_drone_refined')
    doc.Label = 'VINTROX Drone — 中央四光轴支撑'
    b = Study(doc)
    params = doc.addObject('Spreadsheet::Sheet', 'Parameters')
    params.Label = chinese_label('Parameters')
    values = [
        ('ScreenWidth', 210, '用户测量口述 mm'), ('ScreenHeight', 160, '用户测量口述 mm'),
        ('ScreenThickness', 2, '用户测量口述 mm'), ('ActiveWidth', 200, '用户指定 mm'),
        ('ActiveHeight', 150, '用户指定 mm'), ('HullWidth', 240, '外观假设 mm'),
        ('HullDepth', 176, '外观假设 mm'), ('WingTop', 365, '外观假设 Z mm'),
        ('WooferDiameter', 88, '占位假设；未选单元 mm'),
        ('WooferDepth', 40, '占位假设；不含接线/行程 mm'),
    ]
    for row, (key, value, evidence) in enumerate(values, 1):
        params.set(f'A{row}', key)
        params.set(f'B{row}', str(value))
        params.setAlias(f'B{row}', key)
        params.set(f'C{row}', evidence)
    params.setColumnWidth('A', 180)
    params.setColumnWidth('C', 300)

    # Continuous main enclosure; only the screen, CD slot, and bass neck open.
    bass_axis = App.Vector(0, .83, -.56)
    bass_axis.normalize()
    bass_origin = App.Vector(0, 168, 162)
    bass_passage = cylinder(47, 100, tuple(bass_origin-bass_axis*18), tuple(bass_axis))
    hull = box(240, 176, 235, (-120, 0, 38), 10)
    hull = hull.cut(box(232, 168, 227, (-116, 4, 42), 6))
    hull = hull.cut(box(216, 25, 176, (-108, -10, 65), 4))
    hull = hull.cut(bass_passage)
    hull = hull.cut(box(290, 190, 40, (-145, -5, 247)))
    b.add('MainEnclosureShell', hull, GOLD, 'Hull')
    roof = profile([(0, 248), (45, 275), (164, 275), (176, 264),
                    (176, 261), (163, 272), (46, 272), (0, 244)], 'YZ', (-120, 0, 0), 240)
    roof = roof.cut(box(124, 4, 35, (-62, 62, 260)))
    b.add('SlopedUpperArmour', roof, GOLD, 'Hull')
    shoulder = [(0, 248), (45, 275), (164, 275), (176, 264), (176, 247), (0, 247)]
    for side in (-1, 1):
        b.add(f'RoofSideClosure{side:+}', profile(shoulder, 'YZ', (side*117, 0, 0), side*3), GOLD, 'Hull')
    b.add('RearUpperClosure', box(240, 8, 18, (-120, 168, 244), 2), GOLD, 'Hull')
    b.add('BottomChassis', box(232, 158, 7, (-116, 9, 35), 2), DARK, 'Hull')
    belly = profile([(20, 35), (38, 15), (144, 12), (172, 28), (172, 42), (20, 42)],
                    'YZ', (-108, 0, 0), 216)
    b.add('ClosedBellyPan', belly, DARK, 'Hull', 'metal')
    back = box(232, 9, 218, (-116, 175, 43), 4).cut(bass_passage)
    b.add('RearServicePanel', back, GOLD, 'Hull')
    b.add('RearStructuralFrame', rounded_frame(232, 214, 5, 9, (-116, 181, 45), 12), GOLD, 'Hull')
    # Deep continuous brow: large front corner radii and descending side ends.
    hood = rounded_plate(250, 76, 56, (-125, -32, 187), 19)
    hood = hood.cut(rounded_plate(232, 98, 60, (-116, -34, 151), 17))
    b.add('ProjectingBrow', hood, GOLD, 'Hull')
    hood_liner = rounded_plate(234, 67, 41, (-117, -27, 187), 17)
    hood_liner = hood_liner.cut(rounded_plate(228, 91, 45, (-114, -29, 155), 15))
    b.add('BrowUnderside', hood_liner, DARK, 'Hull', 'rubber')
    edge = rounded_plate(248, 74, 1.2, (-124, -33, 188), 18)
    edge = edge.cut(rounded_plate(244, 74, 4, (-122, -34, 186), 16))
    b.add('HoodEdge', edge, EDGE, 'Hull', 'metal')
    # Thin bright gasket around the rounded, recessed flat panel.
    b.add('ScreenBezel', rounded_frame(224, 174, 11, 10, (-112, -13, 63), 15), DARK, 'Face', 'rubber')
    b.add('BezelLip', rounded_frame(228, 178, 3, 2, (-114, -15, 61), 16), EDGE, 'Face', 'metal')
    panel = doc.addObject('Part::Box', 'ScreenPanel210x160x2')
    panel.Label = chinese_label('ScreenPanel210x160x2')
    panel.setExpression('Length', 'Parameters.ScreenWidth')
    panel.setExpression('Width', 'Parameters.ScreenThickness')
    panel.setExpression('Height', 'Parameters.ScreenHeight')
    panel.Placement.Base = App.Vector(-105, -1, 70)
    panel.addProperty('App::PropertyString', 'EvidenceStatus', 'Design')
    panel.EvidenceStatus = '用户测量210×160×2mm；接口与安装净空待验证'
    panel.ViewObject.ShapeColor = DARK
    panel.addProperty('App::PropertyString', 'RenderMaterial', 'Design')
    panel.RenderMaterial = 'rubber'
    panel.Visibility = True
    b.items.append(panel)
    active = doc.addObject('Part::Box', 'ActiveArea200x150')
    active.Label = chinese_label('ActiveArea200x150')
    active.setExpression('Length', 'Parameters.ActiveWidth')
    active.Width = .8
    active.setExpression('Height', 'Parameters.ActiveHeight')
    active.Placement.Base = App.Vector(-100, -9, 75)
    active.ViewObject.ShapeColor = GREEN
    active.addProperty('App::PropertyString', 'RenderMaterial', 'Design')
    active.RenderMaterial = 'screen'
    b.items.append(active)
    # Display-only face, using the existing flat 4:3 screen; no curved glass.
    for x in (-43, 33):
        b.add(f'PixelEye{x}', box(12, .5, 22, (x, -9.6, 166)), DARK, 'Face', 'screen_ink')
        b.add(f'PixelEyeTop{x}', box(6, .5, 6, (x+3, -9.6, 188)), DARK, 'Face', 'screen_ink')
    b.add('PixelMouth', profile([(-65, 132), (65, 132), (65, 115), (52, 115), (52, 103),
          (34, 103), (34, 95), (-34, 95), (-34, 103), (-52, 103), (-52, 115), (-65, 115)],
          'XZ', (0, -9.6, 0), .5), DARK, 'Face', 'screen_ink')
    b.add('PixelSmileHighlight', box(118, .4, 6, (-59, -10, 122)), WHITE, 'Face', 'screen')
    b.add('ControlRail', rounded_plate(228, 31, 25, (-114, -19, 27), 6), METAL, 'Face', 'metal')
    b.add('ControlInset', rounded_plate(216, 23, 4, (-108, -21, 31), 3), DARK, 'Face')
    # Four red keys with a small recessed red indicator between the first two.
    for i, x in enumerate((-101, -51, -26, -1)):
        b.add(f'KeySocket{i}', box(23, 3, 21, (x-1, -24, 32), 1), METAL, 'Face', 'metal')
        b.add(f'RedKey{i}', box(21, 5, 17, (x, -28, 34), 1.5), RED, 'Face')
        # Simple distinct line glyphs, rather than identical dash marks.
        glyphs = [[(5,39),(8,38),(13,46),(15,44)],
                  [(5,38),(9,46),(12,40),(16,39)],
                  [(5,43),(9,46),(13,43),(9,40),(16,40)],
                  [(5,39),(8,40),(11,46),(14,40),(16,39)]]
        glyph = [(x+u, -28.6, v) for u,v in glyphs[i]]
        b.add(f'KeyGlyph{i}', tube(glyph, .55), WHITE, 'Face')
    b.add('StatusKeyFrame', rounded_frame(18, 18, 3, 3, (-76, -27, 33), 2), METAL, 'Face', 'metal')
    b.add('StatusKeyLens', cylinder(4.3, 2, (-67, -28, 42), (0, -1, 0)), RED, 'Face', 'red_light')
    for i in range(3):
        x = 40+i*26
        b.add(f'KnobBase{i}', cylinder(11, 3, (x, -23, 42), (0, -1, 0)), METAL, 'Face', 'metal')
        b.add(f'ControlKnob{i}', cylinder(8.6, 11, (x, -26, 42), (0, -1, 0)), DARK, 'Face', 'rubber')
        b.add(f'KnobRing{i}', ring(9, 7.8, 1, (x, -37, 42), (0, -1, 0)), SILVER, 'Face', 'metal')
        teeth = []
        for j in range(32):
            a = j*math.tau/32
            teeth.append(cylinder(.38, 8, (x+8.55*math.cos(a), -27, 42+8.55*math.sin(a)), (0, -1, 0)))
        b.add(f'KnobFlute{i}', Part.makeCompound(teeth), METAL, 'Face', 'metal')
        b.add(f'KnobPointer{i}', box(.8, .6, 3.5, (x-.4, -38.2, 35)), WHITE, 'Face')

    # Side rings and the thin illuminated armour frame behind them.
    side_outline = [(31, 91), (47, 62), (157, 62), (177, 84), (177, 232), (151, 260), (48, 252), (31, 227)]
    inner_outline = [(39, 95), (52, 70), (152, 70), (169, 88), (169, 228), (147, 252), (54, 244), (39, 223)]
    wing = [(59, 147), (54, 167), (106, 265), (190, 350), (208, 365),
            (217, 361), (202, 314), (109, 175), (109, 151), (95, 135), (76, 132)]
    for side in (-1, 1):
        suffix = 'Left' if side < 0 else 'Right'
        direction = (side, 0, 0)
        b.add('SideClosure'+suffix, profile(side_outline, 'YZ', (side*120, 0, 0), side*15), GOLD, 'Sides')
        b.add('SideMechanicalBacking'+suffix, profile(inner_outline, 'YZ', (side*134, 0, 0), side*3), DARK, 'Sides', 'metal')
        side_frame = profile(side_outline, 'YZ', (side*135, 0, 0), side*4)
        side_frame = side_frame.cut(profile(inner_outline, 'YZ', (side*134, 0, 0), side*6))
        b.add('SideGuard'+suffix, side_frame, GOLD, 'Sides')
        lightpts = [(side*139.5, y, z) for y, z in [(40, 94), (52, 72), (151, 72), (166, 90), (166, 226), (145, 248), (54, 241), (41, 220)]]
        b.add('CyanSideTube'+suffix, polygon_tube(lightpts, 1.1), CYAN, 'Details', 'emission')
        b.add('SpeakerBarrel'+suffix, ring(58, 50, 24, (side*134, 99, 164), direction), DARK, 'Sides', 'metal')
        b.add('SpeakerRearSeal'+suffix, cylinder(50, 3, (side*135, 99, 164), direction), DARK, 'Sides', 'rubber')
        flange = ring(63, 50, 5, (side*154, 99, 164), direction)
        holes = []
        for i in range(16):
            a = i*math.tau/16
            holes.append(cylinder(2, 8, (side*153, 99+57*math.cos(a), 164+57*math.sin(a)), direction))
        b.add('PerforatedSpeakerFlange'+suffix, flange.cut(Part.makeCompound(holes)), METAL, 'Sides', 'metal')
        cone = Part.makeCone(44, 18, 12, App.Vector(side*160, 99, 164), vector((-side, 0, 0)))
        b.add('SpeakerVisualCone'+suffix, cone, DARK, 'Sides', 'rubber')
        b.add('SpeakerOuterLip'+suffix, ring(53, 49, 6, (side*159, 99, 164), direction), METAL, 'Sides', 'metal')
        b.add('SpeakerSurround'+suffix, ring(50, 44, 4, (side*158, 99, 164), direction), DARK, 'Sides', 'rubber')
        b.add('SpeakerCentre'+suffix, cylinder(18, 5, (side*155, 99, 164), direction), METAL, 'Sides', 'metal')
        for i in range(8):
            a = i*math.tau/8
            b.bolt(f'SpeakerBolt{suffix}{i}', (side*160, 99+58*math.cos(a), 164+58*math.sin(a)), direction, 2.8)
        blade = profile(wing, 'YZ', (side*164, 0, 0), side*7)
        blade = blade.fuse(cylinder(26, 7, (side*164, 83, 158), direction)).removeSplitter()
        b.add('WingEdge'+suffix, blade, METAL, 'Wings', 'metal')
        inset = [(63, 149), (58, 167), (110, 264), (193, 349), (208, 360),
                 (212, 358), (198, 315), (105, 174), (105, 153), (93, 139), (78, 136)]
        paint = profile(inset, 'YZ', (side*171, 0, 0), side*.9)
        paint = paint.fuse(cylinder(23.5, .9, (side*171, 83, 158), direction)).removeSplitter()
        b.add('WingPaint'+suffix, paint, RED if side < 0 else GOLD, 'Wings')
        inside = profile(inset, 'YZ', (side*163, 0, 0), side*.9)
        inside = inside.fuse(cylinder(23.5, .9, (side*163, 83, 158), direction)).removeSplitter()
        b.add('WingInnerPaint'+suffix, inside, RED if side < 0 else GOLD, 'Wings')
        # Distinctive diagonal markings on the upper wing.
        for i in range(3):
            z = 278+i*18
            stripe = [(95, z), (225, z+15), (225, z+24), (95, z+9)]
            stripe_shape = profile(stripe, 'YZ', (side*172, 0, 0), side*.4)
            wingmask = profile(inset, 'YZ', (side*171.9, 0, 0), side*1)
            clipped = stripe_shape.common(wingmask)
            if clipped.Solids:
                b.add(f'WingStripe{suffix}{i}', clipped, WHITE, 'Details')
        mark = ring(20, 16.5, .5, (side*172.5, 83, 158), direction)
        for i in range(6):
            gap = box(4, 50, 2.5, (side*172-2, 58, 156.75))
            gap.rotate(App.Vector(side*172, 83, 158), App.Vector(1, 0, 0), i*60)
            mark = mark.cut(gap)
        b.add('WingHubMark'+suffix, mark, WHITE, 'Details')
        # Broad rounded handle cheeks, recessed dark face and wider wrapped grip.
        arm = profile([(49, 252), (77, 318), (120, 329), (145, 316),
                       (144, 301), (108, 298), (84, 244), (65, 237)],
                      'YZ', (side*108, 0, 0), side*9)
        edges = [e for e in arm.Edges if e.BoundBox.XLength > 8.99]
        arm = arm.makeFillet(6, edges)
        b.add('HandleArm'+suffix, arm, METAL, 'Wings', 'metal')
        inset_arm = arm.copy()
        inset_arm.scale(.93, App.Vector(side*108, 96, 282))
        inset_arm.translate(App.Vector(side*1.1, 0, 0))
        b.add('HandleInset'+suffix, inset_arm, DARK, 'Wings', 'rubber')
        b.bolt('HandlePivot'+suffix, (side*119, 71, 254), direction, 5.5)
        for z, color in ((105, RED), (218, RED), (230, CYAN)):
            b.add(f'VisibleWire{suffix}{z}', tube([(side*140, 47, z), (side*144, 64, z-4),
                  (side*141, 128, z+3), (side*139, 152, z+10)], 1.4), color, 'Details', 'rubber')
    b.add('HandleGrip', box(224, 37, 30, (-112, 104, 302), 11), OLIVE, 'Wings', 'rubber')
    for i in range(14):
        pts = []
        # Follow the actual rounded rectangular section, with a diagonal seam.
        for cy, cz, start in ((7.5,4,0),(-7.5,4,90),(-7.5,-4,180),(7.5,-4,270)):
            for j in range(7):
                a = math.radians(start+j*15)
                dy, dz = cy+11.3*math.cos(a), cz+11.3*math.sin(a)
                pts.append((-102+i*15.2+dz*.28,122.5+dy,317+dz))
        pts.append(pts[0])
        b.add(f'GripBand{i}', tube(pts, .5), (.16, .18, .11), 'Details', 'rubber')

    # Top slot and a slim instrumentation strip; the strip is a visual insert.
    slot_trim = box(134, 12, 3, (-67, 58, 274)).cut(box(124, 4, 5, (-62, 62, 273)))
    b.add('TopSlotTrim', slot_trim, DARK, 'Hull')
    def on_slope(shape):
        shape.rotate(App.Vector(), App.Vector(1, 0, 0), 31)
        shape.translate(App.Vector(0, 30, 266))
        return shape
    b.add('TopInstrumentPanel', on_slope(box(152, 24, 3, (-76, 0, 0), 1)), DARK, 'Face')
    for i in range(34):
        z = 2+4*math.sin(i*.55)
        b.add(f'TopMeter{i}', on_slope(box(2, 5+abs(z), .4, (-69+i*4, 7, 3.2))), RED if i%3 else EDGE, 'Details', 'screen')
    b.add('TopMeterLatch', on_slope(box(8, 7, 6, (-4, 20, 2), 1)), RED, 'Details')
    for i in range(23):
        b.add(f'RearCoolingFin{i}', box(3, 23, 13, (-110+i*10, 163, 266), 1), DARK, 'Rear', 'metal')
    rear_light = rounded_frame(226, 192, 3, 3, (-113, 183, 58), 10)
    b.add('RearCyanFrame', rear_light, CYAN, 'Rear', 'emission')
    b.add('RearRecessLiner', box(214, 4, 178, (-107, 184, 58), 2).cut(bass_passage), DARK, 'Rear', 'metal')
    b.add('RearPortRail', box(224, 10, 28, (-112, 181, 226), 3), DARK, 'Rear')
    b.add('RearRedInsert', box(182, 4, 7, (-91, 192, 237), 1), RED, 'Rear')
    for side in (-1, 1):
        axis = (0, 1, 0)
        x = side*107
        b.add(f'RearBeaconBase{side:+}', cylinder(13, 11, (x, 180, 261), axis), DARK, 'Rear', 'rubber')
        b.add(f'RearBeacon{side:+}', Part.makeCone(12, 5, 17, App.Vector(x, 191, 261), vector(axis)), RED, 'Rear', 'red_light')
        b.add(f'RearBeaconBand{side:+}', ring(10, 8, 3, (x, 196, 261), axis), DARK, 'Rear')
    # Bulged transition fairing and separately modelled curved exhaust petals.
    axis = bass_axis
    origin = bass_origin
    rot = App.Rotation(App.Vector(0, 0, 1), axis)
    def place(shape):
        shape.Placement = App.Placement(origin, rot).multiply(shape.Placement)
        return shape
    outer = round_loft([(0, 49, 0), (10, 54, -1), (32, 65, -2),
                        (57, 69, -1), (78, 68, 0), (91, 66, 0)])
    inner = round_loft([(-1, 44.5, 0), (10, 50, -1), (32, 61, -2),
                        (57, 65, -1), (78, 64, 0), (93, 62, 0)])
    b.add('BassNozzleShell', place(outer.cut(inner)), (.60, .37, .13), 'Rear')
    b.add('BassNozzleRearCollar', place(ring(55, 45, 8, (0, 0, -3))), METAL, 'Rear', 'metal')
    b.add('BassChamberBackplate', place(cylinder(45, 4, (0, 0, 5))), DARK, 'Rear', 'metal')
    b.add('BassNozzleMouthRing', place(ring(69, 63, 5, (0, 0, 84))), DARK, 'Rear', 'metal')
    b.add('BassSpeakerGasket', place(ring(63, 54, 4, (0, 0, 93))), DARK, 'Rear', 'rubber')
    b.add('BassVisualCone', place(round_loft([(76, 20, 0), (82, 28, 0), (88, 42, 0), (94, 54, 0)])), DARK, 'Rear', 'rubber')
    b.add('BassDustCap', place(Part.makeSphere(22, App.Vector(0, 0, 91), App.Vector(0, 0, 1), 0, 90)), DARK, 'Rear', 'rubber')
    for i in range(24):
        a = i*15
        sections = [(72, 69, 64.5), (86, 69.3, 65), (103, 64, 59.5), (112, 60.5, 56)]
        petal = Part.makeLoft([sector_wire(ro, ri, z, a+1.6, a+13.4)
                              for z, ro, ri in sections], True, False)
        b.add(f'NozzlePetal{i}', place(petal), METAL, 'Rear', 'metal')
        ridge = Part.makeLoft([sector_wire(ro+.7, ro, z, a+6.6, a+8.4)
                              for z, ro, _ in sections], True, False)
        b.add(f'NozzlePetalRidge{i}', place(ridge), SILVER, 'Details', 'metal')
    warning = Part.makeLoft([sector_wire(70, 69, z, 251, 289) for z in (46, 62)], True, False)
    b.add('BassWarningPlaque', place(warning), WHITE, 'Details')
    triangle = profile([(-9, 68), (9, 68), (0, 84)], 'XZ', (0, -70, 0), .5)
    b.add('BassWarningTriangle', place(triangle), WHITE, 'Details')
    red_triangle = profile([(-6.7, 69.5), (6.7, 69.5), (0, 81.5)], 'XZ', (0, -70.6, 0), .5)
    b.add('BassWarningTriangleInset', place(red_triangle), RED, 'Details')
    for i in range(8):
        a = i*math.tau/8
        bolt = cylinder(2.3, 2, (50*math.cos(a), 50*math.sin(a), 3))
        b.add(f'BassNeckFastener{i}', place(bolt), SILVER, 'Details', 'metal')
    seat = place(ring(48, 44, 4, (0, 0, 22)))
    b.add('WooferMountSeat', seat, METAL, 'Rear', 'metal')
    reserve = b.add('WooferEnvelope_D88_Depth40', place(cylinder(44, 40, (0, 0, 26))), (.8, .18, .06), 'Reservations', visible=False)
    reserve.addProperty('App::PropertyLength', 'AssumedDiameter', 'Reservation')
    reserve.AssumedDiameter = 88
    reserve.addProperty('App::PropertyLength', 'AssumedDepth', 'Reservation')
    reserve.AssumedDepth = 40
    reserve.ViewObject.Transparency = 70
    # Longer front/downturned small exhausts with tapering, layered dark petals.
    for side in (-1, 1):
        direction = App.Vector(side*.21, -.59, -.78)
        direction.normalize()
        p = App.Vector(side*101, 18, 39)
        placement = App.Placement(p, App.Rotation(App.Vector(0, 0, 1), direction))
        def lower_place(shape):
            shape.Placement = placement.multiply(shape.Placement)
            return shape
        shell = round_loft([(0, 18, 0), (10, 24, 0), (27, 28, 0), (37, 27, 0)])
        shell = shell.cut(round_loft([(-1, 14, 0), (10, 20, 0), (27, 24, 0), (39, 23, 0)]))
        b.add(f'LowerPod{side:+}', lower_place(shell), GOLD, 'Hull')
        b.add(f'LowerPodRim{side:+}', lower_place(ring(28, 23, 3, (0,0,33))), METAL, 'Hull', 'metal')
        b.add(f'LowerPodDiaphragm{side:+}', lower_place(cylinder(19, 3, (0,0,32))), DARK, 'Hull', 'rubber')
        for i in range(18):
            sections = [(30, 27.5, 24), (40, 26.5, 23), (53, 22, 18.5)]
            rib = Part.makeLoft([sector_wire(ro, ri, z, i*20+1.5, i*20+18.5) for z,ro,ri in sections], True, False)
            b.add(f'LowerPodRib{side:+}_{i}', lower_place(rib), DARK, 'Details', 'metal')
            ridge = Part.makeLoft([sector_wire(ro+.5, ro, z, i*20+8, i*20+10) for z,ro,ri in sections], True, False)
            b.add(f'LowerPodPetalRidge{side:+}_{i}', lower_place(ridge), SILVER, 'Details', 'metal')
    # Existing decorative cable loops stay above the new support plane.
    for i, x in enumerate((-48, 48)):
        b.add(f'UnderbodyLoop{i}', tube([(x, 57, 36), (x+10, 66, 16), (x+8, 121, 13), (x, 149, 37)], 3), DARK, 'Details', 'rubber')
    add_central_support(b)
    b.add('AntennaBase', cylinder(5, 9, (0, 159, 273)), DARK, 'Details', 'rubber')
    b.add('Antenna', tube([(0, 159, 281), (-4, 163, 316), (-18, 177, 351), (-46, 193, 378)], 1.1), DARK, 'Details', 'rubber')
    for side in (-1, 1):
        for i in range(3):
            x = side*(96+i*7)
            b.add(f'HoodMark{side:+}_{i}', profile([(x, 256), (x+3, 256), (x+7, 250), (x+4, 250)], 'XZ', (0, -32.3, 0), .3), WHITE, 'Details')
    # Hidden CD envelope shows the assumed clear insertion path, not validated travel.
    # CD plane is XZ for the top slot, normal is Y.
    disc = cylinder(60, 1.2, (0, 63, 338), (0, 1, 0))
    b.add('CDInsertionStudy_D120', disc, SILVER, 'Reservations', visible=False)
    info = doc.addObject('App::FeaturePython', 'ConceptStatus')
    info.Label = chinese_label('ConceptStatus')
    info.addProperty('App::PropertyString', 'Scope')
    info.Scope = '外形评审草模；非打印分件包；无内部硬件装配验证；屏幕平面；低音D88×40是假设占位'
    info.addProperty('App::PropertyString', 'ParameterWorkflow')
    info.ParameterWorkflow = '屏幕对象绑定参数表；装甲等造型由生成脚本重建，不是全模型参数联动'
    doc.recompute()
    Gui.activeDocument().activeView().viewAxonometric()
    Gui.activeDocument().activeView().fitAll()
    Gui.updateGui()
    save_outputs(doc, b.items, out)
    return doc


def save_outputs(doc, items, out):
    """Save GUI state and refresh STEP, manifest and render meshes together."""
    path = out/'vintrox-drone-concept.FCStd'
    doc.saveAs(str(path))
    visible = [o for o in items if o.Visibility]
    Import.export(visible, str(out/'vintrox-drone-concept.step'))
    bbox = Part.makeCompound([o.Shape for o in visible]).BoundBox
    manifest = {
        'revision': 'v5-central-four-shaft-support',
        'tree_structure': 'flat', 'group_count': 0,
        'status': 'appearance-study-only', 'physical_tests': False,
        'screen_panel_mm': [210, 160, 2], 'active_area_mm': [200, 150],
        'woofer_reservation_mm': {'diameter': 88, 'depth': 40, 'basis': 'unselected placeholder'},
        'support': {'shafts': 4, 'shaft_diameter_mm': 6, 'ground_z_mm': -100,
                    'foot_centres_span_mm': [244, 216],
                    'basis': 'appearance assumptions; load and stability untested'},
        'visible_features': len(visible), 'bbox_mm': [bbox.XLength, bbox.YLength, bbox.ZLength],
        'bbox_min_mm': [bbox.XMin, bbox.YMin, bbox.ZMin],
        'bbox_max_mm': [bbox.XMax, bbox.YMax, bbox.ZMax],
        'fcstd_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'features': [{'name': o.Name, 'label': o.Label, 'solids': len(o.Shape.Solids), 'valid': o.Shape.isValid()} for o in items],
    }
    (out/'concept-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    meshes = []
    for obj in visible:
        vertices, faces = obj.Shape.tessellate(.12)
        meshes.append({'name': obj.Name, 'vertices': [[v.x, v.y, v.z] for v in vertices],
                       'faces': faces, 'color': list(obj.ViewObject.ShapeColor[:3]),
                       'material': getattr(obj, 'RenderMaterial', 'paint')})
    meshfile = Path(tempfile.gettempdir())/'vintrox-drone-render-meshes.json'
    meshfile.write_text(json.dumps({'fcstd_sha256': manifest['fcstd_sha256'], 'objects': meshes}))
    print(json.dumps({'saved': str(path), 'visible_features': len(visible), 'bbox_mm': manifest['bbox_mm'],
                      'meshfile': str(meshfile)}, ensure_ascii=False))
    return doc
