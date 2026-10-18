"""Native FreeCAD expressions; no Python feature proxy is needed to reopen/edit."""
from pathlib import Path
import json
import FreeCAD as App
import FreeCADGui as Gui
import Part
from importlib.util import module_from_spec, spec_from_file_location

_checks_spec = spec_from_file_location('vintrox_layout_checks', Path(__file__).with_name('layout_checks.py'))
_checks = module_from_spec(_checks_spec)
_checks_spec.loader.exec_module(_checks)
physical, validate = _checks.physical, _checks.validate

PARAMETERS = [
    ('ScreenW', 210, '屏幕面板总宽', '用户测量口述；2026-10-18'),
    ('ScreenH', 160, '屏幕面板总高', '用户确认160；更正原报60；2026-10-18'),
    ('ScreenT', 2, '屏幕本体厚', '用户测量口述；不含背面排线电路板'),
    ('RibbonW', 10, '背面左侧排线电路板宽', '用户更正为左侧；完全位于面板210mm宽度内'),
    ('RibbonT', 2.4, '排线电路板自身厚度', '用户确认板自身厚度；非组合总厚度'),
    ('RibbonTopGap', 10, '排线板距屏幕上边缘', '用户口述；上下各10mm'),
    ('RibbonBottomGap', 10, '排线板距屏幕下边缘', '用户口述；上下各10mm'),
    ('RibbonGap', 0, '排线板与屏幕背面间隙', '未测；暂取0作贴背占位，不是实测'),
    ('ActiveW', 200, '显示可视区宽', '用户指定建模尺寸；2026-10-18；非独立实测记录'),
    ('ActiveH', 150, '显示可视区高', '用户指定建模尺寸；2026-10-18；居中为布局假设'),
    ('SideBorder', 12, '面板两侧结构余量', '设计假设；非实测'),
    ('LowerBand', 38, '下部控件区高度', '设计假设'),
    ('TopBand', 14, '顶部余量', '设计假设'),
    ('Wall', 8, '木壳占位壁厚', '设计假设；无强度结论'),
    ('CornerR', 22, '木壳正面轮廓圆角', '造型假设；内圆角=外圆角-壁厚'),
    ('EdgeR', 2, '木壳前后口沿软化半径', '造型假设；非加工工艺确认'),
    ('BezelExtra', 2, '黑框总宽相对面板增量', '造型假设'),
    ('BezelExtraH', 8, '黑框总高相对面板增量', '造型假设'),
    ('BezelR', 12, '黑框外轮廓圆角', '造型假设；可视窗口保留完整矩形'),
    ('BezelGap', 1, '木壳与黑框单侧阴影缝', '造型假设；非公差'),
    ('BezelInset', 2.5, '黑框前表面内嵌深度', '造型假设'),
    ('BezelT', 3, '黑框厚', '占位假设；材料未选'),
    ('BaseH', 12, '内缩底座高', '造型假设；承重/稳固未验证'),
    ('BaseInsetX', 22, '底座左右内缩量', '造型假设'),
    ('BaseInsetY', 18, '底座前后内缩量', '造型假设'),
    ('BaseR', 8, '底座平面圆角', '造型假设'),
    ('GrilleR', 12, '侧面格栅轮廓圆角', '造型假设；声学开口待验证'),
    ('BoardEdgeGap', 6, '后上方板卡相对内壁退让', '为圆角内腔预留；安装仍未验证'),
    ('BoardTopGap', 9, '后上方板卡距顶板内面的距离', '布局假设'),
    ('Depth', 160, '机身深度', '布局假设；待优化'),
    ('DriveW', 128, '光驱横向宽', '假设；非UJ-898实测/规格'),
    ('DriveH', 128, '竖装光驱高', '假设；非UJ-898实测/规格'),
    ('DriveT', 13, '光驱厚', '假设；待测'),
    ('DriveY', 22, '光驱前表面距前面', '设计假设'),
    ('DriveTopGap', 4, '光驱与顶板内面间隙', '假设；导向结构未设计'),
    ('SlotW', 124, '顶部槽口长', '视觉假设；不可据此加工'),
    ('SlotT', 4, '顶部槽口宽', '视觉假设；不可据此加工'),
    ('SpeakerT', 55, '单箱横向厚', '纯占位假设；非整组尺寸拆半'),
    ('SpeakerD', 105, '单箱前后深', '纯占位假设；待测独立音箱'),
    ('SpeakerH', 115, '单箱高', '占位假设；仅参考整组图高度'),
    ('SpeakerY', 38, '音箱前缘', '设计假设'),
    ('SpeakerZ', 60, '音箱底高', '设计假设'),
    ('SideGap', 2, '音箱与侧壁内面的距离', '静态假设；非隔振验证'),
    ('BatteryW', 120, '电池占位宽', '假设；未定型号/串数/容量'),
    ('BatteryD', 75, '电池占位深', '假设；未定型号'),
    ('BatteryH', 32, '电池占位高', '假设；未定型号'),
    ('BatteryY', 40, '电池前缘', '设计假设'),
    ('BatteryZ', 12, '电池底高', '设计假设；安装件待设计'),
    ('PiW', 85, 'Pi区域宽', '粗略占位；未核对本机及连接器'),
    ('PiD', 65, 'Pi板面第二边（竖放后沿Z）', '原包络旋转；不代表孔位规格'),
    ('PiH', 25, 'Pi及散热区厚（竖放后沿Y）', '假设；散热器未定'),
    ('PiY', 57, 'Pi前缘', '设计假设'),
    ('PiZ', 60, 'Pi底高', '设计假设；支架未设计'),
    ('DiskW', 100, '硬盘占位宽', '假设；未确认SSK型号'),
    ('DiskT', 20, '硬盘占位厚', '假设'),
    ('DiskH', 125, '硬盘竖放高度', '假设；姿态/振动未实测'),
    ('DiskZ', 50, '硬盘底高', '设计假设'),
    ('RearGap', 10, '硬盘距后盖内面', '假设；不代表插头足够'),
    ('DriverW', 80, '屏幕驱动板宽', '假设'),
    ('DriverT', 6, '屏幕驱动板厚', '假设；未计完整接口'),
    ('DriverH', 45, '屏幕驱动板高', '假设'),
    ('HubW', 50, '有源Hub宽', '假设；未选型'),
    ('HubD', 70, 'Hub长边（竖放后沿Z）', '原包络旋转；未选型'),
    ('HubH', 22, 'Hub厚（竖放后沿Y）', '假设；未选型'),
    ('HubY', 90, '竖放Hub前缘', '设计假设'),
    ('HubZ', 80, '竖放Hub底高', '设计假设；安装架未设计'),
    ('AmpW', 50, '功放占位宽', '假设；未选板卡'),
    ('AmpD', 25, '功放占位深', '假设'),
    ('AmpH', 20, '功放占位高', '假设'),
    ('DacW', 60, 'DAC及线路分配占位宽', '假设；未定电路'),
    ('DacD', 25, 'DAC占位深', '假设'),
    ('DacH', 16, 'DAC占位高', '假设'),
    ('PowerW', 70, 'PD/充电/电源路径/稳压区宽', '综合占位；不代表单个成品模块'),
    ('PowerD', 24, '电源区深', '假设；未选型'),
    ('PowerH', 28, '电源区高', '假设'),
    ('CableLaneD', 8, '后部线束通道深', '空间提示；未按连接器验证'),
]

WOOD = (0.42, 0.255, 0.14)
DARK = (0.065, 0.074, 0.082)
BRASS = (0.72, 0.53, 0.27)

def build(root):
    root = Path(root)
    out = root / 'cad'
    out.mkdir(exist_ok=True)
    (out / 'previews').mkdir(exist_ok=True)
    # Create a fresh document; never close or replace an existing user's document.
    doc = App.newDocument('VINTROX_Layout')
    doc.Label = 'VINTROX One — 圆润木壳 / 黑色内嵌框 / 悬浮底座 / 160mm / 假设 / 不可加工'
    params = doc.addObject('Spreadsheet::Sheet', 'Parameters')
    params.Label = '00 参数表（mm；用户测量与设计假设分列）'
    for col, title in zip('ABCD', ['参数别名', '数值（mm）', '含义', '依据与状态']):
        params.set(col+'1', title)
    for row, (alias, value, desc, state) in enumerate(PARAMETERS, 2):
        params.set('A'+str(row), alias)
        params.set('B'+str(row), str(value))
        params.setAlias('B'+str(row), alias)
        params.set('C'+str(row), desc)
        params.set('D'+str(row), state)
    row = len(PARAMETERS)+3
    for alias, expr, desc in [
        ('Width', '=ScreenW + 2 * SideBorder', '机身宽（随屏幕宽联动）'),
        ('Height', '=ScreenH + LowerBand + TopBand', '木壳高（不含底座）'),
        ('BezelW', '=ScreenW + BezelExtra', '黑框外宽'),
        ('BezelH', '=ScreenH + BezelExtraH', '黑框外高'),
        ('BezelZ', '=LowerBand - BezelExtraH / 2', '黑框底高'),
        ('OverallH', '=Height + BaseH', '含底座总高'),
        ('RibbonH', '=ScreenH - RibbonTopGap - RibbonBottomGap', '排线板高（由用户尺寸推导）'),
        ('ScreenAssemblyT', '=ScreenT + RibbonGap + RibbonT', '屏幕局部组合厚度（含未测间隙假设）'),
    ]:
        params.set('A'+str(row), alias)
        params.set('B'+str(row), expr)
        params.setAlias('B'+str(row), alias)
        params.set('C'+str(row), desc)
        params.set('D'+str(row), '派生布局尺寸；不是实测/加工尺寸')
        row += 1
    params.setColumnWidth('A', 155)
    params.setColumnWidth('B', 110)
    params.setColumnWidth('C', 255)
    params.setColumnWidth('D', 380)
    params.setStyle('A1:D1', 'bold', 'add')
    params.setBackground('A1:D1', (0.19, 0.25, 0.29))
    params.setForeground('A1:D1', (1., 1., 1.))
    doc.recompute()
    groups = {}
    for name, label in [('Enclosure', '01 木壳与可拆后盖（概念）'), ('Hardware', '02 硬件占位（非精确零件）'), ('Details', '03 外观控件与格栅（示意）'), ('Clearances', '04 净空提示（默认隐藏）'), ('Presentation', '05 剖视展示（非额外零件）'), ('Construction', '99 布尔辅助体（隐藏）')]:
        groups[name] = doc.addObject('App::DocumentObjectGroup', name)
        groups[name].Label = label
    def E(expr):
        import re
        return re.sub(r'\b([A-Z][A-Za-z0-9]*)\b', lambda m: 'Parameters.'+m.group(1), str(expr))
    def tag(o, note):
        o.addProperty('App::PropertyString', 'EvidenceStatus', 'Layout')
        o.EvidenceStatus = 'ASSUMED / 未实测 / CONCEPT ONLY'
        o.addProperty('App::PropertyString', 'LayoutNote', 'Layout')
        o.LayoutNote = note
    def box(name, label, dims, pos, color=DARK, group='Hardware', note='假设尺寸占位；无固定孔、线缆或热验证'):
        o = doc.addObject('Part::Box', name)
        o.Label = label
        for key, expr in zip(('Length', 'Width', 'Height'), dims):
            o.setExpression(key, E(expr))
        for key, expr in zip(('x', 'y', 'z'), pos):
            o.setExpression('Placement.Base.'+key, E(expr))
        o.ViewObject.ShapeColor = color
        o.ViewObject.LineColor = (0.10, 0.08, 0.06)
        tag(o, note)
        groups[group].addObject(o)
        return o
    def cut(name, label, base, tool, color=WOOD):
        o = doc.addObject('Part::Cut', name)
        o.Label = label
        o.Base, o.Tool = base, tool
        tag(o, '概念开口；不可作为加工尺寸')
        o.ViewObject.ShapeColor = color
        o.ViewObject.LineColor = (0.12, 0.08, 0.04)
        groups['Enclosure'].addObject(o)
        base.Visibility = tool.Visibility = False
        return o
    def rounded(name, label, dims, pos, radius, axis, color=WOOD, group='Construction'):
        """Native PartDesign primitives/fillets; no Python proxy or edge tuple mutation."""
        body = doc.addObject('PartDesign::Body', name)
        body.Label = label
        blank = body.newObject('PartDesign::AdditiveBox', name+'Blank')
        blank.Label = label+' / 原始体'
        for key, expr in zip(('Length','Width','Height'), dims):
            blank.setExpression(key,E(expr))
        for key, expr in zip(('x','y','z'), pos):
            blank.setExpression('Placement.Base.'+key,E(expr))
        doc.recompute()
        selected = []
        for index, edge in enumerate(blank.Shape.Edges, 1):
            bb = edge.BoundBox
            lengths = [bb.XLength, bb.YLength, bb.ZLength]
            if lengths[axis] > 1e-6 and all(lengths[k] < 1e-6 for k in range(3) if k != axis):
                selected.append('Edge'+str(index))
        fillet = body.newObject('PartDesign::Fillet', name+'Round')
        fillet.Base = (blank,selected)
        fillet.setExpression('Radius',E(radius))
        body.Tip = fillet
        for obj in (body,fillet):
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.LineColor = tuple(c*0.65 for c in color)
        tag(body, '参数化轮廓圆角；假设尺寸；非加工或材料验证')
        groups[group].addObject(body)
        blank.Visibility = False
        doc.recompute()
        return body

    outer = rounded('OuterProfile', '连续圆角木壳外轮廓', ('Width','Depth','Height'), (0,0,0), 'CornerR', 1)
    rim_edges = ['Edge'+str(i) for i,e in enumerate(outer.Shape.Edges,1) if e.BoundBox.YLength < 1e-6]
    profile_tip = outer.Tip
    eased = outer.newObject('PartDesign::Fillet', 'OuterEased')
    eased.Label = '木壳前后口沿软化'
    eased.Base = (profile_tip,rim_edges)
    eased.setExpression('Radius',E('EdgeR'))
    eased.ViewObject.ShapeColor = WOOD
    eased.ViewObject.LineColor = tuple(c*0.65 for c in WOOD)
    outer.Tip = eased
    profile_tip.Visibility = False
    doc.recompute()
    inner = rounded('InnerCavity', '圆角内腔 / 后方敞开', ('Width-2*Wall','Depth-Wall+1','Height-2*Wall'), ('Wall','Wall','Wall'), 'CornerR-Wall', 1)
    main = cut('HollowShell', '木壳空腔', outer, inner)
    opening = rounded('BezelOpening', '黑框阴影缝开口', ('BezelW+2*BezelGap','Wall+2','BezelH+2*BezelGap'), ('(Width-BezelW)/2-BezelGap',-1,'BezelZ-BezelGap'), 'BezelR+BezelGap', 1)
    main = cut('ShellFront', '木壳前部开口', main, opening)
    slot = rounded('SlotTool', '顶部圆角进碟槽 / 待验证', ('SlotW','SlotT','Wall+2'), ('(Width-SlotW)/2','DriveY+DriveT/2-SlotT/2','Height-Wall-1'), 'SlotT*0.375', 2)
    main = cut('ShellSlotted', '木壳顶部进碟槽', main, slot)
    slot_pocket = rounded('SlotPocket', '顶部槽口内衬浅槽 / 示意', ('SlotW+4','SlotT+3',2), ('(Width-SlotW-4)/2','DriveY+DriveT/2-(SlotT+3)/2','Height-1'), 'SlotT*0.6', 2)
    main = cut('ShellSlotPocket', '木壳 / 顶部内衬浅槽', main, slot_pocket)
    for side, x in [('Left','-1'),('Right','Width-Wall-1')]:
        aperture = rounded(side+'Aperture', side+'侧向声学开口 / 圆角', ('Wall+2','SpeakerD-12','SpeakerH-12'), (x,'SpeakerY+6','SpeakerZ+6'), 'GrilleR', 0)
        main = cut('Shell'+side, '木壳 / '+side+'侧面开口', main, aperture)
    main.Label = '连续圆润木壳（非制造结构）'
    main.ViewObject.DisplayMode = 'Shaded'
    # Only the final boolean is a delivered part. Ancestors remain editable.
    for obj in list(groups['Enclosure'].Group):
        if obj != main:
            groups['Enclosure'].removeObject(obj)
            groups['Construction'].addObject(obj)
            obj.Visibility = False
    top_mask = box('TopSectionTool', '剖视上部裁切 / 非零件', ('Width+2','Depth-Wall+2','CornerR+2'), (-1,'Wall','Height-CornerR'), group='Construction')
    section = cut('ShellSectionTop', '剖视木壳 / 移除上部', main, top_mask)
    side_mask = box('SideSectionTool', '剖视右部裁切 / 非零件', ('CornerR+2','Depth-Wall+2','Height+2'), ('Width-CornerR','Wall',-1), group='Construction')
    section_final = cut('ShellCutaway', '木壳剖视展示 / 非额外零件', section, side_mask)
    for obj in (section, section_final):
        groups['Enclosure'].removeObject(obj)
        groups['Presentation' if obj == section_final else 'Construction'].addObject(obj)
        obj.Visibility = False
    section_final.ViewObject.DisplayMode = 'Shaded'
    main.Visibility = True
    rounded('Rear', '内嵌可拆黑色后盖 / 无紧固件', ('Width-2*Wall','Wall','Height-2*Wall'), ('Wall','Depth-Wall','Wall'), 'CornerR-Wall', 1, DARK, 'Enclosure')
    rounded('FloatingBase', '内缩悬浮底座 / 承重待验证', ('Width-2*BaseInsetX','Depth-2*BaseInsetY','BaseH'), ('BaseInsetX','BaseInsetY','-BaseH'), 'BaseR', 2, DARK, 'Enclosure')
    bezel = rounded('BezelBlank', '内嵌黑色屏幕框毛坯', ('BezelW','BezelT','BezelH'), ('(Width-BezelW)/2','BezelInset','BezelZ'), 'BezelR', 1, DARK)
    window = box('ScreenWindow', '完整矩形可视区 / 不遮屏', ('ActiveW','BezelT+2','ActiveH'), ('(Width-ActiveW)/2','BezelInset-1','LowerBand+(ScreenH-ActiveH)/2'), group='Construction')
    bezel = cut('BlackBezel', '内嵌黑色屏幕框 / 保留完整可视区', bezel, window, DARK)
    groups['Enclosure'].removeObject(bezel)
    groups['Details'].addObject(bezel)
    slot_liner = rounded('SlotLinerBlank', '顶部槽口黑色内衬毛坯', ('SlotW+4','SlotT+3',0.8), ('(Width-SlotW-4)/2','DriveY+DriveT/2-(SlotT+3)/2','Height-0.8'), 'SlotT*0.6', 2, DARK)
    slot_liner = cut('SlotLiner', '顶部进碟槽黑色内衬 / 非导向设计', slot_liner, slot, DARK)
    groups['Enclosure'].removeObject(slot_liner)
    groups['Details'].addObject(slot_liner)
    box('DisplayClearance', '显示可视区前方净空 / 检查遮挡', ('ActiveW','Wall+0.6','ActiveH'), ('(Width-ActiveW)/2',-1,'LowerBand+(ScreenH-ActiveH)/2'), group='Clearances')
    panel = box('ScreenPanel', '屏幕面板 / 用户测量210×160×2mm', ('ScreenW', 'ScreenT', 'ScreenH'), ('SideBorder', 'Wall+0.5', 'LowerBand'), DARK, note='用户测量口述；可视区按用户指定200×150建模；型号/固定方式待补；不含背面排线电路板')
    panel.EvidenceStatus = 'USER-REPORTED MEASUREMENT / 用户测量口述；安装位置假设'
    ribbon = box('ScreenRibbonBoard', '背面左侧排线电路板 / 10×140×2.4mm', ('RibbonW', 'RibbonT', 'RibbonH'), ('SideBorder', 'Wall+0.5+ScreenT+RibbonGap', 'LowerBand+RibbonBottomGap'), (0.30, 0.46, 0.26), note='用户更正为背面左侧；左右沿用模型正视坐标，左侧为X较小端；宽厚及上下间距为用户口述，高由屏幕高减上下间距推导；板在屏幕宽内；贴背间隙未测暂取0；非HDMI/Type-C驱动板')
    ribbon.EvidenceStatus = 'USER-REPORTED / DERIVED / 位置与间隙部分假设'
    box('Display', '屏幕可视面（无UI实现含义）', ('ActiveW', 0.4, 'ActiveH'), ('(Width-ActiveW)/2', 'Wall-0.4', 'LowerBand+(ScreenH-ActiveH)/2'), (0.10, 0.19, 0.23), 'Details')
    box('ScreenDriver', '屏幕驱动板占位 / 待测', ('DriverW', 'DriverT', 'DriverH'), ('(Width-DriverW)/2', 'Wall+ScreenT+3', 30), (0.22, 0.53, 0.50))
    box('OpticalDrive', 'UJ-898 光驱包络 / 竖装待验证', ('DriveW', 'DriveT', 'DriveH'), ('(Width-DriveW)/2', 'DriveY', 'Height-Wall-DriveTopGap-DriveH'), (0.62, 0.65, 0.67), note='假设包络；非产品精确外形；竖装/顶部槽口/接口待验证')
    box('OpticalBridge', '光驱桥接器占位 / 未选型', (35, 14, 18), ('(Width-35)/2', 'DriveY+DriveT+3', 'Height-Wall-DriveTopGap-DriveH'), (0.35, 0.58, 0.56))
    for side, x in [('Left', 'Wall+SideGap'), ('Right', 'Width-Wall-SideGap-SpeakerT')]:
        box('Speaker'+side, side+'完整音箱包络 / 可拆分假设', ('SpeakerT', 'SpeakerD', 'SpeakerH'), (x, 'SpeakerY', 'SpeakerZ'), (0.17, 0.18, 0.20), note='假设原音箱可独立拆分且音腔完整；未确认，不可据此切割实物')
        gx = 'Wall-1' if side=='Left' else 'Width-Wall+0.2'
        rounded('Grille'+side, side+'内嵌圆角格栅（示意）', (0.8, 'SpeakerD-12', 'SpeakerH-12'), (gx, 'SpeakerY+6', 'SpeakerZ+6'), 'GrilleR', 0, (0.08, 0.08, 0.075), 'Details')
        for i in range(9):
            box('Slat'+side+str(i), side+'格栅条 '+str(i+1), (1.0, 'SpeakerD-24', 1.4), ('Wall-1.2' if side=='Left' else 'Width-Wall+0.1', 'SpeakerY+12', 'SpeakerZ+12+'+str(i)+'*(SpeakerH-24)/8'), BRASS, 'Details')
    box('Battery', '电池包占位 / 未定化学体系及Wh', ('BatteryW', 'BatteryD', 'BatteryH'), ('(Width-BatteryW)/2', 'BatteryY', 'BatteryZ'), (0.73, 0.45, 0.18))
    box('RaspberryPi', '竖放 Pi 4B + 散热包络 / 假设', ('PiW', 'PiH', 'PiD'), ('(Width-PiW)/2', 'PiY', 'PiZ'), (0.18, 0.48, 0.28))
    box('Disk', 'SSK移动硬盘包络 / 非SSD定案', ('DiskW', 'DiskT', 'DiskH'), ('(Width-DiskW)/2', 'Depth-Wall-RearGap-DiskT', 'DiskZ'), (0.31, 0.38, 0.48))
    box('Hub', '竖放有源USB Hub / 未选型', ('HubW', 'HubH', 'HubD'), ('(Width-HubW)/2', 'HubY', 'HubZ'), (0.36, 0.34, 0.54))
    box('Amplifier', 'TPA3118D2候选功放包络', ('AmpW', 'AmpD', 'AmpH'), ('Wall+BoardEdgeGap', 'Depth-Wall-CableLaneD-AmpD-2', 'Height-Wall-AmpH-BoardTopGap'), (0.56, 0.34, 0.20))
    box('DAC', 'DAC + Line Out分配区 / 待选型', ('DacW', 'DacD', 'DacH'), ('Width-Wall-DacW-BoardEdgeGap', 'Depth-Wall-CableLaneD-DacD-2', 'Height-Wall-DacH-BoardTopGap'), (0.20, 0.52, 0.58))
    box('PowerManagement', 'PD/充电/电源路径/稳压综合预留区', ('PowerW', 'PowerD', 'PowerH'), ('(Width-PowerW)/2', 'Depth-Wall-CableLaneD-PowerD-2', 'Wall+4'), (0.66, 0.28, 0.26), note='仅综合空间预留；不表示电源电路、模块数量或UPS功能已完成')
    # Cosmetic controls and connectors have editable native properties, not drill templates.
    def cylinder(name, label, radius, height, pos, direction, color):
        o = doc.addObject('Part::Cylinder', name)
        o.Label = label
        o.Radius, o.Height = radius, height
        for key, expr in zip(('x','y','z'), pos):
            o.setExpression('Placement.Base.'+key, E(expr))
        o.Placement.Rotation = App.Rotation(App.Vector(0,0,1), App.Vector(*direction))
        o.ViewObject.ShapeColor = color
        tag(o, '外观示意；非孔位/器件规格；与壳体接触不用于干涉合格判定')
        groups['Details'].addObject(o)
        return o
    cylinder('VolumeKnob', '音量旋钮（候选）', 11, 7, ('Width-38', 0, 'LowerBand/2'), (0,-1,0), BRASS)
    for i in range(3):
        cylinder('Control'+str(i), '播放控件示意 '+str(i+1), 3, 2, ('Width-'+str(104-i*16), 0, 'LowerBand/2'), (0,-1,0), BRASS)
    cylinder('RcaL', 'RCA L Line Out（位置示意）', 4, 4, ('Width-30', 'Depth', 48), (0,1,0), (0.9,0.9,0.83))
    cylinder('RcaR', 'RCA R Line Out（位置示意）', 4, 4, ('Width-16', 'Depth', 48), (0,1,0), (0.68,0.16,0.12))
    box('TypeC', '单一USB-C电源入口（位置示意）', (10, 2, 4), ('Width-35', 'Depth', 25), DARK, 'Details')
    # CableLane and DisplayClearance are geometric keep-outs; DiscHandling is visual only.
    box('CableLane', '后部线束通道提示 / 非完整插头净空', ('Width-2*Wall-4', 'CableLaneD', 'Height-2*Wall-4'), ('Wall+2', 'Depth-Wall-CableLaneD', 'Wall+2'), (0.6,0.7,0.8), 'Clearances').ViewObject.Transparency = 85
    cylinder('DiscHandling', 'CD上方操作包络（隐藏；非实物装配）', 60, 1.2, ('Width/2', 'DriveY+DriveT/2', 'Height+60'), (0,1,0), (0.7,0.75,0.8))
    groups['Details'].removeObject(doc.getObject('DiscHandling'))
    groups['Clearances'].addObject(doc.getObject('DiscHandling'))
    for o in groups['Construction'].Group + groups['Clearances'].Group + groups['Presentation'].Group:
        o.Visibility = False
    doc.recompute()
    Gui.activeDocument().activeView().viewIsometric()
    Gui.activeDocument().activeView().fitAll()
    doc.recompute()
    refresh(doc, root)
    return doc


def refresh(doc, root):
    """Regenerate the deliverables from the current document's parameters."""
    out = Path(root) / 'cad'
    if not doc or not doc.getObject('Parameters') or not doc.getObject('Hardware'):
        raise ValueError('请先激活 VINTROX 布局文档')
    doc.recompute()
    report = validate(doc)
    if report['errors']:
        raise RuntimeError(report['errors'])
    App.setActiveDocument(doc.Name)
    previews(doc, out)
    doc.saveAs(str(out / 'vintrox-layout.FCStd'))
    Part.export(physical(doc), str(out / 'vintrox-layout.step'))
    (out / 'layout-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')


def scene(doc, kind='exterior'):
    for o in doc.Enclosure.Group + doc.Details.Group:
        o.Visibility = True
    for o in doc.Hardware.Group:
        o.Visibility = True
    for o in doc.Construction.Group + doc.Clearances.Group + doc.Presentation.Group:
        o.Visibility = False
    if kind == 'interior':
        for name in ['ShellRight','Rear','GrilleRight','SlotLiner'] + ['SlatRight'+str(i) for i in range(9)]:
            doc.getObject(name).Visibility = False
        doc.ShellCutaway.Visibility = True
    elif kind == 'hardware':
        for o in doc.Enclosure.Group + doc.Details.Group:
            o.Visibility = False
        # Expose the upright center stack while keeping its true coordinates.
        doc.SpeakerRight.Visibility = False
        doc.Disk.Visibility = False
    Gui.activeDocument().activeView().fitAll()

def previews(doc, out):
    view = Gui.activeDocument().activeView()
    view.setAnimationEnabled(False) if hasattr(view, 'setAnimationEnabled') else None
    # Camera local Z points toward the eye; keep global Z upright.
    def camera(eye):
        z = App.Vector(*eye)
        z.normalize()
        x = App.Vector(0,0,1).cross(z)
        x.normalize()
        y = z.cross(x)
        return App.Rotation(x,y,z,'ZXY').Q
    for kind, filename, quat in [
        ('exterior','exterior.png',camera((1,-1.8,0.55))),
        ('interior','interior.png',camera((1,1.5,1.4))),
        ('hardware','hardware.png',camera((0.7,1.0,2.0))),
    ]:
        scene(doc,kind)
        view.setCameraOrientation(quat)
        view.fitAll()
        Gui.updateGui()
        import re
        camera_text = view.getCamera()
        camera_text = re.sub(r'(height\s+)([0-9.eE+-]+)', lambda m: m.group(1)+str(float(m.group(2))*1.18), camera_text)
        view.setCamera(camera_text)
        Gui.updateGui()
        view.saveImage(str(out/'previews'/filename),1600,1200,'White')
    scene(doc,'exterior')
    view.setCameraOrientation(camera((1,-1.8,0.55)))
    view.fitAll()
    Gui.updateGui()
