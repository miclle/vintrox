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
from drone_guard_notch import trim_guard_notch
from drone_status_rim import restore_status_rim
from drone_petal_hardware import petal_surface_parts
from drone_nozzle_interior import interior_parts
from drone_fairing_shoulder import root_shifted_fairing as blended_fairing_parts
from drone_nozzle_markings import MARKING_SPEC, label_positions as warning_label_positions
from drone_belly_relief import relieved_belly, moved_service_shape
from drone_nozzle_root_profile import (root_shifted_leaf_parts,
    root_shifted_rolls, root_shifted_hinge, root_shifted_fairing, ROOT_DELTA, shifted_z)
import Import
from drone_wing_fold import WING_OUTLINE, WING_CREASE, GOLD_WING_CREASE_OFFSETS, gold_wing_fold_parts


GOLD = (0.61, 0.52, 0.25)
EDGE = (0.76, 0.67, 0.40)
DARK = (0.045, 0.061, 0.067)
METAL = (0.24, 0.29, 0.30)
SILVER = (0.57, 0.62, 0.61)
RED = (0.64, 0.055, 0.035)
WHITE = (0.85, 0.83, 0.65)
CYAN = (0.05, 0.90, 0.94)
GREEN = (0.27, 0.67, 0.19)
OLIVE = (0.36, 0.38, 0.25)
NOZZLE_PETALS = 12  # Rear guide pitch and both oblique views; appearance inference.
COOLING_FINS = 15  # Repeating 22–23 px bands in the fixed rear video view.
UNDERBODY_LOOP_RADIUS = 3.5  # Fixed-video cable thickness fit; appearance only.
NOZZLE_RADIAL_SCALE = 0.90  # Rear fixed-view fit; local X/Y only, appearance only.
NOZZLE_SHELL_RADIAL_SCALE = 0.96  # Recessed housing fit; kept wider than the nozzle interior.
NOZZLE_PETAL_TANGENTIAL_SCALE = 0.94  # Fixed-view petal span fit; root band remains unchanged.

CHINESE_LABELS = {
    'MainEnclosureShell': '主机连续外壳', 'SlopedUpperArmour': '顶部斜面外罩',
    'RoofSideClosure': '顶罩侧封板', 'RearUpperClosure': '后部上封板',
    'BottomChassis': '底盘', 'ClosedBellyPan': '底部封闭托壳',
    'RearServicePanel': '后部检修盖板', 'RearStructuralFrame': '后盖外框',
    'ProjectingBrow': '前伸屏幕罩', 'BrowUnderside': '屏幕罩内衬',
    'ScreenBezel': '屏幕内框', 'BezelLip': '屏框金属压边',
    'ScreenPanel210x160x2': '显示屏本体（210×160×2 毫米）',
    'ActiveArea200x150': '屏幕可视区（200×150 毫米）',
    'ScreenCurvedCover': '曲面透明屏幕罩（外观与光学假设）',
    'PixelEyeTop': '屏幕表情眼睛上缘', 'PixelEye': '屏幕表情眼睛',
    'PixelMouth': '屏幕表情嘴部', 'PixelSmileHighlight': '屏幕表情嘴部高光',
    'ControlKeyBed': '按键区凹入底板', 'ControlRail': '下部控制条外壳', 'ControlInset': '控制条内衬',
    'RedKey': '红色按键帽', 'KeyGlyph': '按键标记', 'ControlKnob': '控制旋钮',
    'KnobRing': '旋钮装饰圈', 'KnobPointer': '旋钮指示线',
    'SideClosure': '侧面封闭壳板', 'SideMechanicalBacking': '侧面机械区内衬',
    'SideGuard': '侧面保护边框', 'CyanSideTube': '青色侧灯带',
    'SpeakerBarrel': '侧音箱筒体', 'SpeakerRearSeal': '侧音箱背部封片',
    'PerforatedSpeakerFlange': '侧音箱穿孔法兰', 'SpeakerVisualCone': '侧圆环内凹盆体示意',
    'SpeakerSurround': '侧扬声器悬边示意', 'SpeakerCentre': '侧扬声器中心盖',
    'SpeakerBolt': '侧音箱固定螺钉示意', 'WingEdge': '翼板金属包边',
    'WingRaisedFace': '翼板曲线抬高面',
    'WingPaint': '翼板彩色面板', 'WingStripe': '翼板斜向色条',
    'WingHubMark': '翼板圆心标记', 'HandleArm': '提手侧支臂',
    'HandlePivot': '提手连接螺钉示意',
    'VisibleWire': '侧面彩色线束示意',
    'HandleGrip': '提手握把', 'GripBand': '握把包覆带', 'TopSlotTrim': '顶部进碟口饰框',
    'TopInstrumentPanel': '顶部仪表装饰面板', 'TopMeterLatch': '顶部仪表红色拨片',
    'TopMeter': '顶部仪表刻线', 'RearCoolingFin': '后部散热鳍片示意',
    'RearCoolingCore': '后部鳍片内层暗色基座',
    'RearCyanUpperLeft': '后凹舱左上灯角',
    'RearCyanLowerRight': '后凹舱右下灯角',
    'RearCyanLowerLeft': '后凹舱左下灯角',
    'RearCavityEmitterLeft': '左后凹舱圆头灯条',
    'RearCavityReflectorLeft': '左后凹舱金属反射背板',
    'RearCavityClipUpperLeft': '左后凹舱上灯条压座',
    'RearCavityClipLowerLeft': '左后凹舱下灯条压座',
    'RearCavityEmitterRight': '右后凹舱圆头灯条',
    'RearCavityReflectorRight': '右后凹舱金属反射背板',
    'RearCavityClipUpperRight': '右后凹舱上灯条压座',
    'RearCavityClipLowerRight': '右后凹舱下灯条压座',
    'RearCyanFrame': '后部青色灯框', 'RearRecessLiner': '后部内嵌封板',
    'RearPortRail': '后部接口凹面板', 'RearRedInsert': '后部阶梯红色滑条',
    'RearRailCarrier': '后部圆角接口承接面', 'RearRailAntennaSlot': '天线两侧凹槽衬片',
    'RearRailStatusIndex': '后部状态灯白色定位条',
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
    'LowerPodEdgeRail': '底部小喷口叶片圆边压条',
    'HoodShoulderPlate': '前罩侧肩叠层甲片', 'HoodShoulderBolt': '前罩侧肩沉槽螺钉',
    'HoodTopInset': '前罩顶面凹槽衬片', 'HoodTopRib': '前罩顶面桥形筋',
    'ControlRailLip': '控制条阶梯压边', 'ControlRailEnd': '控制条端部护块',
    'ControlEndBolt': '控制条端部螺钉', 'KnobFace': '旋钮内凹端面',
    'SideFrameBolt': '侧装甲连接螺钉', 'SideFrameShoe': '侧装甲分段护脚',
    'SpeakerHubNeck': '侧圆环前伸翼根轴颈', 'SpeakerLipTrim': '侧圆环细压边',
    'SpeakerScallopCollar': '侧圆环分瓣过渡环', 'SpeakerRetainer': '侧圆环独立扣片',
    'SpeakerBridgeWire': '侧圆环分瓣间红色连接线示意',
    'WingSpine': '翼板折面纵脊', 'WingHubSeat': '翼板阶梯转接盘',
    'WingHubBolt': '翼板转接盘螺钉', 'HandleWasher': '提手转轴肩环',
    'HandleGripCuff': '提手握把端箍', 'HandleMark': '提手嵌面斜向标记',
    'RoofAccessPanel': '顶部阶梯检修甲板', 'RoofAccessBolt': '顶部检修甲板螺钉',
    'RoofRaisedRib': '顶部折面加强筋', 'InstrumentRim': '仪表斜面金属压框', 'InstrumentMount': '仪表阶梯嵌框',
    'RearArmourCheek': '后部圆角护甲', 'RearArmourBolt': '后部护甲连接螺钉',
    'RearLinerRib': '后部凹舱加强筋', 'RearRailBezel': '后部滑条嵌框',
    'RearRailVent': '后部竖槽底衬', 'RearRailLatch': '后部接口条锁片',
    'RearBeaconLens': '后部指示灯端透镜',
    'NozzleRootClamp': '低音喷口根部夹块', 'NozzlePetalHinge': '低音喷口叶片根铰示意',
    'NozzlePetalFastener': '低音喷口叶片铆钉示意',
    'LowerPodClamp': '底部小喷口根箍', 'BellyServicePlate': '底部独立检修甲板',
    'BellyServiceBolt': '底部检修甲板螺钉',
    'Parameters': '尺寸参数与依据', 'ConceptStatus': '设计状态与假设说明',
    'FrontCheek': '屏幕侧立体护壳', 'CheekDial': '侧面方向控制盘示意',
    'CheekButton': '方向盘红色按键示意', 'CheekArrow': '方向盘三角指示',
    'CheekKnob': '侧面锥形旋钮示意', 'VentBacking': '侧面格栅黑色衬板',
    'CheekVentRib': '侧面格栅独立横肋', 'CheekPerforatedPanel': '侧面穿孔下护板',
    'UtilityBarrel': '外挂筒金属穿孔外罩', 'UtilityLiner': '外挂筒深色内衬',
    'UtilityCollar': '外挂筒环形端箍', 'UtilityCap': '外挂筒圆顶端盖',
    'UtilityMount': '外挂筒连接座示意', 'UtilityIndicator': '外挂筒红色环形指示灯',
    'UtilityControl': '外挂筒上部控制盒示意', 'UtilitySwitch': '外挂筒拨钮示意',
    'UtilityLED': '外挂筒青色指示灯', 'SideCable': '外挂筒螺旋线缆示意',
    'UtilityCableBoot': '外挂筒卷线护套示意', 'SideCableTopBoot': '侧面卷线连接护套示意',
    'UtilityCapRib': '外挂筒端盖分瓣棱线', 'UtilityFrontLens': '外挂筒中心指示透镜',
    'UtilityControlInset': '外挂筒控制面板内衬',
    'UtilitySwitchRed': '外挂筒红色电源按钮示意',
    'SideFrontSpine': '侧前部开槽金属护板',
    'SideFrontSpineLiner': '侧前部护板槽底衬片',
    'CheekUtilityLabel': '侧面通用系统铭牌底片',
    'CheekUtilityRedBand': '侧面铭牌红色侧条',
    'NozzlePetalEdgeRail': '喷口叶片圆边压条',
    'NozzlePetalInset': '喷口叶片凹槽衬片',
    'NozzlePetalGuide': '喷口叶片凹槽导轨', 'NozzlePetalEndHem': '喷口叶片末端折边',
    'BassNozzleRolledLip': '喷口金色卷边',
    'BassInnerThroat': '喷口内侧连续深色衬筒',
    'BassWarningRedBand': '喷口标牌红色侧条',
    'BassSideStripe': '喷口两侧薄涂装条纹',
    'RearRailIndex': '后部滑条白色定位标记',
    'RearRailStatusBase': '后部状态灯底座',
    'RearRailStatusLens': '后部状态灯透镜',
    'RearRecessWire': '后部凹舱弧形线束',
    'RearRecessCornerBoss': '后部灯框角部压座',
    'RearLowerSlope': '后壳下部斜向收口封板',
    'SideSocketBase': '侧面圆形接口底座示意', 'SideSocketLip': '侧面圆形接口口沿',
    'SideSocketRecess': '侧面圆形接口内凹封片', 'SideStatusPlate': '侧面接口标记板示意',
    'SideStatusBracket': '侧面接口连线标记', 'SideStatusSlot': '侧面下部窄槽边框',
    'SideStatusMark': '侧面矩形接口标记示意', 'UnderbodyHarness': '底部多芯线束外观示意',
    'TopMeterGrid': '顶部仪表纵向网格', 'TopMeterRule': '顶部仪表横向网格',
    'TopMeterTrace': '顶部仪表波形曲线', 'TopMeterTick': '顶部仪表刻度',
    'FrontCheekBridge': '屏框侧面后衬连接板',
    'WingFoldFacet': '翼板后缘斜折面', 'HoodShoulderSlotLiner': '前罩侧肩滑槽内衬',
    'HoodShoulderCrown': '前罩侧肩弧面内罩',
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


def perforated_side_flange(side, cy, cz, radial_scale):
    """Two curved skins with staggered open holes, inferred from images 03/05.

    Hole pitch, split angles and section depth are appearance assumptions;
    the previously fitted outer lip and wing attachment remain separate.
    """
    outer_profile=[(63,106),(63,108),(61,111),(57,114),(53,114.5),(50,112)]
    inner_profile=[(50,110),(53,112.5),(57,112),(60,109),(61,107),(61,106)]
    def curve(points):
        c=Part.BSplineCurve()
        c.interpolate([App.Vector(r*radial_scale,0,x) for r,x in points])
        return c.toShape()
    outer,inner=curve(outer_profile),curve(inner_profile)
    section=Part.Wire([outer,Part.makeLine(outer.Vertexes[-1].Point,inner.Vertexes[0].Point),
                      inner,Part.makeLine(inner.Vertexes[-1].Point,outer.Vertexes[0].Point)])
    flange=Part.Face(section).revolve(App.Vector(),App.Vector(0,0,1),360)
    flange.Placement=App.Placement(App.Vector(0,cy,cz),App.Rotation(App.Vector(0,0,1),App.Vector(side,0,0)))
    gaps=[]
    for degrees in (0,180):
        a,b=(math.radians(degrees+d) for d in (-12,12))
        gaps.append(profile([(cy,cz),(cy+80*math.cos(a),cz+80*math.sin(a)),
                             (cy+80*math.cos(b),cz+80*math.sin(b))],
                            'YZ',(side*95,0,0),side*30))
    flange=flange.cut(Part.makeCompound(gaps))
    # Roll the exposed plate edges before drilling, including the split ends.
    flange=flange.makeFillet(.35,flange.Edges)
    holes=[]
    for offset in (0,180):
        for radius,first,count in ((55.8,16,9),(60.3,25.25,8)):
            for j in range(count):
                angle=math.radians(offset+first+j*18.5)
                y,z=cy+radius*math.cos(angle),cz+radius*math.sin(angle)
                holes.append(cylinder(1.7,24,(side*96,y,z),(side,0,0)))
                # A shallow flared mouth gives each hole a physical edge.
                outer_x=114.56 if radius<58 else 111.47
                holes.append(Part.makeCone(2.1,1.7,.7,App.Vector(side*(outer_x+.15),y,z),App.Vector(-side,0,0)))
    flange=flange.cut(Part.makeCompound(holes))
    wires=[]
    for offset in (0,180):
        points=[App.Vector(side*109.5,cy+60.3*math.cos(math.radians(offset+a)),
                           cz+60.3*math.sin(math.radians(offset+a))) for a in (-15,0,15)]
        arc=Part.Arc(*points).toShape();path=Part.Wire([arc])
        cross=Part.Wire([Part.makeCircle(.8,points[0],arc.tangentAt(arc.FirstParameter))])
        wires.append(path.makePipeShell([cross],True,False))
    return flange,wires


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


def contract_nozzle_radial(shape, factor=NOZZLE_RADIAL_SCALE, preserve_root=False):
    """Contract a nozzle-local solid in X/Y while preserving its axial Z.

    The nozzle parts are created in a local frame and placed only at the final
    assembly step.  Keep the placement attached to the shape while applying a
    native BRep transform so the rear cavity shadow remains a separate shell.
    """
    if abs(factor - 1.0) < 1e-12:
        return shape
    placement = shape.Placement
    local = shape.copy()
    local.Placement = App.Placement()
    root_piece = None
    if preserve_root:
        # Keep the fitted root station embedded in the mouth ring.  The
        # contract is applied only beyond this short attachment band.
        root_band = Part.makeBox(200, 200, 8, App.Vector(-100, -100, 94))
        root_piece = local.common(root_band)
    matrix = App.Matrix()
    matrix.A11 = factor
    matrix.A22 = factor
    matrix.A33 = 1.0
    local = local.transformShape(matrix)
    if root_piece is not None and not root_piece.isNull():
        local = local.fuse(root_piece).removeSplitter()
    if local.isNull() or not local.isValid() or not local.Solids:
        raise ValueError('Invalid contracted nozzle solid')
    local.Placement = placement
    return local


def contract_nozzle_petal_tangential(shape, index,
                                     factor=NOZZLE_PETAL_TANGENTIAL_SCALE,
                                     preserve_root=False):
    """Narrow one petal in its local tangential direction.

    The rear reference shows a slightly narrower repeated petal span than the
    earlier fit.  The transform is applied in the saved nozzle frame, so the
    axial station and the four added supports remain unchanged.  The lower
    root band is retained as a real BRep piece to keep its existing overlap
    with the mouth assembly.
    """
    if abs(factor - 1.0) < 1e-12:
        return shape
    placement = shape.Placement
    local = shape.copy()
    local.Placement = App.Placement()
    theta = math.radians(index * 30 + 15)
    radial = App.Vector(math.cos(theta), math.sin(theta), 0)
    tangent = App.Vector(-math.sin(theta), math.cos(theta), 0)
    matrix = App.Matrix()
    matrix.A11 = radial.x * radial.x + factor * tangent.x * tangent.x
    matrix.A12 = radial.x * radial.y + factor * tangent.x * tangent.y
    matrix.A21 = radial.y * radial.x + factor * tangent.y * tangent.x
    matrix.A22 = radial.y * radial.y + factor * tangent.y * tangent.y
    matrix.A33 = 1.0
    if preserve_root:
        root_band = Part.makeBox(200, 200, 8, App.Vector(-100, -100, 94))
        root = local.common(root_band)
        upper = local.cut(root_band)
        local = upper.transformShape(matrix)
        if not root.isNull() and not local.isNull():
            local = local.fuse(root).removeSplitter()
    else:
        local = local.transformShape(matrix)
    if local.isNull() or not local.isValid() or not local.Solids:
        raise ValueError('Invalid tangentially contracted nozzle petal')
    local.Placement = placement
    return local


def curved_wing_plate(points, x, thickness, rim_width=0):
    """Interpolate the observed wing edge, keeping its pointed upper closure.

    The two curves share a tangent at the rounded root. The upper trailing
    segment stays straight so the reference's pointed tip is not rounded off.
    """
    cy=sum(p[0] for p in points)/len(points)
    cz=sum(p[1] for p in points)/len(points)
    def section(depth,scale=1):
        pts=[App.Vector(x+depth,cy+(y-cy)*scale,cz+(z-cz)*scale) for y,z in points]
        tangent=pts[14]-pts[12]
        tangent.normalize()
        front=Part.BSplineCurve()
        front.interpolate(pts[:14],InitialTangent=pts[1]-pts[0],FinalTangent=tangent)
        rear=Part.BSplineCurve()
        rear.interpolate(pts[13:],InitialTangent=tangent,FinalTangent=pts[-1]-pts[-2])
        return Part.Wire([front.toShape(),rear.toShape(),Part.makeLine(pts[-1],pts[0])])
    if rim_width:
        span=min(max(p[i] for p in points)-min(p[i] for p in points) for i in (0,1))
        inset=1-2*rim_width/span
        return Part.makeLoft([section(0,inset),section(thickness*.25),
                              section(thickness*.7),section(thickness,inset)],True,True)
    return Part.Face(section(0)).extrude(App.Vector(thickness,0,0))


def rounded_plate(w, h, depth, pos, radius, plane='XZ'):
    """Rounded silhouette independent of plate thickness."""
    if plane == 'XZ':
        shape = box(w, depth, h, pos)
        edges = [e for e in shape.Edges if e.BoundBox.YLength > depth-.01]
    else:
        shape = box(depth, w, h, pos)
        edges = [e for e in shape.Edges if e.BoundBox.XLength > depth-.01]
    return shape.makeFillet(radius, edges)


def brow_u(width, top, radius, border, bottom, front, depth):
    """Constant-thickness U section with concentric front corner arcs."""
    half = width/2
    inner = half-border
    r = radius-border
    cx,cz = half-radius,top-radius
    v = lambda x,z: App.Vector(x,front,z)
    q = math.sqrt(.5)
    edges = [Part.makeLine(v(-half,bottom),v(-half,cz)),
             Part.Arc(v(-half,cz),v(-cx-radius*q,cz+radius*q),v(-cx,top)).toShape(),
             Part.makeLine(v(-cx,top),v(cx,top)),
             Part.Arc(v(cx,top),v(cx+radius*q,cz+radius*q),v(half,cz)).toShape(),
             Part.makeLine(v(half,cz),v(half,bottom)),
             Part.makeLine(v(half,bottom),v(inner,bottom)),
             Part.makeLine(v(inner,bottom),v(inner,cz)),
             Part.Arc(v(inner,cz),v(cx+r*q,cz+r*q),v(cx,top-border)).toShape(),
             Part.makeLine(v(cx,top-border),v(-cx,top-border)),
             Part.Arc(v(-cx,top-border),v(-cx-r*q,cz+r*q),v(-inner,cz)).toShape(),
             Part.makeLine(v(-inner,cz),v(-inner,bottom)),
             Part.makeLine(v(-inner,bottom),v(-half,bottom))]
    return Part.Face(Part.Wire(edges)).extrude(App.Vector(0,depth,0))


def cooling_fin(x, width=8.3, inset=False):
    """Rounded bent section with a broad rear quarter-circle, not a chamfer."""
    def v(y,z):
        return App.Vector(x,177.5+(y-177.5)*(.91 if inset else 1),
                          256+(z-256)*(.94 if inset else 1))
    edges = [Part.makeLine(v(160,256),v(160,276)),
             Part.Arc(v(160,276),v(162.929,283.071),v(170,286)).toShape(),
             Part.makeLine(v(170,286),v(177.5,286)),
             Part.Arc(v(177.5,286),v(189.874,280.874),v(195,268.5)).toShape(),
             Part.makeLine(v(195,268.5),v(195,256)),
             Part.makeLine(v(195,256),v(160,256))]
    shape = Part.Face(Part.Wire(edges)).extrude(App.Vector(width,0,0))
    return shape.makeFillet(.65,[e for e in shape.Edges if e.BoundBox.XLength < .01])


def grip_wrap(index):
    """Thin overlapping cloth-like bands with small, real ruled-surface folds.

    The wrinkles are an appearance interpretation, not recovered cloth topology.
    """
    x0 = -93+index*18.6
    def section(x, radius, phase=0, fold=0):
        pts = []
        for cy,cz,start in ((7.5,5.5,0),(-7.5,5.5,90),(-7.5,-5.5,180),(7.5,-5.5,270)):
            for j in range(7):
                a = math.radians(start+j*15)
                r = radius+fold*(.55+.45*math.sin(3*a+phase))
                dy,dz = cy+r*math.cos(a),cz+r*math.sin(a)
                pts.append(App.Vector(x+dz*.5,122.5+dy,318.5+dz))
        curve = Part.BSplineCurve()
        curve.interpolate(pts,PeriodicFlag=True)
        return Part.Wire(curve.toShape())
    folds = ((0,12.1),(.08,11.6),(.29,11.7),(.33,12.1),
             (.38,11.65),(.64,11.7),(.70,12.0),(1,11.6))
    outer = Part.makeLoft([section(x0+t*19,radius,index*.79+t*2.3,
                                  .1 if t in (0,1) else .55+.2*math.sin(index+t*6))
                           for t,radius in folds],True,True)
    inner = Part.makeLoft([section(x0-.1,10.8),section(x0+19.1,10.8)],True,True)
    # Straight outer tape ends match the exposed metal at both grip tips.
    return outer.cut(inner).common(box(183,100,100,(-91.5,80,270)))


def handle_arm_wire(x, scale=1):
    """Source side-plane outline with rounded lower end and bent upper shoulder."""
    yz=[(176.822,318.3052),(199.5662,293.2397),(121.299,229.0651),
        (105.1397,224.0566),(91.947,234.3304),(90.5639,243.5156),
        (96.5909,254.6559),(166.0663,313.4387),(171.2209,316.5395)]
    pts=[App.Vector(x,145+(y-145)*scale,273+(z-273)*scale) for y,z in yz]
    edges=[Part.makeLine(pts[0],pts[1]),Part.makeLine(pts[1],pts[2]),
           Part.Arc(pts[2],pts[3],pts[4]).toShape(),
           Part.Arc(pts[4],pts[5],pts[6]).toShape(),Part.makeLine(pts[6],pts[7]),
           Part.Arc(pts[7],pts[8],pts[0]).toShape()]
    return Part.Wire(edges)


def source_roof_shell():
    """Rounded transverse shoulders and a raised, descending longitudinal crown."""
    stations=[(0,233),(15,235),(30,240.5),(40,247.2),(56.6,259.4),
              (70,267),(85,269),(106,269),(160,269),(178,266),
              (195,258),(210,250),(220,246)]
    def section(y,top,half,radius,bottom):
        def v(x,z):return App.Vector(x,y,z)
        k=radius*(1-1/math.sqrt(2))
        points=[v(-half,bottom),v(half,bottom),v(half,top-radius),
                v(half-radius,top),v(-half+radius,top),v(-half,top-radius)]
        return Part.Wire([Part.makeLine(points[0],points[1]),Part.makeLine(points[1],points[2]),
            Part.Arc(points[2],v(half-k,top-k),points[3]).toShape(),Part.makeLine(points[3],points[4]),
            Part.Arc(points[4],v(-half+k,top-k),points[5]).toShape(),Part.makeLine(points[5],points[0])])
    fitted=[]
    for y,z in stations:
        z+=-.92008537*min(y/85,1,(220-y)/35)+3*math.exp(-((y-45)/30)**2)
        r=min(8+(25.35454089-8)*min(max((y-45)/40,0),1,max((220-y)/30,0)),z-220-.1)
        fitted.append((y,z,r))
    outer=Part.makeLoft([section(y,z,100.8,r,220) for y,z,r in fitted],True,False)
    inner=Part.makeLoft([section(y,z-3.3,97.5,r-3.3,218) for y,z,r in fitted],True,False)
    shell=outer.cut(inner)
    # Raised inspection panel bridges a shallow recess in the crown.
    shell=shell.cut(box(130,74,22,(-65,110,260)))
    shell=shell.cut(box(104.16,5,35,(-52.08,77.5,250)))
    # Seat the fitted instrument: its frame bridges the cut edge of the shell.
    aperture=box(159,22,30,(-79.5,-11,-10))
    aperture.rotate(App.Vector(),App.Vector(1,0,0),36.61287666)
    aperture.translate(App.Vector(0,48.33972247,252.35745666))
    shell=shell.cut(aperture)
    with tempfile.TemporaryDirectory(prefix='vintrox-roof-') as folder:
        transfer=str(Path(folder)/'roof.step');shell.exportStep(transfer);shell=Part.read(transfer)
    return shell


def rounded_frame(w, h, depth, border, pos, radius=8):
    x, y, z = pos
    outer = box(w, depth, h, pos)
    edges = [e for e in outer.Edges if e.BoundBox.YLength > depth - .01]
    outer = outer.makeFillet(radius, edges)
    inner = box(w-2*border, depth+2, h-2*border, (x+border, y-1, z+border))
    edges = [e for e in inner.Edges if e.BoundBox.YLength > depth+1.99]
    inner = inner.makeFillet(max(1, radius-border/2), edges)
    return outer.cut(inner)


def side_cable_path():
    """A single 3D cable, with inferred tangent-continuous leads at both ends."""
    p=[-121.00000000187981, 173.79269486001738, 84.82931073498351, -133.50657953286992, 218.23074353191194, 81.65417175464393, -132.00172843718698, 222.4660707646565, 117.46278432869852, -111.13982088555066, 219.5257822691553, 150.77734340659532, 10.926059339297653, 10.152886471235576, 9.357483800355128, 2.3737150087984507, 5.380288823039622, 2.4238393805741754, 0.021353030178268673, -0.9255208806863461, 1.0797281798247538]
    control=[App.Vector(*p[i:i+3]) for i in range(0,12,3)]
    normals=[App.Vector(math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el))
             for az,el in ((p[17],p[18]),(p[19],p[20]))]
    points=[]
    for i in range(361):
        t=i/360
        center=control[0]*(1-t)**3+control[1]*(3*t*(1-t)**2)+control[2]*(3*t*t*(1-t))+control[3]*t**3
        normal=normals[0]*(1-t)+normals[1]*t;normal.normalize()
        u=App.Vector(1,0,0);u-=normal*u.dot(normal);u.normalize();v=normal.cross(u)
        radius=(1-t)**2*p[12]+2*t*(1-t)*p[13]+t*t*p[14]
        angle=p[15]+t*math.tau*p[16]
        points.append(center+(u*math.cos(angle)+v*math.sin(angle))*radius)
    def bezier(controls,count):
        return [controls[0]*(1-t)**3+controls[1]*(3*t*(1-t)**2)+controls[2]*(3*t*t*(1-t))+controls[3]*t**3
                for t in [i/count for i in range(count+1)]]
    # Replace only the terminal fractions of the fitted coil with broader
    # leads; tighter cubic handles produced local radii below the wire radius.
    first=points[8]-points[6];first.normalize()
    last=points[-9]-points[-11];last.normalize()
    points=points[7:-9]
    bottom=App.Vector(-132,155.5,77);top=App.Vector(-114.5,200,179)
    lead_in=bezier([bottom,bottom+App.Vector(0,5,0),points[0]-first*7,points[0]],30)
    lead_out=bezier([points[-1],points[-1]+last*15,top-App.Vector(17,0,0),top],60)
    return [tuple(p) for p in lead_in[:-1]+points+lead_out[1:]]


def side_cable_solid():
    """Sweep C2 cubic spans separately to avoid a C0 monolithic pipe face."""
    points=[vector(p) for p in side_cable_path()]
    curve=Part.BSplineCurve()
    curve.approximate(Points=points,DegMin=3,DegMax=3,Tolerance=.01,
                      Continuity='C2',ParamType='ChordLength')
    knots=curve.getKnots();edges=[]
    for start,end in zip(knots[:-1],knots[1:]):
        span=curve.copy();span.segment(start,end);edges.append(span.toShape())
    path=Part.Wire(edges)
    section=Part.Wire([Part.makeCircle(1.8,curve.value(curve.FirstParameter),curve.tangent(curve.FirstParameter)[0])])
    shape=path.makePipeShell([section],True,False)
    shape.check(True)
    return shape


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


def nozzle_lip_parts():
    """Root rolls reconstructed from five fixed reference-video views."""
    return {name: shape for name, shape in root_shifted_rolls().items()
            if name in ('BassNozzleRolledLip', 'BassNozzleMouthRing', 'BassSpeakerGasket')}


def nozzle_fairing_parts():
    """Blend the fixed body attachment into the fitted root; retain real wall thickness."""
    return blended_fairing_parts(blend_power=4, depth_extra=4, shoulder_inset=6, lower_inset=0, marking_spec=MARKING_SPEC)


def crowned_plate(points, plane, origin, thickness, rim=2):
    """Closed faceted armour: broad bevel shoulders and a raised centre face.

    Unlike a constant extrusion, the two inset faces expose a real sloped rim
    in saved BRep/STEP, including when no render bevel modifier is present.
    """
    u = sum(p[0] for p in points)/len(points)
    v = sum(p[1] for p in points)/len(points)
    span = min(max(p[i] for p in points)-min(p[i] for p in points) for i in (0, 1))
    scale = 1-2*rim/span
    wires = []
    for depth, factor in ((0, scale), (thickness*.25, 1), (thickness*.65, 1), (thickness, scale)):
        pts = [(u+(a-u)*factor, v+(c-v)*factor) for a,c in points]
        verts = [App.Vector(depth, a, c) if plane == 'YZ' else App.Vector(a, depth, c)
                 for a,c in pts]
        wires.append(Part.makePolygon(verts+[verts[0]]))
    result = Part.makeLoft(wires, True, True)
    result.translate(vector(origin))
    return result


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


def nozzle_leaf_parts(i, phase=15, stepped=True, pitch=30):
    """Round-edged leaves with a stepped strap; count/pitch inferred from views."""
    if stepped and phase == 15 and pitch == 30:
        return root_shifted_leaf_parts(i)
    a=i*pitch+phase
    angular_scale=pitch/22.5
    sections=[(96.8067,52.3215,-1.149,0),(108,49.4,.7,-1.5),
              (120,46,2.8,-3),(128.43,43.6,4.28,-4.2)]
    def section(ro,ri,z,dy,tilt,start,stop):
        w=sector_wire(ro,ri,z,start,stop)
        w.rotate(App.Vector(0,0,z),App.Vector(1,0,0),tilt)
        w.translate(App.Vector(0,dy,0))
        return w
    def skin(outer,inner,start,stop,stations=sections):
        return Part.makeLoft([section(r+outer,r+inner,z,dy,t,a+start*angular_scale,a+stop*angular_scale)
                             for z,r,dy,t in stations],True,True)
    petal=skin(0,-2,1.2,21.3)
    # Round the four radial section edges: visible sheet corners, not an
    # arbitrary render bevel. Keep most of the fitted terminal circular arc.
    end_normal=App.Vector(0,-math.sin(math.radians(-4.2)),math.cos(math.radians(-4.2)))
    radial=[e for e in petal.Edges if abs(e.Length-2)<1e-5 and (
        abs(e.CenterOfMass.z-96.8067)<1e-5 or
        abs(end_normal.dot(e.CenterOfMass-App.Vector(0,4.28,128.43)))<1e-5)]
    if len(radial)!=4:raise ValueError('Expected four radial petal corner edges')
    petal=petal.makeFillet(.85,radial)
    # Round tapered cutters before trimming the curved sheet surfaces.
    def window(start,stop,z0,z1,radius):
        theta=math.radians(a+11.25*angular_scale)
        tangent=App.Vector(math.sin(theta),-math.cos(theta),0)
        def point(z,angle):
            lo,hi=next((l,h) for l,h in zip(sections,sections[1:]) if l[0]<=z<=h[0])
            f=(z-lo[0])/(hi[0]-lo[0]);r,dy,tilt=[lo[j]+f*(hi[j]-lo[j]) for j in [1,2,3]]
            t=math.radians(a+angle*angular_scale);q=App.Vector(r*math.cos(t),dy+r*math.sin(t)*math.cos(math.radians(tilt)),z+r*math.sin(t)*math.sin(math.radians(tilt)))
            return (tangent.dot(q),q.z)
        pts=[point(z0,start),point(z0,stop),point(z1,stop),point(z1,start)]
        tool=profile(pts,'XZ',(0,-80,0),160)
        axial=[e for e in tool.Edges if abs(e.Length-160)<1e-6]
        assert len(axial)==4
        tool=tool.makeFillet(radius,axial)
        tool.rotate(App.Vector(),App.Vector(0,0,1),math.degrees(theta)-90)
        return tool
    recess=skin(1,-.8,0,22.5).common(window(2.7,19.8,99.5,127,1.0))
    inset=skin(-.65,-.95,0,22.5).common(window(3.1,19.4,99.8,126.7,.8))
    parts={f'NozzlePetal{i}':petal.cut(recess),f'NozzlePetalInset{i}':inset}
    guides=[(100,51.49,-.62,-.43),(108,49.4,.7,-1.5),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
    if stepped:
        # A raised upper strap ends halfway down the leaf; the narrower
        # recessed guide continues below it, as seen in the rear close-ups.
        upper=[(98,52.05,-.98,-.15),(108,49.4,.7,-1.5),(111.6,48.38,1.33,-1.95)]
        lower=[(111.4,48.44,1.295,-1.925),(120,46,2.8,-3),(123.5,45,3.41,-3.5)]
        parts[f'NozzlePetalRidge{i}']=skin(.7,-1.1,9.5,13.0,upper).fuse(skin(-.2,-1.1,9.8,12.7,lower)).removeSplitter()
        guides=lower
    else:
        parts[f'NozzlePetalRidge{i}']=skin(-.2,-1.1,9.8,12.7,guides)
    for edge_index,edge_offset in enumerate((1.7,20.8)):
        edge=a+edge_offset*angular_scale
        t=math.radians(edge)
        # Stop before the rounded corners rather than overhanging their ends.
        stations=[(98,52.05,-.98,-.15),*sections[1:-1],(127.3,43.92,4.08,-4.04)]
        points=[((r+.05)*math.cos(t),dy+(r+.05)*math.sin(t)*math.cos(math.radians(tilt)),
                 z+(r+.05)*math.sin(t)*math.sin(math.radians(tilt))) for z,r,dy,tilt in stations]
        parts[f'NozzlePetalEdgeRail{i}_{int(i*22.5+(1.7,20.8)[edge_index])}']=tube(points,.28)
    for j,ang in enumerate((a+10.1*angular_scale,a+12.4*angular_scale)):
        t=math.radians(ang)
        points=[((r-.12)*math.cos(t),dy+(r-.12)*math.sin(t)*math.cos(math.radians(tilt)),
                 z+(r-.12)*math.sin(t)*math.sin(math.radians(tilt))) for z,r,dy,tilt in guides]
        parts[f'NozzlePetalGuide{i}_{j}']=tube(points,.28)
    parts[f'NozzlePetalEndHem{i}']=skin(.1,-.4,2.6,19.9,[(127.7,43.81,4.15,-4.1),(128.43,43.6,4.28,-4.2)])
    if stepped and phase==15 and pitch==30:
        parts.update(petal_surface_parts(i))
    return parts


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
        view=getattr(obj,'ViewObject',None)
        if view is not None:
            view.ShapeColor = color
            view.LineColor = tuple(v*.45 for v in color)
            view.DisplayMode = 'Flat Lines'
            view.LineWidth = .6
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


def refine_reference_proportions(study):
    """First screen-anchored 360-degree proportion pass, applied to real BReps.

    The screen and four-support assembly retain their measured/declared geometry.
    These transforms are model dimensions, never image registration or warping.
    """
    for obj in study.items:
        name = obj.Name
        sx, sy, sz, dz, dy = 1, 1, 1, 0, 0
        if name.startswith(('SlopedUpper','RoofSideClosure','TopInstrument','Instrument','TopMeter',
                            'RearPort','RearRail','RearRed','RearBeacon')):
            # Rounded roof and fitted instrument are authored in world coordinates.
            continue
        if name.startswith(('MainEnclosure', 'RearUpper',
                            'BottomChassis', 'ClosedBellyPan', 'RearService', 'RearStructural', 'SideClosure',
                            'SideMechanical', 'SideGuard', 'SideFrame', 'VisibleWire')):
            sx, sy, sz, dz = .84, 1.25, .84, 24
        elif name.startswith(('Speaker', 'PerforatedSpeaker')):
            # Source-fitted side rings are authored in world coordinates.
            continue
        elif name.startswith('Wing'):
            # Tip triangulation: |X|133.4,Y266.6,Z360.3; hub fit near
            # |X|142,Y126,Z151. Top inclines slightly inward in the source.
            sx, sy, sz, dy, dz = .817, 1.12, 1.01, 33, -8.8
        elif name.startswith(('HandleArm','HandleInset','HandleMark','HandleGripCuff')):
            # Source-fitted side plates and end collars use world coordinates.
            continue
        elif name.startswith(('Handle', 'GripBand')):
            sx, sy, dz = 1.04, 1.2, -17
            dy = 25
        elif name.startswith(('Top', 'Instrument', 'RoofAccess', 'RoofRaised', 'RearCooling', 'RearBeacon', 'Antenna')):
            sx, sy, dz = .84, 1.25, -20
            if name.startswith('RoofAccess'):dz=-10
            elif name.startswith('RoofRaised'):dz=-8
            elif name.startswith('TopSlot'):dz=-7
        elif name.startswith(('ProjectingBrow', 'BrowUnderside', 'Hood')):
            dz = -11
            dy = -18
        elif name.startswith(('ControlRailEnd','ControlEndBolt')):
            sx,dy,dz = .91,12.88,5.12
        elif name.startswith(('Control', 'RedKey', 'Key', 'Knob', 'StatusKey')):
            # Three-view fitted front controls use world coordinates.
            continue
        elif name.startswith(('RearArmour', 'RearLiner')):
            sx, sy, sz, dz = .84, 1.25, .84, 24
        elif name.startswith(('RearPort', 'RearRail', 'RearRed')):
            sx, sy, dz = .56, 1.25, -30
        elif name.startswith(('RearCyan', 'RearRecess')):
            sy, dz = 1.25, 10
        elif name.startswith('UnderbodyLoop'):
            # Current loop paths are authored directly in world coordinates.
            sy = 1
        elif name.startswith(('Bass', 'Nozzle', 'Woofer')):
            dy, dz = 12, 15
        elif name.startswith('LowerPod'):
            # World-space mirrored circles fitted to four video views; retain
            # circular sections instead of the old nonuniform Z compression.
            pass
        elif name.startswith('BellyService'):
            sx, dz = .84, 24
        else:
            continue
        matrix = App.Matrix()
        matrix.A11, matrix.A22, matrix.A33, matrix.A34 = sx, sy, sz, dz
        matrix.A24 = dy
        if name.startswith(('ProjectingBrow', 'BrowUnderside', 'Hood')):
            matrix.A23 = -.4
            matrix.A24 += .4*263
        if name.startswith('Wing'):
            side = -1 if 'Left' in name else 1
            matrix.A13, matrix.A14 = -side*.04, side*6
        if name.startswith(('HoodShoulderCrown','HoodMark')):
            # FreeCAD sanitizes signed identifiers; use saved geometry's side.
            side = -1 if obj.Shape.Solids[0].CenterOfMass.x < 0 else 1
            matrix.A13 = -side*.39
            matrix.A14 = side*.39*226
        if (sx, sy, sz) == (1, 1, 1) and matrix.A23 == 0:
            shape = obj.Shape.copy()
            shape.translate(App.Vector(0, dy, dz))
        else:
            shape = obj.Shape.transformGeometry(matrix)
            # OCCT's affine B-splines may integrate differently before STEP
            # transfer. Normalize their parameterization once, then verify the
            # final saved BRep against an independently read final STEP.
            with tempfile.TemporaryDirectory(prefix='vintrox-affine-') as folder:
                transfer = str(Path(folder)/'component.step')
                shape.exportStep(transfer)
                shape = Part.read(transfer)
        if not shape.isValid() or not shape.Solids:
            raise ValueError('Invalid proportion adjustment: '+name)
        obj.Shape = shape


def add_reference_side_modules(study):
    """Restore reference-visible assemblies under the user's latest direction."""
    for side, suffix in ((-1, 'Left'), (1, 'Right')):
        # The broad front cheeks continue from the visor down beside the bezel.
        cheek = rounded_plate(39, 141, 8, (side*116, -2, 64), 7, 'YZ')
        if side < 0:
            cheek.translate(App.Vector(-8, 0, 0))
        study.add('FrontCheek'+suffix, cheek, GOLD, 'Sides')
        study.add('CheekUtilityLabel'+suffix,rounded_plate(31,18,.35,
                  (side*124.8 if side>0 else -125.15,2,66),1,'YZ'),WHITE,'Details')
        study.add('CheekUtilityRedBand'+suffix,rounded_plate(4.5,17,.15,
                  (125.15 if side>0 else -125.3,2.5 if side>0 else 27.5,66.5),.7,'YZ'),RED,'Details')
        study.add('FrontCheekBridge'+suffix,box(12,16,141,(106 if side>0 else -118,22,64),1),
                  DARK,'Sides','rubber')
        x = side*124.5
        direction = (side, 0, 0)
        study.add('VentBacking'+suffix, box(2, 33, 49, (x if side>0 else x-2, 1, 89)), DARK, 'Sides')
        for i in range(10):
            study.add(f'CheekVentRib{suffix}{i}', box(2.8, 32, 1.6, (x if side>0 else x-2.8, 1.5, 90+i*4.8), .5), GOLD, 'Sides')
        if side < 0:
            study.add('CheekDial'+suffix, cylinder(16, 4, (x, 17, 167), direction), DARK, 'Sides', 'rubber')
            study.add('CheekButton'+suffix, cylinder(7.4, 2, (x-4, 17, 167), direction), RED, 'Sides')
            for i in range(4):
                arrow = profile([(14,177),(20,177),(17,181)], 'YZ', (x-4.2,0,0), -.5)
                arrow.rotate(App.Vector(x,17,167), App.Vector(1,0,0), i*90)
                study.add(f'CheekArrow{suffix}{i}', arrow, WHITE, 'Details')
        else:
            study.add('CheekDial'+suffix, cylinder(16, 3, (x, 17, 167), direction), DARK, 'Sides', 'rubber')
            study.add('CheekKnob'+suffix, Part.makeCone(11,6.5,12,App.Vector(x+3,17,167),vector(direction)), METAL, 'Sides','metal')
        panel = box(3,26,38,(side*110 if side>0 else -113,38,73),1)
        holes=[]
        for row in range(7):
            for col in range(4):
                holes.append(cylinder(1.25,12,(side*108,42+col*6,80+row*4),direction))
        study.add('CheekPerforatedPanel'+suffix,panel.cut(Part.makeCompound(holes)),METAL,'Sides','metal')
        spine=profile([(36.35,232.46),(83.92,234.96),(67.72,184.28),
                       (65.23,73.42),(38.31,72.09)],
                      'YZ',(side*114,0,0),side*4)
        spine=spine.makeFillet(2.5,[e for e in spine.Edges if e.BoundBox.XLength>3.99])
        slots=[box(12,4.5,15,(side*116-6,41+i*10.5,221),.7) for i in range(4)]
        study.add('SideFrontSpine'+suffix,spine.cut(Part.makeCompound(slots+holes)),(.40,.39,.32),'Sides','metal')
        study.add('SideFrontSpineLiner'+suffix,box(.8,40,18,(113 if side>0 else -113.8,40,219)),DARK,'Sides','metal')
        # Four-view visible mouth arcs locate this recessed upper circular
        # socket. Its rolled body and blind back remain appearance assumptions.
        mx,sy,sz,inner_r=111.57419246096133,192.27910630805997,201.20766206780763,13.786160811310873
        center=App.Vector(0,sy,sz)
        outer=[(97.8,18.8),(99.2,20.1),(102,20.6),(105,20),(108.2,18.2),(110.3,15.7),(mx-.5,14.8)]
        inner=[(mx-.5,inner_r),(110,13.1),(106,12.6),(101,12.6),(97.8,12.6)]
        def socket_point(p):return App.Vector(side*p[0],sy+p[1],sz)
        def socket_curve(points):
            curve=Part.BSplineCurve();curve.interpolate([socket_point(p) for p in points]);return curve.toShape()
        section=Part.Wire([socket_curve(outer),Part.makeLine(socket_point(outer[-1]),socket_point(inner[0])),
                          socket_curve(inner),Part.makeLine(socket_point(inner[-1]),socket_point(outer[0]))])
        socket=Part.Face(section).revolve(center,App.Vector(side,0,0),360)
        study.add('SideSocketBase'+suffix,socket,(.17,.19,.18),'Sides','cast_metal')
        study.add('SideSocketLip'+suffix,ring(14.8,inner_r,.7,(side*(mx-.7),sy,sz),direction),
                  (.20,.22,.20),'Sides','metal')
        study.add('SideSocketRecess'+suffix,cylinder(20.1,1.4,(side*96.6,sy,sz),direction),DARK,'Sides','rubber')
        hull=study.doc.getObject('MainEnclosureShell')
        hull.Shape=hull.Shape.cut(cylinder(14.3,23,(side*97,sy,sz),direction))
        for prefix in ('SideClosure','SideMechanicalBacking'):
            obj=study.doc.getObject(prefix+suffix)
            obj.Shape=obj.Shape.cut(cylinder(21.2,23,(side*97.8,sy,sz),direction))
        # Three-view status-mark fit puts this panel behind the cladding.
        # Cut a real stepped recess and close it with a separate back plate.
        face_x,mark_y,top_z,pitch=97.78740291,206.66798790,173.55953009,10.65776531
        outline=[(189,183),(215,183),(215,144),(204,132),(189,144)]
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
        pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
        hull=study.doc.getObject('MainEnclosureShell')
        hull.Shape=hull.Shape.cut(pocket)
        # Flared cladding mouth reveals the recessed marks in rear oblique
        # views. The separate panel still closes the local main-shell opening.
        mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        def section(points,x):
            verts=[App.Vector(x,y,z) for y,z in points]
            return Part.Wire(Part.makePolygon(verts+[verts[0]]).Edges)
        flared=Part.makeLoft([section(inner,side*94.6),section(mouth,side*117)],True,True)
        for prefix in ('SideClosure','SideMechanicalBacking','RearArmourCheek'):
            obj=study.doc.getObject(prefix+suffix);obj.Shape=obj.Shape.cut(pocket).cut(flared)
        guard=study.doc.getObject('SideGuard'+suffix)
        relief=profile([(225,140),(239,140),(239,189),(225,189)],
                       'YZ',(side*100,0,0),side*16.5)
        guard.Shape=guard.Shape.cut(relief)
        # The source rear-side light disappears behind the status-panel band.
        light=study.doc.getObject('CyanSideTube'+suffix)
        light.Shape=light.Shape.cut(box(60,60,53,((85 if side>0 else -145),200,130)))
        plate=profile(outline,'YZ',(side*94.6,0,0),side*(face_x-.2-94.6))
        cutouts=[]
        for j,color in enumerate((WHITE,EDGE,RED)):
            z=top_z-j*pitch
            outer=profile([(mark_y-3.5,z-3.5),(mark_y+3.5,z-3.5),
                           (mark_y+3.5,z+3.5),(mark_y-3.5,z+3.5)],'YZ',(side*(face_x-.25),0,0),side*.25)
            hole=profile([(mark_y-2,z-2),(mark_y+2,z-2),(mark_y+2,z+2),(mark_y-2,z+2)],
                         'YZ',(side*(face_x-.8),0,0),side*2)
            cutouts.append(hole)
            study.add(f'SideStatusMark{suffix}{j}',outer.cut(hole),color,'Details','ink')
        slot_z=144
        slot=profile([(199,slot_z-1),(209,slot_z-1),(209,slot_z+1.6),(199,slot_z+1.6)],
                     'YZ',(side*(face_x-.25),0,0),side*.25)
        hole=profile([(199.6,slot_z-.4),(208.4,slot_z-.4),(208.4,slot_z+1),(199.6,slot_z+1)],
                     'YZ',(side*(face_x-.8),0,0),side*2)
        cutouts.append(hole)
        study.add('SideStatusSlot'+suffix,slot.cut(hole),EDGE,'Details','ink')
        bars=[]
        for y0,y1,z0,z1 in [(195,195.6,top_z-2*pitch,top_z),
                           (195,200,top_z-.3,top_z+.3),
                           (195,200,top_z-pitch-.3,top_z-pitch+.3),
                           (195,200,top_z-2*pitch-.3,top_z-2*pitch+.3)]:
            bars.append(profile([(y0,z0),(y1,z0),(y1,z1),(y0,z1)],
                        'YZ',(side*(face_x-.25),0,0),side*.20))
        study.add('SideStatusBracket'+suffix,Part.makeCompound(bars),(.65,.58,.36),'Details','ink')
        study.add('SideStatusPlate'+suffix,plate.cut(Part.makeCompound(cutouts)),(.022,.025,.022),'Sides','metal')
        # The full orbit shows the perforated barrel only on the red-wing side.
        # The gold-wing side ends in a shallow service plate, not a mirrored pod.
        if side > 0:
            continue
        # Reference utility module: Y-axis perforated barrel with a domed front.
        px, py, pz = side*132, 90, 77
        study.add('UtilityMount'+suffix, box(18,39,13,(side*106 if side>0 else -124,98,72),3),DARK,'Sides')
        study.add('UtilityLiner'+suffix,cylinder(18.5,66,(px,py,pz),(0,1,0)),DARK,'Sides','rubber')
        barrel=ring(21,19,60,(px,py+3,pz),(0,1,0))
        perforations=[]
        for row in range(11):
            for col in range(12):
                a=math.tau*(col+(row%2)*.5)/12
                radial=(math.cos(a),0,math.sin(a))
                perforations.append(cylinder(1.15,6,(px+18*radial[0],py+7+row*4.5,pz+18*radial[2]),radial))
        study.add('UtilityBarrel'+suffix,barrel.cut(Part.makeCompound(perforations)),SILVER,'Sides','metal')
        for i,dy in enumerate((0,4,60,65)):
            study.add(f'UtilityCollar{suffix}{i}',ring(22,18,2.5,(px,py+dy,pz),(0,1,0)),METAL,'Sides','metal')
        cap=round_loft([(0,20,0),(5,20,0),(13,16,0),(19,7,0)])
        cap.Placement=App.Placement(App.Vector(px,py,pz),App.Rotation(App.Vector(0,0,1),App.Vector(0,-1,0)))
        study.add('UtilityCap'+suffix,cap,DARK,'Sides','cable')
        for j in range(4):
            angle=math.radians(45+j*90)
            points=[(px+r*math.cos(angle),py-depth,pz+r*math.sin(angle))
                    for depth,r in ((1,20.2),(5,20.2),(10,18.1),(15,13.5),(18,9))]
            study.add(f'UtilityCapRib{suffix}{j}',tube(points,.45),METAL,'Details','metal')
        study.add('UtilityIndicator'+suffix,ring(6.5,4.5,1,(px,py-19,pz),(0,-1,0)),RED,'Sides','red_light')
        study.add('UtilityFrontLens'+suffix,cylinder(2.4,1,(px,py-20,pz),(0,-1,0)),RED,'Sides','red_light')
        study.add('UtilityControl'+suffix,box(23,45,7,(px-11.5,py+7,pz+18),2),GOLD,'Sides')
        study.add('UtilityControlInset'+suffix,box(17,30,.7,(px-8.5,py+12,pz+25),.2),DARK,'Sides')
        study.add('UtilitySwitch'+suffix,box(9,5,3,(px-4.5,py+17,pz+25),1),DARK,'Sides')
        study.add('UtilitySwitchRed'+suffix,cylinder(2.4,1.6,(px-7,py+12,pz+25)),RED,'Sides')
        for i in range(3):
            study.add(f'UtilityLED{suffix}{i}',cylinder(1.1,1.2,(px-4+i*4,py-17,pz-8),(0,-1,0)),CYAN,'Details','emission')
        # Curved coil axis and progressively tilted turns fitted in two video
        # views; the third view is held out. Hidden terminal leads are inferred.
        study.add('SideCable'+suffix,side_cable_solid(),DARK,'Details','cable')
        study.add('UtilityCableBoot'+suffix,Part.makeCone(4.5,2.6,6.8,
                  App.Vector(-132,155,77),App.Vector(0,1,0)),DARK,'Details','rubber')
        study.add('SideCableTopBoot'+suffix,Part.makeCone(3.6,2.5,18.5,
                  App.Vector(-97,200,179),App.Vector(-1,0,0)),DARK,'Details','rubber')
    for obj in study.items:
        if obj.Name.startswith(('UtilityControl','UtilitySwitch')):
            shape=obj.Shape.copy()
            shape.rotate(App.Vector(-132,90,77),App.Vector(0,1,0),-55)
            obj.Shape=shape
        if obj.Name.startswith(('FrontCheek','Cheek','VentBacking')) and not obj.Name.startswith('CheekPerforatedPanel'):
            # Shared side-control centers fitted in video frames 60 and 180.
            # The old -25 mm shift exposed an oversized strip beside the bezel.
            shape=obj.Shape.copy();shape.translate(App.Vector(0,-1.14,-2.2));obj.Shape=shape
    for i,x in enumerate((-8,-4,0,4,8)):
        points=[(x,70,50),(x+3,95,28),(x+3,150,31),(x,170,55)]
        study.add(f'UnderbodyHarness{i}',tube(points,1.2),RED if i==0 else WHITE if i<4 else DARK,'Details','cable')


def rear_raked_slab(front, back, bottom, top, half_width, knee=134):
    """One rounded prism shared by the raked cavity and closure clearance."""
    shift=(bottom-knee)*.98
    section=[(front+shift,bottom),(back+shift,bottom),(back,knee),
             (back,top),(front,top),(front,knee)]
    shape=profile(section,'YZ',(-half_width,0,0),2*half_width)
    edges=[e for e in shape.Edges if e.BoundBox.XLength>2*half_width-.01
           and abs(e.CenterOfMass.z-knee)<.01]
    return shape.makeFillet(8,edges)


def raked_rear_parts(knee=134, outer_x=116.76, lower_rise=6):
    """Construct folded rear pieces and a curved side-to-back transition.

    Keeping each fold inside a single rounded prism avoids the invalid curve-on-
    surface boundaries produced by shearing and fusing trimmed NURBS halves.
    Corner radii and the hidden nozzle passage remain appearance assumptions.
    """
    slope = .98
    def slab(front, back, bottom, top, half_width):
        return rear_raked_slab(front,back,bottom,top,half_width,knee)
    def framed(w,h,z,border,radius,front,back):
        outline=rounded_frame(w,h,400,border,(-w/2,0,z),radius)
        return outline.common(slab(front,back,z,z+h,w/2))
    # Appearance-derived narrower back face and rounded side transition.
    # The shell backing overlaps the retained internal sloping skin.
    # Raise the lower cladding edge without thinning the rounded frame border
    # or moving the cavity, nozzle, shoulders and upper antenna connections.
    panel_bottom=60.12+lower_rise
    panel=rounded_plate(178.6,233.8-panel_bottom,400,(-89.3,0,panel_bottom),3.36)
    panel=panel.common(slab(218.75,244,panel_bottom,233.8,89.3))
    bore_axis=App.Vector(0,.574,-.819);bore_axis.normalize()
    bore=cylinder(50,180,tuple(App.Vector(0,180,173)-bore_axis*40),tuple(bore_axis))
    # The dark region around the nozzle is a recessed housing, not another
    # cylindrical nozzle wall. Open the cladding and retain an actual backing,
    # side walls, forward lip and recessed light mounting ledge. Dimensions are
    # appearance assumptions checked in both fixed rear-oblique cameras.
    opening=rounded_plate(138,116,400,(-69,0,76),8)
    backing=slab(220,223,74,194,71).cut(bore)
    walls=slab(222,244,74,194,71).cut(opening)
    lip=framed(142,120,74,2,10,242,247)
    light_seat=framed(142,120,74,4,10,238,240)
    liner=backing.fuse(walls).fuse(lip).fuse(light_seat).removeSplitter()
    parts={'RearServicePanel':panel.cut(bore).cut(opening),
           'RearStructuralFrame':framed(178,170-lower_rise,61.8+lower_rise,7.56,10.08,241.75,248),
           'RearCyanFrame':framed(137,115,76.5,1.6,7.5,239.8,241.2),
           'RearRecessLiner':liner}
    def rear_y(z,y,h,s,r=8):
        angle=math.atan(s);d=r*math.tan(angle/2)
        top=h+d;bottom=h-d/math.sqrt(1+s*s)
        if z>=top:return y
        if z<=bottom:return y+(z-h)*s
        return y-r+math.sqrt(r*r-(z-top)**2)
    for side,suffix in ((-1,'Left'),(1,'Right')):
        wires=[]
        for z in (67.3,100,123,125,127,129,131,133,135,137,139,141,143,145,180,222):
            back=rear_y(z,248,knee,slope)
            edge=rear_y(z,230.5125,136.2828,64.325/69.4764)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                points=[App.Vector(side*(89+(rx-inset)*math.sin(a)),
                                   edge+(ry-inset)*math.cos(a),z)
                        for a in [i*math.pi/2/16 for i in range(17)]]
                if reverse:points.reverse()
                spline=Part.BSplineCurve();spline.interpolate(points)
                return spline.toShape(),points
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4,0);it=ip[0]+App.Vector(0,-4,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),
                Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
        parts['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
    for name,shape in parts.items():
        if not shape.isValid() or len(shape.Solids)!=1:
            raise ValueError('Invalid rear part: '+name)
        shape.check(True)
    return parts


def rear_cavity_lighting(frame, shell):
    """Rounded primary rails, real reflectors and four separate luminous corners.

    The secondary dim reference trace can be produced by reflection; it is not
    modelled as another lamp. The fitted rail axis and the hidden bend lengths
    are appearance inferences. Only these new parts clear the nozzle envelope.
    """
    wires=[]
    for z,rx,ry,dy in [(0,49,49,0),(28,70,66,-1),(60,68,66,1),(94.81,53.82,53.82,-1.15)]:
        points=[App.Vector((rx+.3)*math.cos(i*math.tau/128),dy+(ry+.3)*math.sin(i*math.tau/128),z) for i in range(128)]
        curve=Part.BSplineCurve();curve.interpolate(points,PeriodicFlag=True)
        wires.append(Part.Wire([curve.toShape()]))
    envelope=Part.makeLoft(wires,True,False)
    axis=App.Vector(0,.574,-.819);axis.normalize()
    envelope.Placement=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),axis))
    updated_envelope = root_shifted_fairing(envelope_only=True)
    updated_envelope.Placement = envelope.Placement
    envelope = envelope.fuse(updated_envelope)
    # Keep the rail/reflector positions and their previously checked clearances.
    # Only the two upper corner ends meet the deeper v50 fairing envelope.
    fixture_envelope = envelope
    corner_envelope = blended_fairing_parts(envelope_only=True, depth_extra=4)
    corner_envelope.Placement = updated_envelope.Placement
    envelope = envelope.fuse(corner_envelope)
    # Narrowing one interpolated station can bulge a neighbouring span.
    # Validate the actual loft independently of historical light clearance cuts.
    shoulder_envelope = blended_fairing_parts(envelope_only=True, depth_extra=4,
                                             shoulder_inset=6, lower_inset=0)
    shoulder_envelope.Placement = updated_envelope.Placement
    # Keep existing light ends: the extra 0.3 mm envelope would shave a clear
    # lower corner. Every light is checked against the actual shell below.
    if shell.cut(shoulder_envelope).Volume>1e-5:raise ValueError('Nozzle clearance envelope does not contain shell')
    pieces=frame.cut(box(200,400,81,(-100,0,94))).cut(envelope).Solids
    upper=sorted([s for s in pieces if s.CenterOfMass.z>150],key=lambda s:s.CenterOfMass.x)
    lower=sorted([s for s in pieces if s.CenterOfMass.z<100],key=lambda s:s.CenterOfMass.x)
    if len(upper)!=2 or len(lower)!=2:raise ValueError('Expected four separate cavity light corners')
    parts={name:(s,CYAN,'emission') for name,s in [('RearCyanFrame',upper[0]),('RearCyanUpperLeft',upper[1]),
            ('RearCyanLowerRight',lower[0]),('RearCyanLowerLeft',lower[1])]}
    for side,suffix in [(1,'Left'),(-1,'Right')]:
        x=side*65.36773626
        rail=tube([(x,231,176),(x,234.6,175),(x,236.50410262,172),
                   (x,236.50410262,147),(x,235.6,142),(x,231,138)],1.5)
        parts['RearCavityEmitter'+suffix]=(rail.cut(fixture_envelope),CYAN,'emission')
        backing=rounded_plate(9,42,2,(x-4.5,229.8,136),2)
        parts['RearCavityReflector'+suffix]=(backing.cut(fixture_envelope),(.42,.45,.43),'metal')
        for name,z in [('Upper',173.5),('Lower',136.8)]:
            clip=rounded_plate(9,4.2,10.5,(x-4.5,230,z),1.6)
            clip=clip.cut(cylinder(1.35,7,(x,236.50410262,z-1))).cut(fixture_envelope)
            parts['RearCavityClip'+name+suffix]=(clip,(.055,.065,.06),'metal')
    for name,(s,_,_) in parts.items():
        s.check(True)
        if not s.isValid() or len(s.Solids)!=1 or s.common(shell).Volume>1e-6:
            raise ValueError('Invalid cavity lighting or nozzle interference: '+name)
    return parts


def add_sloping_rear_closure(study):
    """Join the revised outer trim to the retained inner sloping skin."""
    knee=134
    for name,shape in raked_rear_parts(knee,outer_x=112.76).items():
        study.doc.getObject(name).Shape=shape
    lighting=rear_cavity_lighting(study.doc.getObject('RearCyanFrame').Shape,study.doc.getObject('BassNozzleShell').Shape)
    for name,(shape,color,material) in lighting.items():
        if name=='RearCyanFrame':study.doc.getObject(name).Shape=shape
        else:study.add(name,shape,color,'Rear',material)
    # Partition overlapping front faces instead of letting two coincident
    # gold surfaces shadow each other. Both parts retain the real slot cuts;
    # otherwise the frame behind the carrier fills the antenna-side recesses.
    frame=study.doc.getObject('RearStructuralFrame')
    carrier=study.doc.getObject('RearRailCarrier')
    frame_shape=frame.Shape.copy();carrier_shape=carrier.Shape.copy()
    for side in (-1,1):
        slot=rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3)
        frame_shape=frame_shape.cut(slot);carrier_shape=carrier_shape.cut(slot)
    frame.Shape=frame_shape
    carrier.Shape=carrier_shape.cut(frame_shape).removeSplitter()
    cut=profile([(150,58),(228,126),(360,126),(360,-30),(49,-30)],
                'YZ',(-180,0,0),360)
    for obj in study.items:
        if obj.Name.startswith(('MainEnclosure','ClosedBellyPan','BottomChassis')):
            shape=obj.Shape.cut(cut)
            if not shape.isValid() or not shape.Solids:
                raise ValueError('Invalid sloping rear closure: '+obj.Name)
            obj.Shape=shape
    slope=profile([(150,58),(228,126),(224.7,129.8),(146.7,61.8)],'YZ',(-100.8,0,0),201.6)
    # The narrower nozzle exposes this closure: trim its cavity intrusion
    # rather than hiding two gold tabs behind an oversized fairing.
    clearance=rear_raked_slab(223,330,74,194,69).common(
        rounded_plate(138,116,400,(-69,0,76),8))
    slope=slope.cut(clearance)
    study.add('RearLowerSlope',slope,GOLD,'Hull')
    for obj in list(study.items):
        if obj.Name.startswith('RearArmourBolt'):
            study.items.remove(obj);study.doc.removeObject(obj.Name)
        elif obj.Name.startswith(('RearRecessWire','RearRecessCornerBoss')):
            shape=obj.Shape.copy();shape.translate(App.Vector(0,12,0));obj.Shape=shape


def rebuilt_side_closure(side, with_status_cut=True):
    """Recreate planar extrusion before rounding, avoiding affine 3D fillets.

    The Y/Z perimeter retains the existing transformed corner curves. The
    thickness-edge fillet is now a true 2.1mm world-space radius; this is an
    intentional small geometric change, not a lossless normalization.
    """
    outline=[(54.4,187.9),(69.67,241.01),(171.39,244.33),(183.98,232.58),
             (184.41,133.67),(132.95,50.96),(80.38,49.36),(53.38,72.45)]
    source=profile(outline,'YZ',(0,0,0),1)
    source=source.makeFillet(10,[e for e in source.Edges if e.BoundBox.XLength>.99])
    face=min((f for f in source.Faces if abs(f.normalAt(0,0).x)>.99),key=lambda f:f.CenterOfMass.x)
    matrix=App.Matrix();matrix.A22=1.25;matrix.A33=.84;matrix.A34=24;matrix.A14=side*100.8
    wire=Part.Wire(face.OuterWire.transformGeometry(matrix).Edges)
    result=Part.Face(wire).extrude(App.Vector(side*12.6,0,0))
    result=result.makeFillet(2.1,[e for e in result.Edges if e.BoundBox.XLength<.01])
    result=result.cut(cylinder(64,17,(side*100,129.09686,153.62312),(side,0,0)))
    result=result.cut(cylinder(21.2,23,(side*97.8,192.27910630805997,201.20766206780763),(side,0,0)))
    if not with_status_cut:
        return result
    inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
    mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
    def section(points,x):
        vs=[App.Vector(x,y,z) for y,z in points]
        return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
    result=result.cut(profile(inner,'YZ',(side*94.6,0,0),side*25))
    return result.cut(Part.makeLoft([section(inner,side*94.6),section(mouth,side*117)],True,True))


def rebuilt_side_bolt(side,index):
    """Analytic elliptical extrusion with the original scaled screwdriver slot."""
    y,z=((83,62),(115,62),(178,229),(70,223))[index]
    radius=1.7 if index<2 else 2.6
    center=App.Vector(side*139*.84,y*1.25,z*.84+24)
    ellipse=Part.Ellipse(center+App.Vector(0,radius*1.25,0),center+App.Vector(0,0,radius*.84),center)
    result=Part.Face(Part.Wire([ellipse.toShape()])).extrude(App.Vector(side*1.8*.84,0,0))
    slot=box(radius*1.2,.9,2.8,(-radius*.6,-.45,-.5))
    slot.rotate(App.Vector(),App.Vector(0,0,1),25)
    slot.Placement=App.Placement(App.Vector(side*139,y,z),App.Rotation(App.Vector(0,0,1),App.Vector(side,0,0))).multiply(slot.Placement)
    matrix=App.Matrix();matrix.A11=.84;matrix.A22=1.25;matrix.A33=.84;matrix.A34=24
    return result.cut(slot.transformGeometry(matrix))


def refine_side_cladding(study, inset=4):
    """Narrow the connected trim while preserving the fixed side controls.

    Video/still candidate E retains visibility through a wider guard notch.
    The supported screen, nozzle, ring-connected wires and four shafts do not
    move. World-space repairs avoid invalid affine fillet parameter curves.
    """
    prefixes=('SideClosure','SideMechanicalBacking','SideGuard','SideFrameShoe',
              'SideFrameBolt','CyanSideTube','SideFrontSpine')
    for obj in study.items:
        name=obj.Name
        if not name.startswith(prefixes):continue
        side=-1 if 'Left' in name else 1
        if name.startswith('SideClosure'):shape=rebuilt_side_closure(side)
        elif name.startswith('SideGuard'):shape=obj.Shape.toNurbs()
        elif name.startswith('SideFrameBolt'):shape=rebuilt_side_bolt(side,int(name[-1]))
        else:shape=obj.Shape.copy()
        # Keep the original small mounting patch beneath each unchanged arm.
        seat=shape.common(box(40,21,5,((90 if side>0 else -130),98.5,223))) if name.startswith('SideClosure') else None
        shape.translate(App.Vector(-side*inset,0,0))
        if seat is not None:shape=shape.fuse(seat)
        if name.startswith(('SideClosure','SideMechanicalBacking')):
            inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
            mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
            def wire(points,x):
                vs=[App.Vector(x,y,z) for y,z in points]
                return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
            shape=shape.cut(profile(inner,'YZ',(side*94.6,0,0),side*25))
            shape=shape.cut(Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True))
        elif name.startswith('SideGuard'):
            relief=profile([(219.8,140),(239,140),(239,189),(219.8,189)],
                           'YZ',(side*100,0,0),side*16.5)
            shape=shape.cut(relief)
        shape.check(True)
        if not shape.isValid() or len(shape.Solids)!=len(obj.Shape.Solids):
            raise ValueError('Invalid narrowed side cladding: '+name)
        obj.Shape=shape


def reprojected_rear_shoulders(outer_x,scale,eye_y,eye_z,exponent=1.5):
    def rear_y(z,y,knee,slope,radius=8):
        angle=math.atan(slope);d=radius*math.tan(angle/2)
        top=knee+d;bottom=knee-d/math.sqrt(1+slope*slope)
        if z>=top:return y
        if z<=bottom:return y+(z-knee)*slope
        return y-radius+math.sqrt(radius*radius-(z-top)**2)
    map_z=lambda z:eye_z+scale*(z-eye_z)
    stations=sorted(set([map_z(z) for z in [67.3,100,123,125,127,129,131,133,135,137,139,141,143,145,180,222]]+
                        [125,127,129,131,133,135,137,139,141,143,145]))
    result={}
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        wires=[]
        for z in stations:
            back=rear_y(z,248,134,.98)
            original_z=eye_z+(z-eye_z)/scale
            original_y=rear_y(original_z,230.5125,136.2828,64.325/69.4764)
            edge=eye_y+scale*(original_y-eye_y)
            rx=outer_x-89;ry=back-edge
            def curve(inset,reverse=False):
                pts=[App.Vector(side*(89+(rx-inset)*math.sin(i*math.pi/32)**(2/exponent)),edge+(ry-inset)*math.cos(i*math.pi/32)**(2/exponent),z) for i in range(17)]
                if reverse:pts.reverse()
                spline=Part.BSplineCurve();spline.interpolate(pts)
                return spline.toShape(),pts
            outer,op=curve(0);inner,ip=curve(3.5,True)
            ot=op[-1]+App.Vector(0,-4*scale,0);it=ip[0]+App.Vector(0,-4*scale,0)
            wires.append(Part.Wire([outer,Part.makeLine(op[-1],ot),Part.makeLine(ot,it),Part.makeLine(it,ip[0]),inner,Part.makeLine(ip[-1],op[0])]))
        result['RearArmourCheek'+suffix]=Part.makeLoft(wires,True,True)
    return result


def reproject_side_cladding(study):
    """Use the reviewed X108 frame plane and retain the unchanged arm seats.

    Camera-space rays determine Y/Z, then actual BReps are uniformly scaled.
    The reference camera remains fixed; this does not transform rendered pixels.
    """
    outer_x=108.0
    eye=(1100.478706826763,481.9590609254328,317.0386845391606)
    scale=(outer_x-eye[0])/(116.76-eye[0])
    prefixes=('SideClosure','SideMechanicalBacking','SideGuard','SideFrameShoe',
              'SideFrameBolt','CyanSideTube','SideFrontSpine')
    parts={}
    for obj in study.items:
        name=obj.Name
        if not name.startswith(prefixes):continue
        side=-1 if 'Left' in name else 1
        shape=obj.Shape.copy()
        shape.translate(App.Vector(side*4,0,0))
        shape.scale(scale)
        shape.translate(App.Vector(side*(outer_x-scale*116.76),eye[1]*(1-scale),eye[2]*(1-scale)))
        if name.startswith('SideClosure'):
            seat=obj.Shape.common(box(40,21,5,((90 if side>0 else -130),98.5,223)))
            shape=shape.fuse(seat)
        parts[name]=shape
    parts.update(reprojected_rear_shoulders(outer_x,scale,eye[1],eye[2]))
    for side,suffix in [(-1,'Left'),(1,'Right')]:
        inner=[(190,182),(214,182),(214,145),(204,133),(190,145)]
        mouth=[(185,190),(239,190),(239,140),(206,128),(185,140)]
        def wire(points,x):
            vs=[App.Vector(x,y,z) for y,z in points];return Part.Wire(Part.makePolygon(vs+[vs[0]]).Edges)
        pocket=profile(inner,'YZ',(side*94.6,0,0),side*25)
        flared=Part.makeLoft([wire(inner,side*94.6),wire(mouth,side*117)],True,True)
        for prefix in ['SideClosure','SideMechanicalBacking','RearArmourCheek']:
            name=prefix+suffix;parts[name]=parts[name].cut(pocket).cut(flared)
        relief=profile([(212,140),(239,140),(239,189),(212,189)],'YZ',(side*90,0,0),side*30)
        name='SideGuard'+suffix;parts[name]=parts[name].cut(relief)
        parts[name]=trim_guard_notch(parts[name],side)
        name='SideClosure'+suffix
        parts[name]=restore_status_rim(parts[name],side,rebuilt_side_closure(side,with_status_cut=False))
    for obj in study.items:
        if obj.Name not in parts:continue
        shape=parts[obj.Name];shape.check(True)
        if not shape.isValid() or not shape.Solids or not all(s.isClosed() for s in shape.Solids):
            raise ValueError('Invalid reprojected side cladding: '+obj.Name)
        obj.Shape=shape


def build(root, frame_view=True):
    """Create and save a separate appearance concept without changing terminal."""
    root = Path(root)
    out = root/'cad/drone-concept'
    out.mkdir(parents=True, exist_ok=True)
    if 'vintrox_drone_refined' in App.listDocuments():
        raise RuntimeError('Concept document already open; close it before rebuilding.')
    doc = App.newDocument('vintrox_drone_refined')
    doc.Label = 'VINTROX Drone — 整圈参考比例修订'
    b = Study(doc)
    params = doc.addObject('Spreadsheet::Sheet', 'Parameters')
    params.Label = chinese_label('Parameters')
    values = [
        ('ScreenWidth', 210, '用户测量口述 mm'), ('ScreenHeight', 160, '用户测量口述 mm'),
        ('ScreenThickness', 2, '用户测量口述 mm'), ('ActiveWidth', 200, '用户指定 mm'),
        ('ActiveHeight', 150, '用户指定 mm'), ('HullWidth', 201.6, '外观假设 mm'),
        ('HullDepth', 220, '外观假设 mm'), ('WingTop', 361.54, '参考轮廓反投影假设 Z mm'),
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
    bass_axis = App.Vector(0, .574, -.819)
    bass_axis.normalize()
    bass_origin = App.Vector(0, 168, 158)
    bass_passage = cylinder(47, 100, tuple(bass_origin-bass_axis*18), tuple(bass_axis))
    hull = box(240, 176, 235, (-120, 0, 38), 10)
    hull = hull.cut(box(232, 168, 227, (-116, 4, 42), 6))
    hull = hull.cut(box(216, 25, 176, (-108, -10, 65), 4))
    hull = hull.cut(bass_passage)
    hull = hull.cut(box(290, 190, 40, (-145, -5, 247)))
    b.add('MainEnclosureShell', hull, GOLD, 'Hull')
    roof=source_roof_shell()
    b.add('SlopedUpperArmour',roof.common(box(192,230,100,(-96,-5,210))),GOLD,'Hull')
    for side in (-1,1):
        side_x=96 if side>0 else -101
        b.add(f'RoofSideClosure{side:+}',roof.common(box(5,230,100,(side_x,-5,210))),GOLD,'Hull')
    b.add('RearUpperClosure', box(240, 8, 18, (-120, 168, 244), 2), GOLD, 'Hull')
    b.add('BottomChassis', box(232, 158, 7, (-116, 9, 35), 2), DARK, 'Hull')
    belly = profile([(20, 35), (38, 15), (144, 12), (172, 28), (172, 42), (20, 42)],
                    'YZ', (-108, 0, 0), 216)
    b.add('ClosedBellyPan', belly, DARK, 'Hull', 'metal')
    back = box(232, 9, 218, (-116, 175, 43), 4).cut(bass_passage)
    b.add('RearServicePanel', back, GOLD, 'Hull')
    b.add('RearStructuralFrame', rounded_frame(232, 214, 5, 9, (-116, 181, 45), 12), GOLD, 'Hull')
    # Deep continuous brow: large front corner radii and descending side ends.
    hood = brow_u(243.1,264.2,29.4,9.3,201.6,-46,70)
    hood = hood.makeFillet(1.2, [e for e in hood.Edges if e.BoundBox.YLength < .01])
    b.add('ProjectingBrow', hood, GOLD, 'Hull')
    # The shoulder folds inward toward the front arch instead of projecting
    # square tabs above its corners. The rear portion retains its side depth.
    shoulder_wires = []
    for y,width,radius in ((-50,243.1,29.4),(-25,253,25),(15,265,15),(50,265,15)):
        cap = rounded_plate(width,164.2,1,(-width/2,y,100),radius)
        front_face = min((f for f in cap.Faces if f.findPlane(1e-6) is not None
                          and abs(f.normalAt(0,0).y) > .99),key=lambda f:f.CenterOfMass.y)
        shoulder_wires.append(front_face.OuterWire)
    shoulder_envelope = Part.makeLoft(shoulder_wires,True,False)
    # Shallow pockets have real floors; the full hood stays a closed solid.
    for side in (-1, 1):
        suffix = 'Left' if side < 0 else 'Right'
        center=App.Vector(side*119,9,244)
        start=App.Vector(side*119,-20,226)
        middle=App.Vector(side*137,-20,244)
        end=App.Vector(side*119,-20,262)
        section=Part.Wire([Part.Arc(start,middle,end).toShape(),Part.makeLine(end,start)])
        bulge=Part.Face(section).extrude(App.Vector(0,58,0))
        bulge=bulge.makeFillet(2,[e for e in bulge.Edges if e.BoundBox.YLength<.01 and e.Length>40])
        scaling=App.Matrix();scaling.A11=7/18
        scaling.A14=center.x*(1-7/18)
        bulge=bulge.transformGeometry(scaling)
        pocket=cylinder(18,14,(side*118,9,244),(side,0,0))
        pocket_scale=App.Matrix();pocket_scale.A22=29/18;pocket_scale.A24=9*(1-29/18)
        pocket=pocket.transformGeometry(pocket_scale)
        brow=doc.getObject('ProjectingBrow');brow.Shape=brow.Shape.cut(pocket)
        b.add('HoodShoulderCrown'+suffix,bulge,(.60,.47,.24),'Hull')
        shoulder = [(21.77,199.32),(33.86,228.91),(-5.97,229.21),(-10.08,231.97),
                    (-15.16,262.58),(-45.77,264.90),(-43.82,206.28),(-41.61,202.23),(-38.06,200.32)]
        shoulder_plate = profile(shoulder,'YZ',(side*123,0,0),side*4)
        shoulder_plate = shoulder_plate.makeFillet(1.5,[e for e in shoulder_plate.Edges if e.BoundBox.XLength>3.99])
        taper = App.Matrix();taper.A12 = side*.12;taper.A14 = -side*.12*33.86
        shoulder_plate = shoulder_plate.transformGeometry(taper).common(shoulder_envelope)
        slot = box(12, 27, 3.6, (side*125-6, -6, 210.7), 1)
        b.add('HoodShoulderPlate'+suffix, shoulder_plate.cut(slot), GOLD, 'Hull')
        brow = doc.getObject('ProjectingBrow')
        brow.Shape = brow.Shape.cut(slot)
        b.add('HoodShoulderSlotLiner'+suffix,box(1,27,5.6,(side*121 if side>0 else -122,-6,209.7)),DARK,'Hull','rubber')
        b.bolt('HoodShoulderBolt'+suffix, (side*(126.95+.12*(17.28-33.86)), 17.28, 212.49), (side, 0, 0), 5.2)
        x = -89 if side < 0 else 35
        b.add('HoodTopInset'+suffix, box(54, 27, 1.4, (x, -19, 260), 1), DARK, 'Hull')
        slots=[]
        for i in range(3):
            slots.append(box(8,22,9,(x+6+i*15,-17,261),.8))
        brow.Shape=brow.Shape.cut(Part.makeCompound(slots))
    hood_liner = brow_u(226.5,255.9,21.1,3.2,201.6,-41,55)
    b.add('BrowUnderside', hood_liner, DARK, 'Hull', 'rubber')
    edge = brow_u(226.9,256.1,21.3,.9,201.6,-47,1.2)
    b.add('HoodEdge', edge, EDGE, 'Hull', 'metal')
    # Extend only the lower surround to the source lower edge; retain the
    # measured screen and the existing opening around its active area.
    # The source front frame projects slightly wider and taller than the
    # measured flat display; keep the 202 x 152 mm opening and screen input
    # unchanged while matching the outer reference surround.
    bezel=rounded_plate(220,172,11,(-110,-13,63),12).cut(
          rounded_plate(202,152,13,(-101,-14,74),8.5))
    b.add('ScreenBezel',bezel,DARK,'Face','rubber')
    lip=rounded_frame(224,176,3,2,(-112,-15,61),13)
    lip=lip.makeFillet(.45,[e for e in lip.Edges if e.BoundBox.YLength<.01])
    b.add('BezelLip',lip,GOLD,'Face','metal')
    panel = doc.addObject('Part::Box', 'ScreenPanel210x160x2')
    panel.Label = chinese_label('ScreenPanel210x160x2')
    panel.setExpression('Length', 'Parameters.ScreenWidth')
    panel.setExpression('Width', 'Parameters.ScreenThickness')
    panel.setExpression('Height', 'Parameters.ScreenHeight')
    panel.Placement.Base = App.Vector(-105, -1, 70)
    panel.addProperty('App::PropertyString', 'EvidenceStatus', 'Design')
    panel.EvidenceStatus = '用户测量210×160×2mm；接口与安装净空待验证'
    if panel.ViewObject is not None: panel.ViewObject.ShapeColor = DARK
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
    if active.ViewObject is not None: active.ViewObject.ShapeColor = GREEN
    active.addProperty('App::PropertyString', 'RenderMaterial', 'Design')
    active.RenderMaterial = 'screen'
    b.items.append(active)
    # Display-only face on the existing flat 4:3 screen, behind the separate cap.
    for x in (-39, 27):
        eye=box(12,.5,22,(x,-9.6,175)).fuse(box(6,.5,3,(x+3,-9.6,172)))
        b.add(f'PixelEye{x}', eye, DARK, 'Face', 'screen_ink')
        b.add(f'PixelEyeTop{x}', box(6, .5, 4, (x+3, -9.6, 197)), DARK, 'Face', 'screen_ink')
    b.add('PixelMouth', profile([(-75,147),(75,147),(75,135),(65,135),(65,126),
          (54,126),(54,118),(43,118),(43,111),(33,111),(33,105),(20,105),(20,101),
          (-20,101),(-20,105),(-33,105),(-33,111),(-43,111),(-43,118),(-54,118),
          (-54,126),(-65,126),(-65,135),(-75,135)],
          'XZ', (0, -9.6, 0), .5), DARK, 'Face', 'screen_ink')
    smile=box(140,.4,8,(-70,-10,135)).fuse(box(58,.4,5,(-29,-10,130)))
    b.add('PixelSmileHighlight', smile, WHITE, 'Face', 'screen')
    # A separate shallow transparent cap approximates the reference's curved
    # reflection while retaining the measured flat panel and active rectangle.
    # Optical distortion, material and fabrication are untested assumptions.
    glass = Part.makeSphere(1000,App.Vector(0,981,150)).cut(Part.makeSphere(998.8,App.Vector(0,981,150)))
    glass = glass.common(rounded_plate(200,150,22,(-100,-25,75),12))
    cover=b.add('ScreenCurvedCover',glass,(.8,.94,.74),'Face','glass')
    if cover.ViewObject is not None: cover.ViewObject.Transparency=88
    # Video frames 270, 0 and 240 jointly locate the housing, key faces and
    # knob caps. Dimensions below are appearance fits, not manufacturing data.
    rail_w,rail_h,rail_y,rail_z=206.19156238,26.29319470,-6.93125240,44.54044806
    olive=(.16,.19,.11);bronze=(.32,.30,.22);knob_dark=(.035,.045,.037)
    b.add('ControlRail', rounded_plate(rail_w,rail_h,25,
          (-rail_w/2,rail_y+.8,rail_z-rail_h/2),4),olive,'Face','cast_metal')
    b.add('ControlInset',rounded_plate(rail_w-2,rail_h-2,1.3,
          (-rail_w/2+1,rail_y+.25,rail_z-rail_h/2+1),3.2),olive,'Face','metal')
    b.add('ControlRailLip',rounded_frame(rail_w,rail_h,1,.8,
          (-rail_w/2,rail_y,rail_z-rail_h/2),4),bronze,'Face','metal')
    b.add('ControlKeyBed',rounded_plate(116,20,1.2,(-96,-7.3,35.8),1.5),DARK,'Face','rubber')
    for side in (-1, 1):
        suffix = 'Left' if side < 0 else 'Right'
        end = crowned_plate([(-19, 29), (-19, 56), (3, 56), (7, 51), (7, 32)],
                            'YZ', (side*113, 0, 0), side*6, 2)
        b.add('ControlRailEnd'+suffix, end, METAL, 'Face', 'metal')
        b.bolt('ControlEndBolt'+suffix, (side*119, -6, 42), (side, 0, 0), 3.8)
    # Hand-traced short strokes approximate the four source pictograms. They
    # remain raised CAD geometry; small source strokes are not fully resolved.
    glyphs=[[[(-4,4),(-3,1),(-1,0),(1,1),(1,4)],[(1,1),(1,-3),(-1,-5),(-4,-4)],
             [(3,3),(5,3)],[(3,0),(5,0)],[(3,-3),(5,-3)]],
            [[(-5,2),(-3,4),(0,5),(3,4),(5,2)],
             [(-1,-4),(0,2),(2,-2),(4,-4)]],
            [[(-5,2),(-4,0),(-5,-2),(-6,-1)],
             [(-2,3),(4,3)],[(-2,0),(6,0)],[(-2,-3),(4,-3)],[(4,2),(6,0),(4,-2)]],
            [[(-5,-4),(-3,-4),(-1,-1),(0,1),(1,-2),(3,-4),(5,-4)],
             [(-1,3),(1,5),(2,3),(-1,3)]]]
    for i,x in enumerate((-84.16317550,-40.50554001,-17.60757993,5.65467558)):
        z=45.78431823;y=-9.43579761
        b.add(f'KeySocket{i}',rounded_plate(19.5,16,1.5,(x-9.75,-7.8,z-8),.8),knob_dark,'Face','rubber')
        b.add(f'RedKey{i}',box(17.5,2.8,13.8,(x-8.75,y,z-6.9),.6),(.49,.018,.028),'Face')
        strokes=[tube([(x+u,y-.15,z+v) for u,v in stroke],.24) for stroke in glyphs[i]]
        b.add(f'KeyGlyph{i}',Part.makeCompound(strokes),(.64,.58,.42),'Face')
    b.add('StatusKeyFrame',rounded_frame(11,11,2,1.8,(-68.7,-8.8,40.3),1.5),
          knob_dark,'Face','metal')
    b.add('StatusKeyLens',rounded_plate(5.5,4,.8,(-65.95,-7.7,43.8),.8),
          (.28,.003,.008),'Face','red_light')
    # The visible first-cap outline, rather than an ambiguous dark center,
    # sets cap radius and a slight downward axis. See knob-outline-fit.json.
    axis=App.Vector(0,-.9953921546936677,-.09588773839390424)
    u=App.Vector(1,0,0);v=axis.cross(u)
    for i in range(3):
        cap=App.Vector(33.37404087845301+i*27.2,-17.0549876487441,45.79308002661759)
        base_front=cap-axis*8.8
        b.add(f'KnobBase{i}',cylinder(10.3,2.2,tuple(cap-axis*11),tuple(axis)),knob_dark,'Face','rubber')
        b.add(f'KnobRing{i}',ring(9,7.8,.65,tuple(base_front),tuple(axis)),(.08,.32,.31),'Face','metal')
        b.add(f'ControlKnob{i}',Part.makeCone(7.8,6.5,7.9,base_front,axis),knob_dark,'Face','rubber')
        b.add(f'KnobFace{i}',cylinder(6.13302323363055,.9,tuple(cap-axis*.9),tuple(axis)),
              (.065,.085,.075),'Face','metal')
        teeth=[]
        for j in range(24):
            a=j*math.tau/24;radial=u*math.cos(a)+v*math.sin(a)
            p0=base_front+axis*.3+radial*7.71
            p1=base_front+axis*7.6+radial*6.51
            delta=p1-p0
            teeth.append(cylinder(.11,delta.Length,tuple(p0),tuple(delta)))
        b.add(f'KnobFlute{i}',Part.makeCompound(teeth),knob_dark,'Face','rubber')
        b.add(f'KnobPointer{i}',tube([tuple(cap+axis*.05-u*3.1-v*4.8),
                                    tuple(cap+axis*.05-u*2.1-v*3.3)],.3),
              (.61,.61,.47),'Face')

    # Side rings and the thin illuminated armour frame behind them.
    # Video frame 180 boundary at the retained side mounting plane; see
    # fit_drone_side_frame.py. Rear/lower gold rim is deliberately broader.
    side_outline = [(54.4,187.9),(69.67,241.01),(171.39,244.33),(183.98,232.58),
                    (184.41,133.67),(132.95,50.96),(80.38,49.36),(53.38,72.45)]
    light_outline = [(60.45,187.12),(75.59,235.72),(170.68,236.29),(174.4,229.5),
                     (174.68,147.06),(129.1,78.63),(75.31,73.99),(59.7,97.09)]
    inner_outline = [(y+(1.8 if y<110 else -1.8), z+(1.8 if z<155 else -1.8))
                     for y,z in light_outline]
    # Full colored boundary back-projected from video frame 30 onto the inclined
    # wing plane. Earlier endpoint-only fitting missed the broad trailing edge.
    wing = list(WING_OUTLINE)
    for side in (-1, 1):
        suffix = 'Left' if side < 0 else 'Right'
        direction = (side, 0, 0)
        closure=profile(side_outline,'YZ',(side*120,0,0),side*15)
        closure=closure.makeFillet(10,[e for e in closure.Edges if e.BoundBox.XLength>14.99])
        closure=closure.makeFillet(2.5,[e for e in closure.Edges if e.BoundBox.XLength<.01])
        b.add('SideClosure'+suffix, closure, GOLD, 'Sides')
        b.add('SideMechanicalBacking'+suffix, profile(inner_outline, 'YZ', (side*134, 0, 0), side*3), DARK, 'Sides', 'metal')
        side_frame = profile(side_outline, 'YZ', (side*135, 0, 0), side*4)
        side_frame=side_frame.makeFillet(10,[e for e in side_frame.Edges if e.BoundBox.XLength>3.99])
        aperture=profile(inner_outline, 'YZ', (side*134, 0, 0), side*6)
        aperture=aperture.makeFillet(6,[e for e in aperture.Edges if e.BoundBox.XLength>5.99])
        side_frame=side_frame.cut(aperture)
        side_frame=side_frame.makeFillet(1.3,[e for e in side_frame.Edges if e.BoundBox.XLength<.01])
        service_pocket=profile([(80.6,51.6),(118.4,52.6),(118.4,65.4),(80.6,64.4)],
                               'YZ',(side*137.8,0,0),side*2)
        service_pocket=service_pocket.makeFillet(.5,[e for e in service_pocket.Edges if e.BoundBox.XLength>1.99])
        side_frame=side_frame.cut(service_pocket)
        b.add('SideGuard'+suffix, side_frame, GOLD, 'Sides')
        shoe = crowned_plate([(81,52),(118,53),(118,65),(81,64)],
                             'YZ', (side*137.5, 0, 0), side*1.8, .35)
        b.add('SideFrameShoe'+suffix, shoe, (.42,.32,.15), 'Sides')
        for i, (y,z) in enumerate(((83,62),(115,62),(178,229),(70,223))):
            screw=b.bolt(f'SideFrameBolt{suffix}{i}', (side*139, y, z), direction, 1.7 if i<2 else 2.6)
            if i<2:
                if screw.ViewObject is not None:
                    screw.ViewObject.ShapeColor=(.12,.13,.12)
                    screw.ViewObject.LineColor=(.054,.0585,.054)
        # Source shows continuous curved bends, not mitered glowing sticks.
        # Work in final coordinates so the circular tube stays circular.
        lightface=profile([(y*1.25,z*.84+24) for y,z in light_outline],
                          'YZ',(side*139.5*.84,0,0),1)
        lightface=lightface.makeFillet(4,[e for e in lightface.Edges if e.BoundBox.XLength>.99])
        face=min([f for f in lightface.Faces if f.findPlane(1e-6) is not None
                  and abs(f.normalAt(0,0).x)>.99],key=lambda f:f.CenterOfMass.x)
        path=face.OuterWire
        edge=path.Edges[0]
        section=Part.Wire([Part.makeCircle(1.8,edge.Vertexes[0].Point,edge.tangentAt(edge.FirstParameter))])
        b.add('CyanSideTube'+suffix,path.makePipeShell([section],True,False),CYAN,'Details','emission')
        # World-space, source-fitted recessed circular assembly. A dark
        # projecting hub connects the recessed cone to the unchanged wing root.
        cx,cy,cz,lip_radius = 113.62074,129.09686,153.62312,53.78761
        radial_scale=lip_radius/54
        def ring_place(shape, axial_start):
            shape.Placement=App.Placement(App.Vector(side*axial_start,cy,cz),
                App.Rotation(App.Vector(0,0,1),vector(direction))).multiply(shape.Placement)
            return shape
        b.add('SpeakerBarrel'+suffix,ring(58*radial_scale,50*radial_scale,12,
              (side*100.8,cy,cz),direction),DARK,'Sides','metal')
        collar=round_loft([(0,58*radial_scale,0),(2.5,61*radial_scale,0),
                           (7,61*radial_scale,0),(10,58*radial_scale,0)])
        collar=collar.cut(cylinder(54*radial_scale,12,(0,0,-1)))
        scallops=[]
        for j in range(20):
            a=j*math.tau/20
            scallops.append(cylinder(2.3*radial_scale,12,
                (61*radial_scale*math.cos(a),61*radial_scale*math.sin(a),-1)))
        b.add('SpeakerScallopCollar'+suffix,ring_place(collar.cut(Part.makeCompound(scallops)),101.5),
              METAL,'Sides','metal')
        b.add('SpeakerRearSeal'+suffix,cylinder(61*radial_scale,1.6,(side*100.4,cy,cz),direction),
              DARK,'Sides','rubber')
        # Two source-visible curved plate segments; open staggered holes
        # replace the unsupported alternating screw heads of the old ring.
        flange,bridge_wires=perforated_side_flange(side,cy,cz,radial_scale)
        b.add('PerforatedSpeakerFlange'+suffix,flange,METAL,'Sides','metal')
        for i,wire in enumerate(bridge_wires):
            b.add(f'SpeakerBridgeWire{suffix}{i}',wire,RED,'Details','rubber')
        # The reference opening has a recessed wall around the axle; the old
        # solid cone exposed its broad planar cap and read as a flat disc.
        cone=Part.makeCone(44*radial_scale,31*radial_scale,10,
                          App.Vector(side*cx,cy,cz),vector((-side,0,0)))
        cavity=Part.makeCone(40.7*radial_scale,24*radial_scale,9.2,
                            App.Vector(side*(cx+.1),cy,cz),vector((-side,0,0)))
        b.add('SpeakerVisualCone'+suffix,cone.cut(cavity),DARK,'Sides','rubber')
        b.add('SpeakerOuterLip'+suffix,Part.makeTorus(lip_radius-5,5,
              App.Vector(side*cx,cy,cz),vector(direction)),(.10,.12,.12),'Sides','metal')
        b.add('SpeakerLipTrim'+suffix,Part.makeTorus(lip_radius-.8,.55,
              App.Vector(side*(cx+1),cy,cz),vector(direction)),(.32,.36,.35),'Sides','metal')
        b.add('SpeakerSurround'+suffix,Part.makeTorus(43.5*radial_scale,2.8*radial_scale,
              App.Vector(side*(cx-1.7),cy,cz),vector(direction)),DARK,'Sides','rubber')
        b.add('SpeakerCentre'+suffix,cylinder(18,5,(side*109,cy,cz),direction),DARK,'Sides','metal')
        b.add('SpeakerHubNeck'+suffix,cylinder(27,30,(side*107,126,151),direction),
              DARK,'Sides','metal')
        for i in range(6):
            lug=box(3.4,9,5.4,(cx-1.7 if side>0 else -cx-1.7,cy+46,cz-2.7),.8)
            lug.rotate(App.Vector(0,cy,cz),App.Vector(1,0,0),i*60+15)
            b.add(f'SpeakerRetainer{suffix}{i}',lug,(.20,.24,.24),'Sides','metal')
        crease = list(WING_CREASE)
        main_face = wing[:14]+crease[1:]
        blade = curved_wing_plate(wing,side*167,side*1)
        b.add('WingEdge'+suffix, blade, RED if side<0 else GOLD, 'Wings')
        raised=curved_wing_plate(main_face,side*168,side*3)
        b.add('WingRaisedFace'+suffix,raised,RED if side<0 else GOLD,'Wings')
        inset = [(83+(y-83)*.994,158+(z-158)*.994) for y,z in main_face]
        paint = curved_wing_plate(inset,side*170,side*3.5,.6)
        b.add('WingPaint'+suffix, paint, RED if side < 0 else GOLD, 'Wings')
        def boundary_y(path, height):
            for (y0,z0),(y1,z1) in zip(path,path[1:]):
                if z0 <= height <= z1:
                    return y0+(y1-y0)*(height-z0)/(z1-z0)
            raise ValueError('Wing fold section outside reference boundary')
        sections=[]
        for z in (174.4,193.27,224.39,248.67,286.70,335.21):
            front=boundary_y(crease,z);rear=boundary_y(wing[13:]+[wing[0]],z)
            vertices=[App.Vector(side*x,y,z) for x,y in ((167,front),(169.5,front),(168,rear),(167,rear))]
            sections.append(Part.makePolygon(vertices+[vertices[0]]))
        fold=Part.makeLoft(sections,True,True)
        b.add('WingFoldFacet'+suffix,fold,RED if side<0 else GOLD,'Wings')
        inside = curved_wing_plate(wing,side*166.4,side*.6)
        b.add('WingInnerPaint'+suffix, inside, RED if side < 0 else GOLD, 'Wings')
        # A tapered folded rib on the inward face catches light from the rear.
        spine = crowned_plate([(99,178),(110,204),(199,341),(202,350),(191,337),(106,201)],
                              'YZ', (side*166.4,0,0), -side*4.2, .7)
        b.add('WingSpine'+suffix, spine, RED if side < 0 else GOLD, 'Wings')
        b.add('WingHubSeat'+suffix, ring(26,21,3,(side*164,83,158),direction), SILVER, 'Wings','metal')
        # Distinctive diagonal markings on the upper wing.
        if side < 0:
            skins=[]
            for surface in (paint,raised,fold):
                outer=surface.copy();outer.translate(App.Vector(side*.3,0,0))
                skins.append(outer.cut(surface))
            coating=Part.makeCompound(skins)
            stripes=[[(162.34,306.51),(150.05,289.65),(167.96,248.06),(181.74,267.21)],
                     [(142.20,283.95),(135.67,275.14),(154.68,227.20),(163.96,240.48)]]
            for i,stripe in enumerate(stripes):
                stripe_shape=profile(stripe,'YZ',(side*157,0,0),side*19)
                b.add(f'WingStripe{suffix}{i}',coating.common(stripe_shape),WHITE,'Details')
        mark = cylinder(25,.3,(side*173.5,83,158),direction)
        pentagon=[(83+22*math.cos(math.radians(18+i*72)),158+22*math.sin(math.radians(18+i*72))) for i in range(5)]
        mark=mark.cut(profile(pentagon,'YZ',(side*173,0,0),side*2))
        for i in range(5):
            gap = box(8, 30, 3.8, (side*172-4, 83, 156.1))
            gap.rotate(App.Vector(side*172, 83, 158), App.Vector(1, 0, 0), i*72+18)
            mark = mark.cut(gap)
        b.add('WingHubMark'+suffix, mark, WHITE, 'Details')
        # Fixed side-plane outline from frame 180; opposite side is mirrored.
        arm=Part.Face(handle_arm_wire(side*112.32)).extrude(App.Vector(side*9.36,0,0))
        arm=arm.makeFillet(1.1,[e for e in arm.Edges if e.BoundBox.XLength<.01])
        # Normalize the fillet's trimmed surfaces before saved-BRep/STEP checks.
        with tempfile.TemporaryDirectory(prefix='vintrox-handle-') as folder:
            transfer=str(Path(folder)/'arm.step')
            arm.exportStep(transfer)
            arm=Part.read(transfer)
        b.add('HandleArm'+suffix,arm,(.28,.29,.27),'Wings','metal')
        inset_arm=Part.Face(handle_arm_wire(side*121.38,.94)).extrude(App.Vector(side*.5,0,0))
        b.add('HandleInset'+suffix,inset_arm,(.30,.31,.29),'Wings','metal')
        marks=[[(153.299,295.1532),(157.0917,298.2991),(172.1302,282.8133),(168.3688,279.6522)],
               [(147.5865,289.745),(151.3963,292.9061),(165.5414,277.834),(161.7608,274.6576)],
               [(142.3188,282.9682),(147.5763,287.056),(159.3937,273.2841),(146.0828,270.4156)]]
        for i,points in enumerate(marks):
            b.add(f'HandleMark{suffix}{i}',profile(points,'YZ',(side*121.78,0,0),side*.25),WHITE,'Details')
        end_envelope=Part.Face(handle_arm_wire(side*101)).extrude(App.Vector(side*18,0,0))
        cuff=box(8.32,46.8,32,(side*109.2-4.16,148.6,284),5).common(end_envelope)
        b.add('HandleGripCuff'+suffix,cuff,METAL,'Wings','metal')
        wire_paths=[(105,RED,[(73.58,114.3),(74.67,101.01),(79.38,95.29),(84.57,105.22),
                              (91.63,104.73),(93.51,91.01),(98.95,85.41),(102.87,92.43),(106.01,99.92)]),
                    (218,WHITE,[(71.66,121.94),(70.75,106.81),(74.64,96.53),
                                (86.46,92.59),(100.13,88.3),(111.01,91.53)]),
                    (230,(.30,.55,.70),[(70.15,214.12),(75.02,228.18),(83.74,234.06),
                     (91.19,232.16),(93.9,225.14),(89.95,219.47),(84.06,221.95),
                     (85.28,228.07),(95.49,230.15),(102.86,223.34),(121,210)])]
        for z,color,path in wire_paths:
            # Lower cables emerge forward of the ring; their ends return into
            # its depth. The upper coil sits in the recessed side-frame plane.
            x = 142 if z == 230 else 136/.84
            points = [(side*(113/.84 if z != 230 and i in (0,len(path)-1) else x),y,height)
                      for i,(y,height) in enumerate(path)]
            b.add(f'VisibleWire{suffix}{z}',tube(points,1.4),color,'Details','rubber')
    grip = box(224,37,30,(-112,104,302),11).fuse(box(190,37,33,(-95,104,302),11)).removeSplitter()
    b.add('HandleGrip',grip,(.24,.25,.23),'Wings','metal')
    for i in range(10):
        shade = 1+.025*math.sin(i*2.4)
        b.add(f'GripBand{i}',grip_wrap(i),tuple(c*shade for c in OLIVE),'Details','rubber')

    # Top slot and a slim instrumentation strip; the strip is a visual insert.
    slot_trim = box(134, 12, 3, (-67, 58, 274)).cut(box(124, 4, 5, (-62, 62, 273)))
    b.add('TopSlotTrim', slot_trim, DARK, 'Hull')
    access = box(164, 66, 4, (-82, 85, 274), 1.5)
    access = access.cut(box(146, 48, 2.5, (-73, 94, 276), 1))
    b.add('RoofAccessPanel', access, METAL, 'Hull', 'metal')
    for i, (x,y) in enumerate(((-77,90),(77,90),(-77,146),(77,146))):
        b.bolt(f'RoofAccessBolt{i}', (x,y,278), (0,0,1), 2.5)
    for i,y in enumerate((99,128)):
        b.add(f'RoofRaisedRib{i}', profile([(-63,276),(-56,282),(56,282),(63,276)],
              'XZ',(0,y,0),9),METAL,'Hull','metal')
    def on_slope(shape):
        transform=App.Matrix();transform.A11=157.53261522/156;transform.A22=20.51739159/28
        shape=shape.transformGeometry(transform)
        angle=36.61287666;rad=math.radians(angle);cy=12*transform.A22
        shape.rotate(App.Vector(),App.Vector(1,0,0),angle)
        shape.translate(App.Vector(0,48.33972247-cy*math.cos(rad)+4.2*math.sin(rad),
                                   252.35745666-cy*math.sin(rad)-4.2*math.cos(rad)))
        with tempfile.TemporaryDirectory(prefix='vintrox-instrument-') as folder:
            transfer=str(Path(folder)/'instrument.step');shape.exportStep(transfer);shape=Part.read(transfer)
        return shape
    b.add('TopInstrumentPanel', on_slope(box(152, 24, 3, (-76, 0, 0), 1)), DARK, 'Face')
    instrument_rim = box(156,28,1.4,(-78,-2,2.8),.6).cut(box(150,22,3,(-75,1,2),.5))
    b.add('InstrumentRim', on_slope(instrument_rim), SILVER,'Face','metal')
    # A stepped dark socket seats the rim below the surrounding rounded crown.
    # Dimensions are expressed in the pre-fit plane used by on_slope.
    scale_x=157.53261522/156;scale_y=20.51739159/28
    def socket_ring(w,h,inner_w,inner_h,z,depth):
        return box(w/scale_x,h/scale_y,depth,(-w/scale_x/2,12-h/scale_y/2,z)).cut(
            box(inner_w/scale_x,inner_h/scale_y,depth+2,(-inner_w/scale_x/2,12-inner_h/scale_y/2,z-1)))
    mount=socket_ring(162,25,154,17.8,-2.8,6.5).fuse(socket_ring(162,25,159,22,3.7,2)).removeSplitter()
    b.add('InstrumentMount',on_slope(mount),DARK,'Face','metal')
    for i in range(13):
        b.add(f'TopMeterGrid{i}',on_slope(box(.18,17,.18,(-65+i*10,3,3.05))),(.25,.16,.23),'Details','screen')
    for i in range(3):
        b.add(f'TopMeterRule{i}',on_slope(box(136,.18,.18,(-68,5+i*6,3.05))),(.25,.16,.23),'Details','screen')
    for i,color in enumerate(((.58,.18,.49),(.39,.31,.66))):
        points=[(-66+j*2,11+3*math.sin(j*.31+i*1.7)+1.8*math.sin(j*.77+i),3.45) for j in range(67)]
        b.add(f'TopMeterTrace{i}',on_slope(tube(points,.23)),color,'Details','screen')
    for i in range(7):
        b.add(f'TopMeterTick{i}',on_slope(box(1,.8,.3,(-64+i*21,20,3.1))),WHITE,'Details','screen')
    b.add('TopMeterLatch', on_slope(box(8, 7, 6, (-4, 20, 2), 1)), RED, 'Details')
    for i in range(COOLING_FINS):
        b.add(f'RearCoolingFin{i}',cooling_fin(-90.25+i*12.3),(.18,.19,.18),'Rear','cast_metal')
    b.add('RearCoolingCore',cooling_fin(-90.25,180.5,True),(.07,.08,.08),'Rear','ink')
    rear_light = rounded_frame(144, 110, 3, 3, (-72, 185, 70), 8)
    b.add('RearCyanFrame', rear_light, CYAN, 'Rear', 'emission')
    b.add('RearRecessLiner', box(140, 4, 106, (-70, 184, 72), 2).cut(bass_passage), DARK, 'Rear', 'metal')
    for side,color in ((1,(.30,.55,.70)),(-1,RED)):
        path=[(side*x,188,z) for x,z in ((64,165),(57,176),(48,173),(42,178),(28,174))]
        b.add(f'RearRecessWire{side:+}',tube(path,1.5),color,'Details','rubber')
        b.add(f'RearRecessCornerBoss{side:+}',ring(4,1.6,2.5,(side*64,188,174),(0,1,0)),METAL,'Details','metal')
    for side in (-1,1):
        suffix='Left' if side<0 else 'Right'
        cheek=[(side*x,z) for x,z in ((91,59),(116,50),(116,227),(100,227),(96,197),(96,91))]
        rear_cheek = profile(cheek,'XZ',(0,183,0),9)
        rear_cheek = rear_cheek.makeFillet(3.5,[e for e in rear_cheek.Edges if e.BoundBox.YLength>8.99])
        rear_cheek = rear_cheek.makeFillet(3.8,[e for e in rear_cheek.Edges if e.BoundBox.YLength<.01])
        b.add('RearArmourCheek'+suffix,rear_cheek,GOLD,'Rear')
        for i,z in enumerate((76,210)):
            b.bolt(f'RearArmourBolt{suffix}{i}',(side*107,192,z),(0,1,0),3)
    # Three-camera fitted rear insert, recessed in a rounded gold carrier.
    rail_w,rail_h,rail_y,rail_z=121.16123372,20.62114643,247.86106424,210.93081714
    carrier=box(185,21,44,(-92.5,227,191),8)
    carrier=carrier.cut(rounded_plate(rail_w+.5,rail_h+.5,5,(-rail_w/2-.25,245.5,rail_z-rail_h/2-.25),1.8))
    for side in (-1,1):
        slot=rounded_plate(13.5,2.8,2.1,(side*15.5-6.75,246.7,228),1.3)
        carrier=carrier.cut(slot)
        b.add(f'RearRailAntennaSlot{side:+}',rounded_plate(12.5,2,.3,(side*15.5-6.25,246.6,228.4),.9),(.16,.13,.07),'Rear','ink')
    b.add('RearRailCarrier',carrier,GOLD,'Rear')
    rail=rounded_plate(rail_w,rail_h,rail_y-245.3,(-rail_w/2,245.3,rail_z-rail_h/2),1.5)
    for i in range(7):
        x=42+i*2.25
        rail=rail.cut(rounded_plate(1.05,14.8,1.8,(x-.525,246.6,203.6),.5))
        b.add(f'RearRailVent{i}',rounded_plate(.8,14.2,.25,(x-.4,246.5,203.9),.35),(.025,.025,.023),'Rear','ink')
    b.add('RearPortRail',rail,(.10,.105,.10),'Rear','cast_metal')
    slider_seat=rounded_plate(87,6.5,1.7,(-50,247.4,207.5),.7)
    slider_seat=slider_seat.cut(rounded_plate(84.8,4.8,1.2,(-48.9,248.3,208.35),.35))
    b.add('RearRailBezel',slider_seat,(.32,.27,.13),'Rear','metal')
    slider=[(-48.5,213.2),(35.5,213.2),(35.5,208.5),(-21,208.5),
            (-23,209.8),(-45.5,209.8),(-46.3,209),(-48.5,209)]
    b.add('RearRedInsert',profile(slider,'XZ',(0,248.2,0),1.65),(.48,.18,.18),'Rear','paint')
    b.add('RearRailIndex',box(3.2,.16,4.7,(-.6,249.8,208.5)),WHITE,'Details')
    latch=profile([(-20,200.2),(20,200.2),(17,197.2),(-17,197.2)],'XZ',(0,247.2,0),1.2)
    latch=latch.cut(profile([(-17.5,199.6),(17.5,199.6),(16.3,198),(-16.3,198)],'XZ',(0,248,0),1))
    b.add('RearRailLatch',latch,(.43,.36,.19),'Rear','metal')
    for side in (-1,1):
        x=side*52.3
        b.add(f'RearRailStatusBase{side:+}',rounded_plate(10,3.3,1.2,(x-5,247.1,195.9),1.5),DARK,'Rear')
        b.add(f'RearRailStatusLens{side:+}',rounded_plate(7.8,1.9,.8,(x-3.9,248.1,196.6),.8),(.95,.28,.32),'Rear','red_light')
        b.add(f'RearRailStatusIndex{side:+}',box(1.2,.15,1.7,(x-.6,248.85,196.7)),WHITE,'Details')
    # Circular body sections and conforming broad rings; retain lens centre datum.
    for side in (-1,1):
        x=side*92.4
        axis=App.Vector(0,1,0)
        rot=App.Rotation(App.Vector(0,0,1),axis)
        base=round_loft([(0,15.5,0),(13,15.3,0),(33.5,14.7,0)])
        base.Placement=App.Placement(App.Vector(x,205,241),rot)
        b.add(f'RearBeaconBase{side:+}',base,GOLD,'Rear')
        stations=[(0,14.7,0),(5,14.3,0),(11,12.3,0),(17,9.6,0),(22.5,6.3,0)]
        beacon=round_loft(stations)
        coating=round_loft([(z,r+.18,dy) for z,r,dy in stations]).cut(
            round_loft([(z,r-1,dy) for z,r,dy in stations]))
        beacon.Placement=App.Placement(App.Vector(x,238.5,241),rot)
        b.add(f'RearBeacon{side:+}',beacon,(.95,.20,.25),'Rear','red_light')
        for j,(start,depth) in enumerate(((.2,2.4),(8,3),(17,2.8))):
            band=coating.common(cylinder(20,depth,(0,0,start)))
            band.Placement=App.Placement(App.Vector(x,238.5,241),rot)
            b.add(f'RearBeaconBand{side:+}_{j}',band,(.045,.035,.035),'Rear','metal')
        lens=Part.makeSphere(6.3,App.Vector(x,261,241)).common(box(14,7,14,(x-7,261,234)))
        b.add(f'RearBeaconLens{side:+}',lens,(.99,.40,.44),'Rear','red_light')
    # Bulged transition fairing and separately modelled curved exhaust petals.
    axis = bass_axis
    origin = bass_origin
    rot = App.Rotation(App.Vector(0, 0, 1), axis)
    def place(shape):
        shape.Placement = App.Placement(origin, rot).multiply(shape.Placement)
        return shape
    fairing=nozzle_fairing_parts()
    # The dark band around the nozzle is a recessed housing shadow.  Contract
    # the actual fairing separately so it does not become a continuous tube
    # wall around the nozzle mouth.
    b.add('BassNozzleShell',place(contract_nozzle_radial(
        fairing['BassNozzleShell'].copy(), NOZZLE_SHELL_RADIAL_SCALE)),(.52,.37,.21),'Rear')
    b.add('BassNozzleRearCollar', place(ring(55, 45, 8, (0, 0, -3))), METAL, 'Rear', 'metal')
    b.add('BassChamberBackplate', place(cylinder(45, 4, (0, 0, 5))), DARK, 'Rear', 'metal')
    lip=nozzle_lip_parts()
    b.add('BassNozzleMouthRing', place(lip['BassNozzleMouthRing']), METAL, 'Rear', 'metal')
    b.add('BassNozzleRolledLip',place(lip['BassNozzleRolledLip']),(.52,.37,.21),'Rear')
    for i in range(6):
        clamp=box(9,8,13,(-4.5,49,-2),1.5)
        clamp.rotate(App.Vector(),App.Vector(0,0,1),i*60)
        b.add(f'NozzleRootClamp{i}',place(clamp),METAL,'Rear','metal')
    b.add('BassSpeakerGasket', place(lip['BassSpeakerGasket']), DARK, 'Rear', 'rubber')
    inner = interior_parts(recessed=True)
    b.add('BassVisualCone',place(contract_nozzle_radial(inner['BassVisualCone'])),DARK,'Rear','rubber')
    b.add('BassDustCap',place(contract_nozzle_radial(inner['BassDustCap'])),DARK,'Rear','rubber')
    # Terminal circle comes from 19 pixels across three fixed reference views.
    # Each petal curves inward and its final section tilts gently relative to
    # the gold fairing axis; this is geometry, not a render-space deformation.
    b.add('BassInnerThroat',place(contract_nozzle_radial(inner['BassInnerThroat'])),DARK,'Rear','rubber')
    for i in range(NOZZLE_PETALS):
        for name,shape in nozzle_leaf_parts(i).items():
            if name==f'NozzlePetal{i}':color,category=(.27,.28,.27),'Rear'
            elif name.startswith('NozzlePetalInset'):color,category=(.07,.08,.075),'Details'
            elif name.startswith('NozzlePetalRidge'):color,category=(.39,.41,.38),'Details'
            elif name.startswith('NozzlePetalEdgeRail'):color,category=(.53,.54,.50),'Details'
            elif name.startswith('NozzlePetalGuide'):color,category=(.58,.59,.54),'Details'
            else:color,category=(.49,.50,.46),'Details'
            b.add(name,place(contract_nozzle_radial(
                contract_nozzle_petal_tangential(
                    shape, i, preserve_root=(name == f'NozzlePetal{i}')),
                preserve_root=(name == f'NozzlePetal{i}'))),
                color,category,'metal')
        hinge=root_shifted_hinge(i)
        b.add(f'NozzlePetalHinge{i}',place(contract_nozzle_petal_tangential(
            hinge, i)),(.30,.32,.29),'Details','metal')
    # Projected surface patches remain in contact with the revised fairing.
    for name,shape in fairing.items():
        if name=='BassNozzleShell':continue
        color=RED if name in ('BassWarningRedBand','BassWarningTriangleInset') else WHITE
        b.add(name,place(contract_nozzle_radial(
            shape.copy(), NOZZLE_SHELL_RADIAL_SCALE)),color,'Details')
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
    if reserve.ViewObject is not None: reserve.ViewObject.Transparency = 70
    # Four-view terminal-circle fit; shell and petals share a real oblique axis.
    for side in (-1, 1):
        direction = App.Vector(side*.70841617, -.15711996, -.68808419)
        direction.normalize()
        terminal = App.Vector(side*121.2565, 62.9651, 21.4892)
        p = terminal-direction*53
        placement = App.Placement(p, App.Rotation(App.Vector(0, 0, 1), direction))
        def lower_place(shape):
            shape.Placement = placement.multiply(shape.Placement)
            return shape
        shell = round_loft([(0, 18, 0), (10, 24, 0), (27, 28, 0), (37, 27, 0)])
        shell = shell.cut(round_loft([(-1, 14, 0), (10, 20, 0), (27, 24, 0), (39, 23, 0)]))
        b.add(f'LowerPod{side:+}', lower_place(shell), (.52,.34,.19), 'Hull')
        b.add(f'LowerPodClamp{side:+}',lower_place(ring(20.5,17,4,(0,0,3))),METAL,'Hull','metal')
        b.add(f'LowerPodRim{side:+}', lower_place(Part.makeTorus(27.5,.8,App.Vector(0,0,36))), (.40,.37,.30), 'Hull', 'metal')
        b.add(f'LowerPodDiaphragm{side:+}', lower_place(cylinder(21.5, 2, (0,0,44))), DARK, 'Hull', 'rubber')
        for i in range(18):
            sections = [(30,27.5,24.8), (40,25.8,23.1), (53,20.53624,18.1)]
            rib = Part.makeLoft([sector_wire(ro, ri, z, i*20+1.5, i*20+18.5) for z,ro,ri in sections], True, False)
            recess = Part.makeLoft([sector_wire(ro+1,ro-.7,z,i*20+4,i*20+16)
                                    for z,ro in [(32,27.4),(40,25.8),(51,21.6)]],True,False)
            b.add(f'LowerPodRib{side:+}_{i}', lower_place(rib.cut(recess)), (.13,.12,.10), 'Details', 'metal')
            ridge = Part.makeLoft([sector_wire(ro+.5, ro, z, i*20+8, i*20+10) for z,ro,ri in sections], True, False)
            b.add(f'LowerPodPetalRidge{side:+}_{i}', lower_place(ridge), (.35,.34,.30), 'Details', 'metal')
            for edge in (2.2,17.8):
                a=math.radians(i*20+edge)
                points=[(ro*math.cos(a),ro*math.sin(a),z) for z,ro,_ in sections]
                b.add(f'LowerPodEdgeRail{side:+}_{i}_{int(edge)}',lower_place(tube(points,.35)),(.48,.47,.43),'Details','metal')
    # Existing decorative cable loops stay above the new support plane.
    for i, x in enumerate((-44.5, 44.5)):
        path=[(x,72.8,57),(x,72.79,43.28),(x,72.66,28.78),(x,79.02,14.23),
              (x,90.8,4.28),(x,105.26,4.96),(x,117.52,9.58),(x,124.96,19.42),
              (x,127.11,33.41),(x,126.62,47.15),(x,126.6,57)]
        b.add(f'UnderbodyLoop{i}',tube(path,UNDERBODY_LOOP_RADIUS),DARK,'Details','cable')
    add_central_support(b)
    # Two recessed belly plates flank the shaft roots without obstructing them.
    for side in (-1,1):
        suffix='Left' if side<0 else 'Right'
        x=-94 if side<0 else 62
        b.add('BellyServicePlate'+suffix,box(32,59,3,(x,68,10),1),METAL,'Hull','metal')
        for i,y in enumerate((74,121)):
            b.bolt(f'BellyServiceBolt{suffix}{i}',(x+16,y,10),(0,0,-1),2.6)
    b.add('AntennaBase', cylinder(5, 9, (0, 195, 248)), DARK, 'Details', 'rubber')
    b.add('Antenna', tube([(0, 195, 257), (0, 199, 316), (0, 213, 351), (0, 229, 405)], 1.1), DARK, 'Details', 'rubber')
    for side in (-1, 1):
        suffix='Left' if side<0 else 'Right'
        crown=doc.getObject('HoodShoulderCrown'+suffix).Shape
        outer=crown.copy();outer.translate(App.Vector(side*.25,0,0))
        coating=outer.cut(crown)
        for i in range(4):
            y=-4+i*9
            stencil=profile([(y,248),(y+4,248),(y+11,232),(y+7,232)],'YZ',(side*118,0,0),side*10)
            b.add(f'HoodMark{side:+}_{i}',coating.common(stencil),WHITE,'Details')
    # Hidden CD envelope shows the assumed clear insertion path, not validated travel.
    # CD plane is XZ for the top slot, normal is Y.
    disc = cylinder(60, 1.2, (0, 63, 338), (0, 1, 0))
    b.add('CDInsertionStudy_D120', disc, SILVER, 'Reservations', visible=False)
    refine_reference_proportions(b)
    for name, shape in gold_wing_fold_parts().items():
        doc.getObject(name).Shape = shape
    # Trim exposed grip ends into the sloping shoulders; retain the central wrap.
    grip=doc.getObject('HandleGrip')
    keep=box(202,100,100,(-101,125,260))
    for side in (-1,1):
        keep=keep.fuse(Part.Face(handle_arm_wire(side*101)).extrude(App.Vector(side*18,0,0)))
    grip.Shape=grip.Shape.common(keep)
    # Recess the speaker assembly into the separate side cladding, while the
    # continuous main enclosure remains closed behind its dark rear seal.
    for side,suffix in ((-1,'Left'),(1,'Right')):
        pocket=cylinder(64,17,(side*100,129.09686,153.62312),(side,0,0))
        for prefix in ('SideClosure','SideMechanicalBacking'):
            obj=doc.getObject(prefix+suffix)
            obj.Shape=obj.Shape.cut(pocket)
            if not obj.Shape.isValid() or not obj.Shape.Solids:
                raise ValueError('Invalid side ring pocket: '+obj.Name)
    add_sloping_rear_closure(b)
    add_reference_side_modules(b)
    refine_side_cladding(b)
    reproject_side_cladding(b)
    pan=doc.getObject('ClosedBellyPan')
    pan.Shape=relieved_belly(pan.Shape,52.5,32)
    for obj in b.items:
        if obj.Name.startswith(('BellyServicePlate','BellyServiceBolt')):
            obj.Shape=moved_service_shape(obj.Shape,-1 if 'Left' in obj.Name else 1,52.5,
                                          is_bolt=obj.Name.startswith('BellyServiceBolt'))
    info = doc.addObject('App::FeaturePython', 'ConceptStatus')
    info.Label = chinese_label('ConceptStatus')
    info.addProperty('App::PropertyString', 'Scope')
    info.Scope = '外形评审草模；非打印分件包；无内部硬件装配验证；实测平面屏与曲面透明罩示意；光学/工艺未验证；低音D88×40是假设占位'
    info.addProperty('App::PropertyString', 'ParameterWorkflow')
    info.ParameterWorkflow = '屏幕对象绑定参数表；装甲等造型由生成脚本重建，不是全模型参数联动'
    doc.recompute()
    if frame_view:
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
    # Trimmed affine B-splines can have distant control poles; measure surfaces.
    bbox = Part.makeCompound([o.Shape for o in visible]).optimalBoundingBox(False, False)
    nozzle_axis=App.Vector(0,.574,-.819);nozzle_axis.normalize()
    nozzle_frame=App.Placement(App.Vector(0,180,173),App.Rotation(App.Vector(0,0,1),nozzle_axis))
    local_patches={}
    for name in ('BassWarningPlaque','BassWarningTriangleInset'):
        local=doc.getObject(name).Shape.copy()
        local.Placement=nozzle_frame.inverse().multiply(local.Placement)
        local_patches[name]=local
    label_metadata=warning_label_positions(local_patches)
    manifest = {
        'revision': 'v57-nozzle-shell-shadow-contract',
        'belly_relief': {'outer_floor_z_mm':52.5,'central_strip_width_mm':64,'outer_flat_start_x_mm':62,'basis':'appearance-derived closed lower shell; support geometry retained, no load validation'},
        'nozzle_marking_spec': MARKING_SPEC,
        'rear_shoulder_section_exponent': 1.5,
        'gold_wing_crease_offsets_local_y_mm': list(GOLD_WING_CREASE_OFFSETS),
        'petal_recess_stations_mm': [shifted_z(99.5,1),shifted_z(127.0,1)],
        'petal_recess_corner_radius_mm': 1.0,
        'petal_inset_window_degrees': [4.4, 18.1],
        'nozzle_radial_scale': NOZZLE_RADIAL_SCALE,
        'nozzle_shell_radial_scale': NOZZLE_SHELL_RADIAL_SCALE,
        'nozzle_petal_tangential_scale': NOZZLE_PETAL_TANGENTIAL_SCALE,
        'rear_lower_edge_rise_mm': 6,
        'nozzle_lip_parameters_mm': {'gold_major_radius':52.82+ROOT_DELTA[1],'gold_minor_radius':1.0,'gold_station':95.6+ROOT_DELTA[0],'metal_major_radius':52.3215+ROOT_DELTA[1],'metal_minor_radius':1.0,'metal_station':96.8067+ROOT_DELTA[0],'gasket_outer_radius':52.5+ROOT_DELTA[1]},
        'nozzle_root_profile': {'local_delta_z_radius_y_tilt':list(ROOT_DELTA),'guide_span_degrees':5.4,'terminal_circle_preserved':True,'basis':'five fixed video views; manual root centreline observations'},
        'nozzle_mid_depth_reduction_mm': 3,
        'fairing_root_blend_power': 4,
        'fairing_middle_depth_extra_mm': 4,
        'fairing_shoulder_inset_mm': 6,
        'fairing_lower_inset_mm': 0,
        'nozzle_interior': {'throat_end_station_before_root_map_mm':112,'bowl_depth_mm':23,'bowl_radial_wall_mm':1,'back_plate_mm':1,'basis':'appearance-only recessed bowl; hidden speaker hardware unselected'},
        'side_profile_reprojection': {'outer_x_mm':108.0,'scale':1.0089049846660512,'eye_mm':[1100.478706826763,481.9590609254328,317.0386845391606]},
        'tree_structure': 'flat', 'group_count': 0,
        'status': 'appearance-study-only', 'physical_tests': False,
        'screen_panel_mm': [210, 160, 2], 'active_area_mm': [200, 150],
        'bass_axis': [0, .574, -.819],
        'bass_origin_mm': [0, 180, 173],
        'nozzle_petals': NOZZLE_PETALS,
        'rear_cavity': {'aperture_mm': [138,116], 'back_y_mm':223,
                        'lip_y_mm':247, 'light_front_y_mm':241.2,
                        'basis':'appearance assumption; recessed housing shadow is not a continuous nozzle wall'},
        **label_metadata,
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
        view=getattr(obj,'ViewObject',None)
        color=list(view.ShapeColor[:3]) if view is not None else list(getattr(obj,'ShapeColor',GOLD))
        meshes.append({'name': obj.Name, 'vertices': [[v.x, v.y, v.z] for v in vertices],
                       'faces': faces, 'color': color,
                       'material': getattr(obj, 'RenderMaterial', 'paint')})
    meshfile = Path(tempfile.gettempdir())/'vintrox-drone-render-meshes.json'
    meshfile.write_text(json.dumps({'fcstd_sha256': manifest['fcstd_sha256'],
                                   'bass_axis': manifest['bass_axis'],
                                   'bass_origin_mm': manifest['bass_origin_mm'],
                                   'bass_warning_label_local_mm': manifest['bass_warning_label_local_mm'],
                                   'bass_alert_local_mm': manifest['bass_alert_local_mm'],
                                   'bass_warning_text_size_mm': manifest['bass_warning_text_size_mm'],
                                   'bass_alert_text_size_mm': manifest['bass_alert_text_size_mm'], 'objects': meshes}))
    print(json.dumps({'saved': str(path), 'visible_features': len(visible), 'bbox_mm': manifest['bbox_mm'],
                      'meshfile': str(meshfile)}, ensure_ascii=False))
    return doc
