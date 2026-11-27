"""Parametric modular terminal, using native FreeCAD solids and expressions."""
from pathlib import Path
import csv
import json
import re
import FreeCAD as App
import Part
import Sketcher

# Numbers are mm. Entries explicitly distinguish user inputs from assumptions.
PARAMETERS = [
 ('ScreenW',210,'屏幕总宽','用户测量口述'),('ScreenH',160,'屏幕总高','用户测量口述'),
 ('ScreenT',2,'屏幕厚','用户测量口述，不含排线板'),('ActiveW',200,'可视区宽','用户指定建模尺寸'),
 ('ActiveH',150,'可视区高','用户指定建模尺寸'),('RibbonW',10,'左侧排线板宽','用户口述，正视X较小端'),
 ('RibbonT',2.4,'排线板自身厚','用户口述'),('RibbonEndGap',10,'排线板上下留边','用户口述'),
 ('RibbonGap',0,'排线板贴背间隙','未测，暂取0'),('SideBorder',12,'单侧结构余量','假设'),
 ('LowerBand',38,'屏幕底高','布局假设'),('TopBand',14,'屏幕顶部余量','假设'),
 ('Depth',160,'机身本体深度','候选目标，非加工规格'),('Wall',3,'打印外罩壁厚','假设，材料/强度未验证'),
 ('BaseT',4,'底盘厚','假设'),('Seam',0.4,'壳片装配缝','假设，须打印小样'),
 ('EdgeR',3,'后盖小圆角','造型假设'),('ControlH',32,'下控制区分界高','假设'),
 ('FrontRun',18,'顶部前斜肩进深','造型假设'),('FrontDrop',12,'顶部前缘下降','造型假设'),
 ('RearRun',12,'顶部后斜肩进深','造型假设'),('RearDrop',8,'顶部后缘下降','造型假设'),
 ('LowerRun',14,'侧壳前下切角进深','造型假设'),('LowerRise',10,'侧壳前下切角抬高','造型假设'),
 ('RearLowerRun',12,'侧壳后下切角进深','造型假设'),('RearLowerRise',6,'侧壳后下切角抬高','造型假设'),
 ('SideRecess',0.8,'侧面嵌区深度','假设；局部余壁2.2mm未验证'),('SideCut',8,'侧面嵌区切角','造型假设'),
 ('GrilleRise',12,'格栅槽两端高差','造型假设；声学未测'),('ControlBevel',6,'控制面板上下斜面高度','造型假设'),
 ('BezelCorner',3,'前框角部斜切','造型假设'),('BaseCorner',10,'底盘平面切角','造型假设'),
 ('FaceInset',2,'黑框前表面内嵌','假设'),('FootH',5,'支撑脚高','假设'),
 ('MountT',2,'托架侧壁','假设'),('MountFloor',2.4,'托架底厚','假设'),
 ('Fit',0.4,'硬件与托架单侧间隙','假设，非验证配合'),('LipH',8,'托架围边高度','假设'),
 ('BoltD',3.4,'候选连接通孔径','假设，紧固件规格/孔补偿待试制'),('Post',7,'支柱边长','假设'),
 ('ShelfT',4,'中央托臂厚','假设，层间强度未验证'),('SpineY',116,'中央骨架前表面','布局假设'),
 ('SpineW',106,'中央骨架宽','假设'),('SpineT',3,'中央骨架板厚','假设'),
 ('CableD',8,'后部线束预留深','假设，不证明插头/弯线足够'),
 ('DriveW',128,'光驱横宽','原占位假设，非完整测绘包络'),('DriveH',128,'光驱竖高','假设，照片方向尚未统一'),
 ('DriveT',13,'光驱厚','原占位假设'),('DriveY',22,'光驱前缘','假设'),('DriveTopGap',4,'光驱顶部间隙','假设'),
 ('SlotW',124,'顶部入口长','假设，未验证导向/退盘'),('SlotT',4,'顶部入口宽','假设'),
 ('SpeakerT',55,'单箱横厚','假设，非整组尺寸拆半'),('SpeakerD',105,'单箱前后深','假设'),
 ('SpeakerH',115,'单箱高','假设'),('SpeakerY',38,'音箱前缘','假设'),('SpeakerZ',60,'音箱底高','假设'),
 ('SpeakerGap',3.5,'音箱距侧板内面的距离','假设'),('BatteryW',120,'电池宽','假设，未选型号/Wh'),
 ('BatteryD',75,'电池深','假设'),('BatteryH',32,'电池高','假设'),('BatteryY',36,'电池前缘','布局假设'),
 ('BatteryZ',12,'电池底高','假设'),('PiW',85,'Pi综合包络宽','占位假设，含器件/散热未实测'),
 ('PiT',25,'竖放Pi厚','假设'),('PiH',65,'竖放Pi高','假设'),('PiY',57,'Pi前缘','假设'),('PiZ',60,'Pi底高','假设'),
 ('HubW',50,'Hub宽','假设，未选型'),('HubT',22,'Hub厚','假设'),('HubH',70,'竖放Hub高','假设'),
 ('HubY',85,'Hub前缘','假设'),('HubZ',80,'Hub底高','假设'),('DiskW',80.5,'硬盘横宽','用户含壳宽80.5；竖放映射为假设'),
 ('DiskT',13,'硬盘厚','用户含壳厚13，未本地复测'),('DiskH',131.5,'硬盘高','用户含壳长131.5；竖放映射为假设'),('DiskY',126,'硬盘前缘','假设'),('DiskZ',45,'硬盘底高','假设'),
 ('DriverW',94.5,'屏幕独立驱动板横宽','用户长94.5；整机横向映射为假设'),('DriverT',5,'驱动板厚','用户指定估算5，非实测'),
 ('DriverH',63.5,'驱动板高','用户宽63.5；竖高映射为假设'),('DriverY',14,'驱动板前缘','假设'),('DriverZ',24,'驱动板底高','假设'),
 ('AmpW',50,'功放宽','假设，未选板'),('AmpT',20,'竖放功放厚','旋转原包络'),('AmpH',25,'竖放功放高','旋转原包络'),
 ('DacW',60,'DAC宽','假设'),('DacT',16,'竖放DAC厚','旋转原包络'),('DacH',25,'竖放DAC高','旋转原包络'),
 ('AudioZ',183.6,'音频板底高','假设'),('PowerW',70,'电源管理区宽','综合假设，非选定单模块'),
 ('PowerD',24,'电源管理区深','假设'),('PowerH',28,'电源管理区高','假设'),('PowerY',121.6,'电源区前缘','假设'),
 ('PowerZ',10,'电源区底高','假设'),('PrintX',256,'评估成型空间X','仅假设，不是用户打印机规格'),
 ('PrintY',256,'评估成型空间Y','仅假设'),('PrintZ',256,'评估成型空间Z','仅假设'),
]
GRAY=(0.68,0.72,0.74); DARK=(0.075,0.095,0.12); ORANGE=(0.98,0.31,0.075)
GREEN=(0.18,0.47,0.31); BLUE=(0.28,0.40,0.55); SILVER=(0.64,0.68,0.71)


def expression(value):
    return re.sub(r'\b([A-Z][A-Za-z0-9]*)\b',lambda m:'Parameters.'+m.group(1),str(value))


class Builder:
    def __init__(self,doc):
        self.doc=doc; self.parts=[]; self.interfaces=[]
        self.groups={}
        for name,label in [('Printed','01 打印分件 / 试制假设'),('Hardware','02 硬件占位 / 非精确零件'),('Standard','03 接口与紧固件示意'),('Clearances','04 净空检查 / 隐藏'),('Presentation','05 展示 / 非额外零件'),('Construction','99 原生构造 / 隐藏')]:
            self.groups[name]=doc.addObject('App::DocumentObjectGroup',name);self.groups[name].Label=label
    def tag(self,obj,note='假设尺寸；未实测，非验证打印件'):
        obj.addProperty('App::PropertyString','EvidenceStatus','Evidence');obj.EvidenceStatus=note
    def box(self,name,dims,pos,color=DARK):
        obj=self.doc.addObject('Part::Box',name)
        for key,val in zip(('Length','Width','Height'),dims): obj.setExpression(key,expression(val))
        for key,val in zip(('x','y','z'),pos): obj.setExpression('Placement.Base.'+key,expression(val))
        obj.ViewObject.ShapeColor=color;self.groups['Construction'].addObject(obj)
        return obj
    def cylinder(self,name,r,h,pos,axis=(0,0,1),color=DARK):
        obj=self.doc.addObject('Part::Cylinder',name)
        obj.setExpression('Radius',expression(r));obj.setExpression('Height',expression(h))
        obj.Placement.Rotation=App.Rotation(App.Vector(0,0,1),App.Vector(*axis))
        for key,val in zip(('x','y','z'),pos):obj.setExpression('Placement.Base.'+key,expression(val))
        obj.ViewObject.ShapeColor=color;self.groups['Construction'].addObject(obj)
        return obj
    def rounded(self,name,dims,pos,r,axis,color=DARK):
        body=self.doc.addObject('PartDesign::Body',name)
        blank=body.newObject('PartDesign::AdditiveBox',name+'Blank')
        for key,val in zip(('Length','Width','Height'),dims):blank.setExpression(key,expression(val))
        for key,val in zip(('x','y','z'),pos):blank.setExpression('Placement.Base.'+key,expression(val))
        self.doc.recompute()
        ids=[]
        for i,e in enumerate(blank.Shape.Edges,1):
            bb=e.BoundBox;values=[bb.XLength,bb.YLength,bb.ZLength]
            if values[axis]>1e-6 and all(values[j]<1e-6 for j in range(3) if j!=axis):ids.append('Edge'+str(i))
        fillet=body.newObject('PartDesign::Fillet',name+'Round');fillet.Base=(blank,ids)
        fillet.setExpression('Radius',expression(r));body.Tip=fillet
        for obj in (body,fillet):obj.ViewObject.ShapeColor=color
        blank.Visibility=False;self.groups['Construction'].addObject(body)
        self.doc.recompute();return body
    def prism(self,name,points,plane,pos,length,color=DARK):
        """Closed native sketch + extrusion; all vertex coordinates use expressions."""
        sketch=self.doc.addObject('Sketcher::SketchObject',name+'Profile')
        if plane=='YZ':sketch.Placement.Rotation=App.Rotation(App.Vector(1,1,1),120)
        elif plane=='XZ':sketch.Placement.Rotation=App.Rotation(App.Vector(1,0,0),90)
        for key,val in zip(('x','y','z'),pos):sketch.setExpression('Placement.Base.'+key,expression(val))
        coords=[tuple(float(self.doc.Parameters.evalExpression(expression(v))) for v in pt) for pt in points]
        for i,(u,v) in enumerate(coords):
            nu,nv=coords[(i+1)%len(coords)]
            sketch.addGeometry(Part.LineSegment(App.Vector(u,v,0),App.Vector(nu,nv,0)),False)
        for i,pt in enumerate(points):
            sketch.addConstraint(Sketcher.Constraint('Coincident',i,2,(i+1)%len(points),1))
            for axis,value in zip(('X','Y'),pt):
                index=sketch.addConstraint(Sketcher.Constraint('Distance'+axis,i,1,coords[i][0 if axis=='X' else 1]))
                sketch.setExpression('Constraints['+str(index)+']',expression(value))
        obj=self.doc.addObject('Part::Extrusion',name);obj.Base=sketch;obj.Solid=True
        obj.Dir=App.Vector(*( {'YZ':(1,0,0),'XZ':(0,1,0),'XY':(0,0,1)}[plane]))
        obj.setExpression('LengthFwd',expression(length));obj.ViewObject.ShapeColor=color
        self.groups['Construction'].addObject(sketch);self.groups['Construction'].addObject(obj)
        sketch.Visibility=False
        return obj
    def octagon(self,name,u,v,w,h,cut,plane,pos,length,color=DARK):
        points=[(f'({u})+({cut})',v),(f'({u})+({w})-({cut})',v),
                (f'({u})+({w})',f'({v})+({cut})'),(f'({u})+({w})',f'({v})+({h})-({cut})'),
                (f'({u})+({w})-({cut})',f'({v})+({h})'),(f'({u})+({cut})',f'({v})+({h})'),
                (u,f'({v})+({h})-({cut})'),(u,f'({v})+({cut})')]
        return self.prism(name,points,plane,pos,length,color)
    def cut(self,name,base,tools):
        if not isinstance(tools,list):tools=[tools]
        tool=self.fuse(name+'Tools',tools) if len(tools)>1 else tools[0]
        obj=self.doc.addObject('Part::Cut',name);obj.Base=base;obj.Tool=tool;obj.Refine=True
        self.groups['Construction'].addObject(obj);base.Visibility=False;tool.Visibility=False
        return obj
    def fuse(self,name,objects):
        if len(objects)==1:return objects[0]
        obj=self.doc.addObject('Part::MultiFuse',name);obj.Shapes=objects;obj.Refine=True
        self.groups['Construction'].addObject(obj)
        for o in objects:o.Visibility=False
        return obj
    def finish(self,obj,label,color=GRAY,group='Printed',rotation=(0,0,0),note='假设分件；打印/强度/装配未验证'):
        self.groups['Construction'].removeObject(obj);self.groups[group].addObject(obj)
        obj.Label=label;obj.ViewObject.ShapeColor=color;obj.ViewObject.LineColor=tuple(c*.55 for c in color)
        obj.ViewObject.DisplayMode='Flat Lines' if group=='Hardware' else 'Shaded'
        self.tag(obj,note)
        if group=='Printed':
            obj.addProperty('App::PropertyString','PartID','Manufacturing');obj.PartID='P'+str(len(self.parts)+1).zfill(2)
            obj.addProperty('App::PropertyVector','ExportRotation','Manufacturing');obj.ExportRotation=App.Vector(*rotation)
            self.parts.append(obj)
        return obj
    def bolt_z(self,name,points,z,h):
        return [self.cylinder(name+str(i),'BoltD/2',h,(x,y,z)) for i,(x,y) in enumerate(points)]
    def bolt_y(self,name,points,y,h):
        return [self.cylinder(name+str(i),'BoltD/2',h,(x,y,z),(0,1,0)) for i,(x,z) in enumerate(points)]
    def cradle(self,name,w,d,x,y,z,open_side=None,tabs=None,posts=None):
        # Fit clearance applies only to side walls; hardware rests at the floor's top face.
        ox=f'({x})-Fit-MountT';oy=f'({y})-Fit-MountT';oz=f'({z})-MountFloor'
        ow=f'({w})+2*(Fit+MountT)';od=f'({d})+2*(Fit+MountT)'
        floor=self.box(name+'Floor',(ow,od,'MountFloor'),(ox,oy,oz))
        solids=[floor]
        if open_side!='left':solids.append(self.box(name+'Left',('MountT',od,'LipH'),(ox,oy,z)))
        if open_side!='right':solids.append(self.box(name+'Right',('MountT',od,'LipH'),(f'({x})+({w})+Fit',oy,z)))
        solids += [self.box(name+'Front',(ow,'MountT','LipH'),(ox,oy,z)), self.box(name+'Back',(ow,'MountT','LipH'),(ox,f'({y})+({d})+Fit',z))]
        holes=[]
        if tabs:
            side,edge=tabs
            tx=f'({ox})-8' if side=='left' else f'({x})+({w})+Fit+MountT'
            ys=[oy] if edge=='front' else [f'({y})+({d})+Fit+MountT-8'] if edge=='back' else [oy,f'({y})+({d})+Fit+MountT-8']
            for i,ty in enumerate(ys):
                solids.append(self.box(name+'Ear'+str(i),(8,8,'MountFloor'),(tx,ty,oz)))
                holes.append((f'({tx})+4',f'({ty})+4'))
        if posts:
            for i,(px,py) in enumerate(posts):
                solids.append(self.box(name+'Post'+str(i),('Post','Post',f'({z})-MountFloor-BaseT'),(px,py,'BaseT')))
        obj=self.fuse(name+'Raw',solids)
        if holes:obj=self.cut(name,obj,self.bolt_z(name+'Bolt',holes,f'({z})-MountFloor-6',12))
        return obj,holes


def build(root):
    import FreeCADGui as Gui
    root=Path(root);out=root/'cad/terminal';(out/'previews').mkdir(parents=True,exist_ok=True);(out/'parts').mkdir(exist_ok=True)
    doc=App.newDocument('VINTROX_Terminal');doc.Label='VINTROX / 模块化桌面终端 / 打印分件草案'
    p=doc.addObject('Spreadsheet::Sheet','Parameters');p.Label='00 参数 / 用户尺寸与假设分列'
    for c,t in zip('ABCD',('别名','数值 mm','含义','信息状态')):p.set(c+'1',t)
    for row,(key,value,label,state) in enumerate(PARAMETERS,2):
        for c,value_ in zip('ABCD',(key,str(value),label,state)):p.set(c+str(row),value_)
        p.setAlias('B'+str(row),key)
    row=len(PARAMETERS)+3
    for key,formula,label in [('Width','=ScreenW+2*SideBorder','机身宽'),('Height','=ScreenH+LowerBand+TopBand','机身高，不含脚'),('DriveZ','=Height-Wall-DriveTopGap-DriveH','光驱底高'),('RibbonH','=ScreenH-2*RibbonEndGap','排线板推导高')]:
        p.set('A'+str(row),key);p.set('B'+str(row),formula);p.setAlias('B'+str(row),key);p.set('C'+str(row),label);p.set('D'+str(row),'派生；非实测整机');row+=1
    for c,width in zip('ABCD',(150,100,230,365)):p.setColumnWidth(c,width)
    p.setStyle('A1:D1','bold','add');doc.recompute()
    b=Builder(doc)
    # Native hardware envelopes, preserving the measured screen and prior assumptions.
    hw=[('ScreenPanel','屏幕本体',( 'ScreenW','ScreenT','ScreenH'),('SideBorder',8.5,'LowerBand'),DARK),
        ('ScreenRibbonBoard','屏幕后左侧排线板',('RibbonW','RibbonT','RibbonH'),('SideBorder','8.5+ScreenT+RibbonGap','LowerBand+RibbonEndGap'),GREEN),
        ('ScreenDriver','独立屏幕驱动板',('DriverW','DriverT','DriverH'),('(Width-DriverW)/2','DriverY','DriverZ'),GREEN),
        ('OpticalDrive','竖装光驱 / 姿态待验证',('DriveW','DriveT','DriveH'),('(Width-DriveW)/2','DriveY','DriveZ'),SILVER),
        ('OpticalBridge','光驱桥接占位', (35,14,18),('(Width-35)/2','DriveY+DriveT+3','DriveZ-26'),GREEN),
        ('SpeakerLeft','左完整音箱 / 拆分待验证',('SpeakerT','SpeakerD','SpeakerH'),('Wall+SpeakerGap','SpeakerY','SpeakerZ'),DARK),
        ('SpeakerRight','右完整音箱 / 拆分待验证',('SpeakerT','SpeakerD','SpeakerH'),('Width-Wall-SpeakerGap-SpeakerT','SpeakerY','SpeakerZ'),DARK),
        ('Battery','电池包 / 容量及型号未定',('BatteryW','BatteryD','BatteryH'),('(Width-BatteryW)/2','BatteryY','BatteryZ'),(0.79,.48,.18)),
        ('Pi','竖放Pi及散热包络',('PiW','PiT','PiH'),('(Width-PiW)/2','PiY','PiZ'),GREEN),
        ('Hub','竖放有源Hub占位',('HubW','HubT','HubH'),('(Width-HubW)/2','HubY','HubZ'),(.4,.35,.58)),
        ('Disk','SSK硬盘占位 / 介质未知',('DiskW','DiskT','DiskH'),('(Width-DiskW)/2','DiskY','DiskZ'),BLUE),
        ('Amplifier','竖放功放候选',('AmpW','AmpT','AmpH'),(14,126,'AudioZ'),(.56,.34,.2)),
        ('DAC','竖放DAC候选',('DacW','DacT','DacH'),('Width-14-DacW',128,'AudioZ'),(.2,.52,.58)),
        ('Power','PD/充电/电源路径/稳压综合区',('PowerW','PowerD','PowerH'),('(Width-PowerW)/2','PowerY','PowerZ'),(.65,.28,.25))]
    for name,label,dims,pos,color in hw:
        obj=b.box(name,dims,pos,color);note='用户测量/指定及派生；装配净空待核对' if name in ('ScreenPanel','ScreenRibbonBoard') else '假设包络；不是具体板卡、接口、固定孔或整机实测'
        if name in ('Disk','ScreenDriver'):note='用户部件尺寸及指定估算/假设，整机方向映射候选；插头/最高元件/固定孔净空未验证'
        b.finish(obj,label,color,'Hardware',note=note)
    # Side panels and their top/base/rear attachment lands.
    top_points=[(7,'FrontRun+14'),(7,'Depth-RearRun-10'),('Width-7','FrontRun+14'),('Width-7','Depth-RearRun-10')]
    base_points=[(7,14),(7,'Depth-14'),('Width-7',14),('Width-7','Depth-14')]
    rear_points=[(7,20),(7,'Height-20'),('Width-7',20),('Width-7','Height-20')]
    for side,x in [('Left',0),('Right','Width-Wall')]:
        outline=[(0,'BaseT+Seam+LowerRise'),('LowerRun','BaseT+Seam'),('Depth-RearLowerRun','BaseT+Seam'),('Depth','BaseT+Seam+RearLowerRise'),
                 ('Depth','Height-RearDrop-Wall-Seam'),('Depth-RearRun','Height-Wall-Seam'),('FrontRun','Height-Wall-Seam'),(0,'Height-FrontDrop-Wall-Seam')]
        obj=b.prism(side+'ShellBlank',outline,'YZ',(x,0,0),'Wall',GRAY)
        aperture=b.octagon(side+'SoundTool','SpeakerY+4','SpeakerZ+4','SpeakerD-8','SpeakerH-8','SideCut+2','YZ',(-1 if side=='Left' else 'Width-Wall-1',0,0),'Wall+2')
        obj=b.cut(side+'SoundOpening',obj,aperture)
        inset=b.octagon(side+'Inset','SpeakerY-4','SpeakerZ-4','SpeakerD+8','SpeakerH+8','SideCut','YZ',(-.01 if side=='Left' else 'Width-SideRecess',0,0),'SideRecess+0.01')
        obj=b.cut(side+'Recessed',obj,inset)
        tabx='Wall' if side=='Left' else 'Width-Wall-8'
        tabs=[]
        for i,yy in enumerate(('FrontRun+10','Depth-RearRun-14')):
            tabs.append(b.box(side+'TopLand'+str(i),(8,8,4),(tabx,yy,'Height-Wall-4')))
        for i,yy in enumerate((10,'Depth-18')):
            tabs.append(b.box(side+'BaseLand'+str(i),(8,8,4),(tabx,yy,'BaseT')))
        for i,zz in enumerate((16,'Height-24')):
            tabs.append(b.box(side+'RearLand'+str(i),(8,4,8),(tabx,'Depth-Wall-4',zz)))
        obj=b.fuse(side+'ShellLands',[obj]+tabs)
        obj=b.cut(side+'Shell',obj,b.bolt_z(side+'TopBolt',top_points[:2] if side=='Left' else top_points[2:],'Height-Wall-8',12)+b.bolt_z(side+'BaseBolt',base_points[:2] if side=='Left' else base_points[2:],-1,12)+b.bolt_y(side+'RearBolt',rear_points[:2] if side=='Left' else rear_points[2:],'Depth-10',12))
        b.finish(obj,side+' / 外罩及连接耳',GRAY,rotation=(0,-90 if side=='Left' else 90,0))
    # Top and a separate printed slot surround.
    roof=[(0,'Height-FrontDrop-Wall'),('FrontRun','Height-Wall'),('Depth-RearRun','Height-Wall'),('Depth','Height-RearDrop-Wall'),
          ('Depth','Height-RearDrop'),('Depth-RearRun','Height'),('FrontRun','Height'),(0,'Height-FrontDrop')]
    top=b.prism('TopBlank',roof,'YZ',(0,0,0),'Width',GRAY)
    slot=b.rounded('SlotTool',('SlotW','SlotT','Wall+3'),('(Width-SlotW)/2','DriveY+DriveT/2-SlotT/2','Height-Wall-1'),1.5,2)
    pocket=b.rounded('SlotPocket',('SlotW+4','SlotT+3',2),('(Width-SlotW-4)/2','DriveY+DriveT/2-(SlotT+3)/2','Height-1'),2.4,2)
    top=b.cut('TopCap',top,[slot,pocket]+b.bolt_z('TopBolts',top_points,'Height-Wall-1','Wall+2'));b.finish(top,'折面顶部外罩 / CD入口',GRAY,rotation=(0,90,0))
    trim=b.rounded('SlotTrimBlank',('SlotW+4','SlotT+3',.8),('(Width-SlotW-4)/2','DriveY+DriveT/2-(SlotT+3)/2','Height-.8'),2.4,2,DARK)
    b.finish(b.cut('SlotTrim',trim,slot),'顶部槽口饰件 / 非验证导向件',DARK)
    # Base and independently printed feet.
    base=b.octagon('BaseBlank',0,0,'Width','Depth','BaseCorner','XY',(0,0,0),'BaseT',DARK)
    foot_points=[(20,12),('Width-20',12),(20,'Depth-12'),('Width-20','Depth-12')]
    bosses=[b.cylinder('FootBoss'+str(i),4,6,(x,y,'BaseT')) for i,(x,y) in enumerate(foot_points)]
    base=b.fuse('BaseBosses',[base]+bosses)
    base_holes=b.bolt_z('BaseSideBolt',base_points,-1,10)+b.bolt_z('FootBolt',foot_points,-6,18)
    # Additional base holes for the screen/drive/speaker/carrier mounting feet.
    mount_base_points=[]
    drive_x='(Width-DriveW)/2-Fit-MountT'; drive_right='(Width+DriveW)/2+Fit+MountT-Post'
    drive_ys=['DriveY-Fit-MountT','DriveY+DriveT-Post-2']
    drive_posts=[(x,y) for x in (drive_x,drive_right) for y in drive_ys]
    speaker_posts=[]
    for side in ('Left','Right'):
        xs=(10,45) if side=='Left' else ('Width-10-Post','Width-45-Post')
        speaker_posts.append([(x,y) for x in xs for y in ('SpeakerY+8','SpeakerY+SpeakerD-12')])
    driver_posts=[(x,'DriverY+DriverT/2-Post/2') for x in ('(Width-DriverW)/2-Fit-MountT','(Width+DriverW)/2+Fit+MountT-Post')]
    for pts in [drive_posts,driver_posts]+speaker_posts:
        mount_base_points += [(f'({x})+Post/2',f'({y})+Post/2') for x,y in pts]
    spine_feet=[('(Width-SpineW)/2+6','SpineY+6'),('(Width+SpineW)/2-6','SpineY+6')]
    battery_feet=[(f'({x})+Post/2',y) for x in ('(Width-BatteryW)/2','(Width+BatteryW)/2-Post') for y in ('BatteryY+8','BatteryY+BatteryD-8')]
    power_feet=[(f'({x})+Post/2','(SpineY+13+Fit+PowerY+PowerD)/2') for x in ('(Width-PowerW)/2','(Width+PowerW)/2-Post')]
    control_feet=[(12,6),('Width-12',6)]
    mount_base_points+=spine_feet+battery_feet+power_feet+control_feet
    base_holes+=b.bolt_z('BaseMountBolt',mount_base_points,-1,'BaseT+7')
    base=b.cut('BaseTray',base,base_holes);b.finish(base,'底盘 / 固定孔与脚座',DARK)
    for i,y in enumerate((8,'Depth-16')):
        foot=b.rounded('FootBlank'+str(i),('Width-28',8,'FootH'),(14,y,'-FootH'),2,2,DARK)
        b.finish(b.cut('Foot'+str(i),foot,b.bolt_z('FootHole'+str(i),foot_points[i*2:i*2+2],'-FootH-1','FootH+2')),('前' if i==0 else '后')+'支撑脚',DARK)
    # Screen bezel and independent lower control panel.
    bezel=b.octagon('BezelBlank','Wall+Seam','ControlH+Seam','Width-2*(Wall+Seam)','Height-FrontDrop-Wall-ControlH','BezelCorner','XZ',(0,'FaceInset',0),'Wall',DARK)
    win=b.box('ScreenWindow',('ActiveW',10,'ActiveH'),('(Width-ActiveW)/2',-1,'LowerBand+(ScreenH-ActiveH)/2'))
    bezel=b.cut('BezelWindow',bezel,win)
    screen_points=[(9,'LowerBand+4'),(9,'LowerBand+ScreenH-4'),('Width-9','LowerBand+4'),('Width-9','LowerBand+ScreenH-4')]
    bosses=[b.cylinder('ScreenBoss'+str(i),3,'11.3-FaceInset-Wall',(x,'FaceInset+Wall',z),(0,1,0)) for i,(x,z) in enumerate(screen_points)]
    bezel=b.fuse('BezelBosses',[bezel]+bosses)
    bezel=b.cut('FrontBezel',bezel,b.bolt_y('ScreenBolt',screen_points,-1,16));b.finish(bezel,'内嵌屏幕前框 / 压框连接柱',DARK,rotation=(90,0,0))
    panel=b.prism('ControlBlank',[(0,'BaseT+Seam+ControlBevel'),('Wall','BaseT+Seam'),('Wall','ControlH-Seam'),(0,'ControlH-Seam-ControlBevel')],'YZ',('Wall+Seam',0,0),'Width-2*(Wall+Seam)',DARK)
    control_points=[(12,12),('Width-12',12)]
    panel=b.cut('ControlPanel',panel,b.bolt_y('ControlHoles',control_points,-1,8));b.finish(panel,'独立下部控制面板',DARK,rotation=(90,0,0))
    # Mounting lands connect the control panel to the floor; holes are aligned.
    lands=[b.box('ControlLand'+str(i),(8,6,12),(f'({x})-4','Wall', 'BaseT')) for i,(x,z) in enumerate(control_points)]
    control_land=b.cut('ControlSupport',b.fuse('ControlLands',lands),b.bolt_y('ControlLandHoles',control_points,0,12))
    # The two lands need a connected bottom bar to form a single printable part.
    bar=b.box('ControlSupportBar',('Width-16',3,3),(8,3,'BaseT'))
    control_land=b.fuse('ControlMountRaw',[control_land,bar])
    control_land=b.cut('ControlMount',control_land,b.bolt_z('ControlBaseBolts',control_feet,-1,'BaseT+12'))
    b.finish(control_land,'控制区内支架 / 底盘连接孔',GRAY)
    ret=b.box('RetainerBlank',('ScreenW+12',2.0,'ScreenH+8'),('SideBorder-6',11.3,'LowerBand-4'))
    inner=b.box('RetainerInner',('ScreenW',4,'ScreenH'),('SideBorder',10.3,'LowerBand'))
    ret=b.cut('RetainerRing',ret,inner)
    pads=[b.box('ScreenPad'+str(i),(4,2.8,4),(x,10.5,z)) for i,(x,z) in enumerate([(50,'LowerBand'),('Width-54','LowerBand'),(50,'LowerBand+ScreenH-4'),('Width-54','LowerBand+ScreenH-4')])]
    legs=[b.box('RetainerLeg'+str(i),(6,2,'LowerBand-15.3'),(x,11.3,11.3)) for i,x in enumerate(('SideBorder-6','Width-SideBorder'))]
    feet=[b.box('RetainerFoot'+str(i),(7.6,8,3.3),(x,10,8)) for i,x in enumerate((3.4,'Width-11'))]
    ret=b.fuse('RetainerPads',[ret]+pads+legs+feet)
    ret=b.cut('ScreenRetainer',ret,b.bolt_y('RetainerBolt',screen_points,9,6)+b.bolt_z('RetainerBaseBolts',base_points[:1]+base_points[2:3],7,5))
    b.finish(ret,'屏幕独立压框 / 左排线避让及底脚',GRAY,rotation=(-90,0,0))
    # Tray cradles and support legs.
    drv,_=b.cradle('DriveCradle','DriveW','DriveT','(Width-DriveW)/2','DriveY','DriveZ',posts=drive_posts)
    bridge,_=b.cradle('BridgeCradle',35,14,'(Width-35)/2','DriveY+DriveT+3','DriveZ-26')
    hanger=b.box('BridgeHanger',(39.8,'MountT',17.6),('(Width-35)/2-Fit-MountT','DriveY+DriveT+3-Fit-MountT','DriveZ-18'))
    drv=b.fuse('DriveMountRaw',[drv,bridge,hanger]);drv=b.cut('DriveMount',drv,b.bolt_z('DriveBaseHoles',[(f'({x})+Post/2',f'({y})+Post/2') for x,y in drive_posts],-1,'BaseT+7'))
    b.finish(drv,'光驱与桥接器一体托架 / 脚座',GRAY,rotation=(180,0,0))
    for i,side in enumerate(('Left','Right')):
        x='Wall+SpeakerGap' if side=='Left' else 'Width-Wall-SpeakerGap-SpeakerT'
        cr,_=b.cradle('SpeakerMount'+side,'SpeakerT','SpeakerD',x,'SpeakerY','SpeakerZ',open_side=side.lower(),posts=speaker_posts[i])
        cr=b.cut('SpeakerHolder'+side,cr,b.bolt_z('SpeakerFootHole'+side,[(f'({x})+Post/2',f'({y})+Post/2') for x,y in speaker_posts[i]],-1,'BaseT+7'))
        b.finish(cr,side+'音箱独立托座 / 发声面敞开',GRAY,rotation=(180,0,0))
    dr,_=b.cradle('DriverMount','DriverW','DriverT','(Width-DriverW)/2','DriverY','DriverZ',posts=driver_posts)
    dr=b.cut('DriverHolder',dr,b.bolt_z('DriverFootHoles',[(f'({x})+Post/2',f'({y})+Post/2') for x,y in driver_posts],-1,'BaseT+7'))
    b.finish(dr,'独立屏幕驱动板托架',GRAY,rotation=(180,0,0))
    bat,_=b.cradle('BatteryTray','BatteryW','BatteryD','(Width-BatteryW)/2','BatteryY','BatteryZ')
    power,_=b.cradle('PowerTray','PowerW','PowerD','(Width-PowerW)/2','PowerY','PowerZ')
    # Feet underneath both low trays reach the base.
    for name,obj,w,d,x,y,z in [('BatteryHolder',bat,'BatteryW','BatteryD','(Width-BatteryW)/2','BatteryY','BatteryZ'),('PowerHolder',power,'PowerW','PowerD','(Width-PowerW)/2','PowerY','PowerZ')]:
        runner_y='SpineY+13+Fit' if name=='PowerHolder' else y
        runner_d=f'({y})+({d})-({runner_y})'
        runners=[b.box(name+'Runner'+str(i),('Post',runner_d,f'({z})-MountFloor-BaseT'),(xx,runner_y,'BaseT')) for i,xx in enumerate((x,f'({x})+({w})-Post'))]
        holder=b.fuse(name+'Raw',[obj]+runners)
        holder=b.cut(name,holder,b.bolt_z(name+'BaseBolt',battery_feet if name=='BatteryHolder' else power_feet,-1,'BaseT+6'))
        b.finish(holder,('电池' if name=='BatteryHolder' else '电源区')+'托盘与底部支撑',GRAY)
    # Carrier spine, independently printable shelves, and their mating through holes.
    spine=b.box('SpineBlank',('SpineW','SpineT','Height-18-BaseT'),('(Width-SpineW)/2','SpineY','BaseT'))
    foot=b.box('SpineFoot',('SpineW',13,3),('(Width-SpineW)/2','SpineY','BaseT'))
    spine=b.fuse('SpineRaw',[spine,foot])
    windows=[b.box('SpineWindow'+str(i),('SpineW-12','SpineT+2',hh),('(Width-SpineW)/2+6','SpineY-1',zz)) for i,(zz,hh) in enumerate([(20,20),(90,20),(140,25)])]
    spine=b.cut('SpineWindows',spine,windows)
    shelf_specs=[('PiShelf','(Width-PiW)/2-Fit-MountT-8','PiW+2*(Fit+MountT)+16','PiY+PiT+Fit+MountT-8','PiZ-MountFloor-ShelfT',False),
                 ('HubShelf','(Width-HubW)/2-Fit-MountT-8','HubW+2*(Fit+MountT)+16','HubY+HubT+Fit+MountT-8','HubZ-MountFloor-ShelfT',False),
                 ('DiskShelf','(Width-DiskW)/2-Fit-MountT-8','DiskW+2*(Fit+MountT)+16','DiskY-Fit-MountT+8','DiskZ-MountFloor-ShelfT',True),
                 ('AudioShelf', '14-Fit-MountT','Width-28+2*(Fit+MountT)', '126+AmpT+Fit+MountT','AudioZ-MountFloor-ShelfT',True)]
    spine_holes=[];shelves={}
    for name,x,w,edge,z,back in shelf_specs:
        sy='SpineY+SpineT' if back else edge
        depth=f'({edge})-SpineY-SpineT' if back else f'SpineY-({edge})'
        flange_y='SpineY+SpineT' if back else 'SpineY-ShelfT'
        base=b.box(name+'Base',(w,depth,'ShelfT'),(x,sy,z))
        flange_x='(Width-SpineW)/2' if name=='DiskShelf' else x
        flange_w='SpineW' if name=='DiskShelf' else w
        flange=b.box(name+'Flange',(flange_w,'ShelfT',20),(flange_x,flange_y,z))
        shelf=b.fuse(name+'Raw',[base,flange])
        xx=(84,150) if name=='AudioShelf' else (f'({x})+12',f'({x})+({w})-12')
        points=[(px,f'({z})+{dz}') for px in xx for dz in ((7,12) if name=='AudioShelf' else (7,15))]
        holes=b.bolt_y(name+'SpineBolt',points,'SpineY-5','SpineT+10')
        shelf=b.cut(name+'Fixing',shelf,holes);spine_holes+=holes
        shelves[name]=shelf
        b.interfaces.append({'name':name+' / 中央板','axis':'Y','centers':points,'note':'孔同源，螺钉/螺母空间及强度未实测'})
    spine=b.cut('CarrierSpine',spine,spine_holes+b.bolt_z('SpineFootBolts',spine_feet,-1,10));b.finish(spine,'中央模块骨架 / 通线窗与底座',GRAY,rotation=(90,0,0))
    trays=[('PiCradle','PiW','PiT','(Width-PiW)/2','PiY','PiZ','PiShelf','both','back'),
           ('HubCradle','HubW','HubT','(Width-HubW)/2','HubY','HubZ','HubShelf','both','back'),
           ('DiskCradle','DiskW','DiskT','(Width-DiskW)/2','DiskY','DiskZ','DiskShelf','both','front'),
           ('AmpCradle','AmpW','AmpT',14,126,'AudioZ','AudioShelf','right','both'),
           ('DacCradle','DacW','DacT','Width-14-DacW',128,'AudioZ','AudioShelf','left','both')]
    shelf_bolts={k:[] for k in shelves}
    for name,w,d,x,y,z,shelf,side,edge in trays:
        cr,pts=b.cradle(name,w,d,x,y,z,tabs=('left' if side=='both' else side,edge))
        if side=='both':
            # Add the opposite ear, keeping its matching hole driven by the same coordinates.
            tx=f'({x})+({w})+Fit+MountT';ty=f'({y})+({d})+Fit+MountT-8' if edge=='back' else f'({y})-Fit-MountT'
            ear=b.box(name+'RightEar',(8,8,'MountFloor'),(tx,ty,f'({z})-MountFloor'))
            pts.append((f'({tx})+4',f'({ty})+4'))
            cr=b.fuse(name+'Ears',[cr,ear]);cr=b.cut(name+'EarHoles',cr,b.bolt_z(name+'SecondHole',pts,f'({z})-MountFloor-6',12))
        shelf_bolts[shelf]+=b.bolt_z(name+'ShelfBolt',pts,f'({z})-MountFloor-ShelfT-1','ShelfT+MountFloor+2')
        b.finish(cr,name+' / 模块托盘',GRAY)
    for name,obj in shelves.items():b.finish(b.cut(name,obj,shelf_bolts[name]),name+' / 可拆托臂',GRAY)
    # Separate side grilles, with rear locating flanges and through slots.
    for side in ('Left','Right'):
        x=.6 if side=='Left' else 'Width-3.6';fx=3 if side=='Left' else 'Width-5'
        plate=b.octagon('Grille'+side+'Face','SpeakerY+6','SpeakerZ+6','SpeakerD-12','SpeakerH-12','SideCut-1','YZ',(x,0,0),3,DARK)
        flange=b.octagon('Grille'+side+'Flange','SpeakerY+3','SpeakerZ+3','SpeakerD-6','SpeakerH-6','SideCut','YZ',(fx,0,0),2,DARK)
        grille=b.fuse('Grille'+side+'Raw',[plate,flange])
        slots=[]
        for i in range(12):
            z=f'SpeakerZ+10+{i}*7.2'
            pts=[('SpeakerY+11',z),('SpeakerY+SpeakerD-11',f'{z}+GrilleRise'),('SpeakerY+SpeakerD-11',f'{z}+GrilleRise+2.8'),('SpeakerY+11',f'{z}+2.8')]
            slots.append(b.prism('Grille'+side+'Slot'+str(i),pts,'YZ',(-1 if side=='Left' else 'Width-6',0,0),7))
        b.finish(b.cut('Grille'+side,grille,slots),side+'侧向格栅 / 背缘定位，卡接待样件',DARK,rotation=(0,-90 if side=='Left' else 90,0))
    # Rear service panel, connectors and heat vents (not speaker ports).
    rear=b.rounded('RearBlank',('Width-2*(Wall+Seam)','Wall','Height-RearDrop-BaseT-Wall-2*Seam'),('Wall+Seam','Depth-Wall','BaseT+Seam'),'EdgeR',1,GRAY)
    holes=b.bolt_y('RearFastener',rear_points,'Depth-8',12)
    holes += [b.cylinder('RcaHole'+str(i),3.8,8,(xx,'Depth-5',48),(0,1,0)) for i,xx in enumerate(('Width-28','Width-14'))]
    holes.append(b.box('UsbPortHole',(10,8,4),('Width-35','Depth-5',25)))
    holes += [b.rounded('RearVent'+str(i),(70,8,2),('(Width-70)/2','Depth-5',f'Height-28+{i}*5'),.8,1) for i in range(3)]
    b.finish(b.cut('RearPanel',rear,holes),'可拆接口后盖 / 独立散热孔',GRAY,rotation=(-90,0,0))
    knob=b.cylinder('KnobCap',10,6,('Width-38',0,18),(0,-1,0),ORANGE);b.finish(knob,'主旋钮打印帽 / 编码器未选',ORANGE,rotation=(90,0,0))
    for i in range(3):b.finish(b.cylinder('Button'+str(i),2.7,2,('Width-'+str(104-i*16),0,18),(0,-1,0)),f'控制按键帽 {i+1}',(.25,.29,.31),rotation=(90,0,0))
    accent=b.box('AccentBadge',(28,1.2,2),(22,-1.2,18),ORANGE);b.finish(accent,'识别色条 / 无状态功能含义',ORANGE,rotation=(90,0,0))
    b.finish(b.box('Display',('ActiveW',.4,'ActiveH'),('(Width-ActiveW)/2',7.8,'LowerBand+(ScreenH-ActiveH)/2'),(.10,.19,.23)),'显示可视面 / 无UI实现含义',(.1,.19,.23),'Standard')
    for i,(xx,cc) in enumerate([('Width-28',(.9,.9,.82)),('Width-14',(.7,.15,.1))]):
        b.finish(b.cylinder('Rca'+str(i),3.5,4,(xx,'Depth',48),(0,1,0),cc),'RCA线路输出位置示意',cc,'Standard')
    for i,(xx,zz) in enumerate(screen_points):
        b.finish(b.cylinder('ScreenBoltHead'+str(i),2.8,1,(xx,'FaceInset-1',zz),(0,1,0),SILVER),'屏框连接螺钉头示意',SILVER,'Standard')
    # Keep-outs and physical access checks are separate from presentation geometry.
    b.groups['Clearances'].addObject(b.box('DisplayClearance',('ActiveW',8.8,'ActiveH'),('(Width-ActiveW)/2',-1,'LowerBand+(ScreenH-ActiveH)/2')))
    lane=[('Depth-Wall-CableD','BaseT+7'),('Depth-Wall','BaseT+7'),
          ('Depth-Wall','Height-Wall-RearDrop*(RearRun-Wall)/RearRun-Seam'),
          ('Depth-Wall-CableD','Height-Wall-RearDrop*(RearRun-Wall-CableD)/RearRun-Seam')]
    b.groups['Clearances'].addObject(b.prism('CableLane',lane,'YZ',('Wall+12',0,0),'Width-2*(Wall+12)'))
    doc.recompute()
    # All construction objects are hidden; final parts are explicit, single-solid outputs.
    for obj in b.groups['Construction'].Group + b.groups['Clearances'].Group:obj.Visibility=False
    for obj in doc.Objects:
        if obj.TypeId=='App::Origin':obj.Visibility=False
    doc.addObject('App::FeaturePython','ModelInfo')
    info=doc.ModelInfo;info.addProperty('App::PropertyString','Status');info.Status='参数化打印分件草案；未实物试装/打印/热/声学验证'
    info.addProperty('App::PropertyString','InterfaceNotes');info.InterfaceNotes=json.dumps(b.interfaces,ensure_ascii=False)
    # Store no Python proxy: this metadata object only holds strings.
    refresh(doc,root)
    return doc


def refresh(doc,root):
    out=Path(root)/'cad/terminal'
    doc.recompute();report=validate(doc)
    if report['errors']:raise RuntimeError(json.dumps(report,ensure_ascii=False))
    for obj in list(doc.Presentation.Group):doc.removeObject(obj.Name)
    export_package(doc,out);make_presentations(doc);previews(doc,out)
    doc.recompute();doc.saveAs(str(out/'vintrox-terminal.FCStd'))
    report['parts']=parts_manifest(doc);report['saved_readback_required']=True
    (out/'terminal-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


def physical(doc):return list(doc.Printed.Group)+list(doc.Hardware.Group)+list(doc.Standard.Group)

def validate(doc):
    errors=[];objects=physical(doc);printed=list(doc.Printed.Group);hardware=list(doc.Hardware.Group)
    for obj in objects:
        if obj.Shape.isNull() or not obj.Shape.isValid() or len(obj.Shape.Solids)!=1:errors.append('无效或非单实体: '+obj.Name)
        if 'Invalid' in obj.State:errors.append('重计算失败: '+obj.Name)
    if errors:return {'errors':errors}
    p=doc.Parameters;outside=[]
    for obj in hardware:
        bounds=obj.Shape.optimalBoundingBox(False,False)
        if any(getattr(bounds,axis+'Min') < -1e-6 or getattr(bounds,axis+'Max') > limit+1e-6
               for axis,limit in [('X',float(p.Width)),('Y',float(p.Depth)),('Z',float(p.Height))]):
            outside.append({'name':obj.Name,'min_xyz_mm':[bounds.XMin,bounds.YMin,bounds.ZMin],
                            'max_xyz_mm':[bounds.XMax,bounds.YMax,bounds.ZMax]})
    if outside:errors.append('硬件超出机身边界')
    clashes=[]
    # No overlap exemption between separate printed parts or hardware envelopes.
    tested=printed+hardware
    for i,a in enumerate(tested):
        for c in tested[i+1:]:
            aa=a.Shape.BoundBox;bb=c.Shape.BoundBox
            if min(aa.XMax,bb.XMax)-max(aa.XMin,bb.XMin)<1e-5 or min(aa.YMax,bb.YMax)-max(aa.YMin,bb.YMin)<1e-5 or min(aa.ZMax,bb.ZMax)-max(aa.ZMin,bb.ZMin)<1e-5:continue
            volume=a.Shape.common(c.Shape).Volume
            if volume>.01:clashes.append({'a':a.Name,'b':c.Name,'volume_mm3':round(volume,3)})
    if clashes:errors.append('分件/硬件相交')
    keepouts={}
    for name in ('DisplayClearance','CableLane'):
        hits=[];test=doc.getObject(name).Shape
        for obj in printed:
            v=obj.Shape.common(test).Volume
            if v>.01:hits.append({'part':obj.Name,'volume_mm3':round(v,3)})
        if name=='CableLane':
            for obj in hardware:
                v=obj.Shape.common(test).Volume
                if v>.01:hits.append({'hardware':obj.Name,'volume_mm3':round(v,3)})
        keepouts[name]=hits
        if hits:errors.append('侵入净空: '+name)
    p=doc.Parameters
    slot=doc.SlotTool.Shape.BoundBox.Center;drive=doc.OpticalDrive.Shape.BoundBox.Center
    slot_offset=[round(slot.x-drive.x,6),round(slot.y-drive.y,6)]
    if any(abs(v)>1e-6 for v in slot_offset):errors.append('顶部槽口偏心')
    # A printed surface must not close the slot's exact cut volume.
    blocked=sum(o.Shape.common(doc.SlotTool.Shape).Volume for o in printed if o.Name not in ('DriveMount',))
    if blocked>.01:errors.append('进碟槽被打印件封堵')
    bb=[o.Shape.optimalBoundingBox(False,False) for o in objects]
    overall={key:round(max(getattr(v,axis+'Max') for v in bb)-min(getattr(v,axis+'Min') for v in bb),3) for key,axis in [('width','X'),('depth','Y'),('height','Z')]}
    return {'status':'分件/占位草案；未打印或实测','body_mm':{'width':float(p.Width),'height':float(p.Height),'depth':float(p.Depth)},'overall_mm':overall,'printed_parts':len(printed),'hardware_envelopes':len(hardware),'assembly_solids':len(objects),'intersections':clashes,'hardware_outside_body':outside,'keepouts':keepouts,'slot_offset_xy_mm':slot_offset,'slot_blocked_mm3':round(blocked,6),'errors':errors,'scope':'静态简化实体；标准接口/螺钉头仅示意，不证明线缆、螺母、孔配合、强度、散热或声学通过。'}


def print_shape(obj):
    angles=obj.ExportRotation
    rot=App.Rotation(angles.z,angles.y,angles.x)
    shape=obj.Shape.copy();shape.transformShape(App.Placement(App.Vector(),rot).toMatrix(),True)
    bb=shape.optimalBoundingBox(False,False);shape.translate(App.Vector(-bb.XMin,-bb.YMin,-bb.ZMin))
    return shape


def parts_manifest(doc):
    records=[];p=doc.Parameters
    for obj in doc.Printed.Group:
        shape=print_shape(obj);bb=shape.optimalBoundingBox(False,False)
        fits=bb.XLength<=float(p.PrintX) and bb.YLength<=float(p.PrintY) and bb.ZLength<=float(p.PrintZ)
        records.append({'id':obj.PartID,'name':obj.Name,'label':obj.Label,'print_bounds_mm':[round(bb.XLength,3),round(bb.YLength,3),round(bb.ZLength,3)],'assumed_256_cube_fit':fits,'rotation_xyz_deg':list(obj.ExportRotation),'note':'方向为初步建议，未验证支撑/翘曲/层间强度；成型空间是假设'})
    return records


def export_package(doc,out):
    import MeshPart
    Part.export(physical(doc),str(out/'vintrox-terminal.step'))
    for obj in doc.Printed.Group:
        shape=print_shape(obj)
        stem=obj.PartID+'-'+obj.Name
        shape.exportStep(str(out/'parts'/(stem+'.step')))
        mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.12,AngularDeflection=.25,Relative=False)
        mesh.write(str(out/'parts'/(stem+'.stl')))
    records=parts_manifest(doc)
    (out/'parts.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    with (out/'parts.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f,lineterminator='\n');writer.writerow(['ID','Name','Label','X_mm','Y_mm','Z_mm','Status'])
        for r in records:writer.writerow([r['id'],r['name'],r['label'],*r['print_bounds_mm'],'ASSUMED / UNTESTED'])


def make_presentations(doc):
    # Native links retain source geometry after recomputation; offsets are presentation only.
    for i,obj in enumerate(doc.Printed.Group):
        link=doc.addObject('App::Link','Exploded_'+obj.Name);link.LinkedObject=obj;link.LinkTransform=True
        name=obj.Name
        if name=='FrontBezel':offset=(0,-65,10)
        elif name in ('ControlPanel','ControlMount'):offset=(0,-70,-5)
        elif name.startswith('LeftShell'):offset=(-65,0,0)
        elif name.startswith('RightShell'):offset=(65,0,0)
        elif name=='TopCap' or name=='SlotTrim':offset=(0,0,65)
        elif name=='RearPanel':offset=(0,65,0)
        elif name=='BaseTray' or name.startswith('Foot'):offset=(0,0,-50)
        elif name.startswith('GrilleLeft'):offset=(-95,0,0)
        elif name.startswith('GrilleRight'):offset=(95,0,0)
        else:offset=(0,0,0)
        link.LinkPlacement=App.Placement(App.Vector(*offset),App.Rotation())
        doc.Presentation.addObject(link);link.Visibility=False
        # Flat, oriented contact-sheet solids; only this view is a static regenerated presentation.
        tile=doc.addObject('Part::Feature','Tile_'+obj.Name);tile.Shape=print_shape(obj)
        col=i%7;row=i//7;tile.Placement.Base=tile.Placement.Base+App.Vector(col*260,-row*250,0)
        tile.ViewObject.ShapeColor=obj.ViewObject.ShapeColor;doc.Presentation.addObject(tile);tile.Visibility=False
        annotation=doc.addObject('App::Annotation','Label_'+obj.Name);annotation.LabelText=[obj.PartID]
        annotation.Position=App.Vector(col*260+10,-row*250-18,0)
        annotation.ViewObject.FontSize=15;annotation.ViewObject.TextColor=(.1,.1,.1)
        doc.Presentation.addObject(annotation);annotation.Visibility=False
    doc.recompute()


def scene(doc,kind):
    for obj in physical(doc):
        obj.Visibility=True;obj.ViewObject.Transparency=0
    for obj in doc.Construction.Group+doc.Clearances.Group+doc.Presentation.Group:obj.Visibility=False
    if kind=='interior':
        for obj in doc.Printed.Group:
            if obj.Name in ('TopCap','SlotTrim','RightShell','RearPanel','GrilleRight'):obj.Visibility=False
        doc.Disk.Visibility=False
        doc.CarrierSpine.ViewObject.Transparency=75
    elif kind=='hardware':
        for obj in doc.Printed.Group+doc.Standard.Group:obj.Visibility=False
        for obj in (doc.ScreenPanel,doc.ScreenRibbonBoard,doc.ScreenDriver,doc.SpeakerRight,doc.Disk):obj.Visibility=False
    elif kind=='exploded':
        for obj in doc.Printed.Group+doc.Standard.Group:obj.Visibility=False
        for obj in doc.Presentation.Group:
            if obj.Name.startswith('Exploded_'):obj.Visibility=True
    elif kind=='parts':
        for obj in physical(doc):obj.Visibility=False
        for obj in doc.Presentation.Group:
            if obj.Name.startswith(('Tile_','Label_')):obj.Visibility=True


def previews(doc,out):
    import FreeCADGui as Gui
    App.setActiveDocument(doc.Name);view=Gui.activeDocument().activeView()
    def camera(eye):
        z=App.Vector(*eye);z.normalize();x=App.Vector(0,0,1).cross(z);x.normalize();return App.Rotation(x,z.cross(x),z,'ZXY').Q
    for kind,eye in [('exterior',(1,-1.8,.6)),('interior',(1,1.4,1.4)),('hardware',(1,1.8,1)),('exploded',(1,-1.7,1.2)),('parts',None)]:
        scene(doc,kind)
        if eye:view.setCameraOrientation(camera(eye))
        else:view.viewTop()
        view.fitAll();Gui.updateGui()
        cam=view.getCamera();cam=re.sub(r'(height\s+)([0-9.eE+-]+)',lambda m:m.group(1)+str(float(m.group(2))*1.12),cam);view.setCamera(cam)
        view.saveImage(str(out/'previews'/(kind+'.png')),1800,1300,'White')
    scene(doc,'exterior');view.setCameraOrientation(camera((1,-1.8,.6)));view.fitAll();Gui.updateGui()
