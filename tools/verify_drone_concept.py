"""Read saved appearance CAD and STEP independently; never save through headless.

Run with FreeCAD's bundled Python and library PYTHONPATH, as documented in
docs/drone-concept.md. This checks static deliverables, not manufacturing fit.
"""
from pathlib import Path
import hashlib
import json
import math
import re
from xml.etree import ElementTree
from zipfile import ZipFile

import FreeCAD as App
import Part


def verify(root):
    """Validate saved solids, screen inputs, bass reservation, and STEP parity."""
    out = Path(root)/'cad/drone-concept'
    cad = out/'vintrox-drone-concept.FCStd'
    step = out/'vintrox-drone-concept.step'
    manifest = json.loads((out/'concept-manifest.json').read_text())
    errors = []
    digest = hashlib.sha256(cad.read_bytes()).hexdigest()
    if digest != manifest['fcstd_sha256']:
        errors.append('Saved FCStd hash differs from concept manifest')
    with ZipFile(cad) as archive:
        gui = ElementTree.fromstring(archive.read('GuiDocument.xml'))
        visible_names = {node.attrib['name'] for node in gui.findall('.//ViewProvider')
                         if node.find('./Properties/Property[@name="Visibility"]/Bool') is not None
                         and node.find('./Properties/Property[@name="Visibility"]/Bool').get('value') == 'true'}
    doc = App.openDocument(str(cad))
    try:
        objects = [doc.getObject(entry['name']) for entry in manifest['features']]
        invalid = [entry['name'] for entry, obj in zip(manifest['features'], objects)
                   if obj is None or not obj.Shape.isValid() or not obj.Shape.Solids]
        if invalid:
            raise RuntimeError('Invalid saved features: '+str(invalid))
        visible = [obj for obj in objects if obj.Name in visible_names]
        if len(visible) != manifest['visible_features']:
            errors.append('Saved GUI visibility count differs from manifest')
        groups = [o.Name for o in doc.Objects if o.TypeId == 'App::DocumentObjectGroup']
        non_chinese = [o.Name for o in doc.Objects if not re.search(r'[\u4e00-\u9fff]', o.Label)
                       or re.search(r'[A-Za-z]', o.Label)]
        if groups or non_chinese:
            errors.append('Expected a flat tree and Chinese labels for all objects')
        panel = doc.getObject('ScreenPanel210x160x2')
        screen_dims = [panel.Length.Value, panel.Height.Value, panel.Width.Value]
        if screen_dims != [210, 160, 2]:
            errors.append('Measured screen dimensions changed')
        active = doc.getObject('ActiveArea200x150')
        if [active.Length.Value, active.Height.Value] != [200, 150]:
            errors.append('Specified active area changed')
        cover = doc.getObject('ScreenCurvedCover')
        if cover is None or cover.Shape.common(panel.Shape).Volume > .001 or cover.Shape.common(active.Shape).Volume > .001:
            errors.append('Curved visual cover is missing or intersects the flat display')
        reserve = doc.getObject('WooferEnvelope_D88_Depth40')
        if [reserve.AssumedDiameter.Value, reserve.AssumedDepth.Value] != [88, 40]:
            errors.append('Bass placeholder dimensions changed')
        reserve_shell_overlap = reserve.Shape.common(doc.getObject('BassNozzleShell').Shape).Volume
        if reserve_shell_overlap > .01:
            errors.append('Bass placeholder intersects nozzle shell')
        restored_modules = {}
        for prefix in ('FrontCheek', 'CheekDial', 'VentBacking', 'CheekPerforatedPanel',
                       'UtilityBarrel', 'UtilityCap', 'UtilityIndicator', 'SideCable'):
            restored_modules[prefix] = [o.Name for o in visible
                                         if o.Name in (prefix+'Left',prefix+'Right')]
            expected_count = 1 if prefix.startswith(('Utility', 'SideCable')) else 2
            if len(restored_modules[prefix]) != expected_count:
                errors.append('Missing restored reference assembly: '+prefix)
        shafts = [obj for obj in objects if obj.Name.startswith('SupportShaft')]
        feet = [obj for obj in objects if obj.Name.startswith('SupportFoot')]
        sockets = [obj for obj in objects if obj.Name.startswith('SupportSocket')]
        old_supports = [o.Name for o in doc.Objects if o.Name.startswith('RearSupport')]
        if len(shafts) != 4 or len(feet) != 4 or len(sockets) != 4 or old_supports:
            errors.append('Expected four shafts, sockets and feet with old rear feet removed')
        support_details = []
        seat = doc.getObject('CentralSupportSeat')
        if seat is None:
            errors.append('Missing central support seat')
        else:
            if seat.Shape.common(doc.getObject('ClosedBellyPan').Shape).Volume < 1:
                errors.append('Central support seat is detached from belly pan')
            for shaft in shafts:
                suffix = shaft.Name[len('SupportShaft'):]
                foot = doc.getObject('SupportFoot'+suffix)
                socket = doc.getObject('SupportSocket'+suffix)
                root, tip = shaft.RootCentre, shaft.FootCentre
                length = (tip-root).Length
                radii = [face.Surface.Radius for face in shaft.Shape.Faces
                         if type(face.Surface).__name__ == 'Cylinder']
                if len(radii) != 1 or abs(radii[0]-3) > 1e-6:
                    errors.append('Expected a smooth 6 mm cylinder: '+shaft.Name)
                if abs(shaft.Shape.Volume-math.pi*9*length) > .01:
                    errors.append('Shaft length differs from saved endpoints: '+shaft.Name)
                if not (abs(root.x) < 42 and 55 < root.y < 125 and root.z > tip.z
                        and abs(tip.x) > abs(root.x)
                        and abs(tip.y-90) > abs(root.y-90)):
                    errors.append('Shaft does not splay downward from the centre: '+shaft.Name)
                if (not seat.Shape.isInside(root, .01, True) or foot is None or socket is None
                        or shaft.Shape.common(foot.Shape).Volume < .01
                        or seat.Shape.common(socket.Shape).Volume < .01):
                    errors.append('Disconnected support detail: '+shaft.Name)
                # Only the mounting region, sleeve and pad may meet the shaft.
                intentional = {shaft.Name, 'CentralSupportSeat', 'ClosedBellyPan',
                               socket.Name if socket else '', foot.Name if foot else ''}
                clashes = [obj.Name for obj in visible if obj.Name not in intentional
                           and shaft.Shape.common(obj.Shape).Volume > .01]
                if clashes:
                    errors.append('Shaft intersects unrelated geometry: '+str(clashes))
                support_details.append({'name': shaft.Name, 'diameter_mm': 6,
                                        'length_mm': length,
                                        'root_mm': list(root), 'tip_mm': list(tip)})
        ground_levels = [foot.Shape.BoundBox.ZMin for foot in feet]
        if len(ground_levels) != 4 or any(abs(z+100) > .01 for z in ground_levels):
            errors.append('Four foot pads must share the assumed Z=-100 mm plane')
        # Targeted regressions for the reported open side/back surfaces. These
        # samples do not claim airtightness, waterproofing, or a fitted assembly.
        closure_samples = []
        shell = doc.getObject('MainEnclosureShell')
        for side in (-1, 1):
            for y in (50, 100, 150):
                for z in (90, 160, 230):
                    point = App.Vector(side*118*.84, y*1.25, z*.84+24)
                    closure_samples.append(shell.Shape.isInside(point, .01, True))
        back = Part.makeCompound([doc.getObject('RearServicePanel').Shape,
                                  doc.getObject('RearLowerSlope').Shape])
        for x in (-95, 95):
            for z in (75, 150, 220):
                height=z*.84+24
                depth=150+(height-58)*78/68-2 if height < 126 else 179*1.25
                closure_samples.append(back.isInside(App.Vector(x*.84, depth, height), .01, True))
        if not all(closure_samples):
            errors.append('Missing side/back shell material at a closure probe')
        # Inspect the saved tube end caps, not generator coordinates. A local
        # overlap confirms visual attachment only, not a manufactured joint.
        loop_body = Part.makeCompound([doc.getObject(name).Shape for name in
                                       ('MainEnclosureShell', 'BottomChassis',
                                        'ClosedBellyPan', 'RearLowerSlope')])
        loop_connections = []
        for name in ('UnderbodyLoop0', 'UnderbodyLoop1'):
            loop = doc.getObject(name)
            # Affine-transformed caps may be represented as B-splines.
            caps = [face for face in loop.Shape.Faces if face.findPlane(1e-6) is not None]
            if len(caps) != 2:
                errors.append('Expected two underbody loop end caps: '+name)
            for cap in caps:
                centre = cap.CenterOfMass
                overlap = loop.Shape.common(Part.makeSphere(12, centre)).common(loop_body).Volume
                loop_connections.append({'name': name, 'end_centre_mm': list(centre),
                                         'probe_radius_mm': 12, 'body_overlap_mm3': overlap})
                if overlap <= .1:
                    errors.append('Detached underbody loop end: '+name+' '+str(list(centre)))
        nozzle = doc.getObject('BassNozzleShell')
        curved_faces = sum(type(face.Surface).__name__ == 'BSplineSurface' for face in nozzle.Shape.Faces)
        if curved_faces == 0:
            errors.append('Nozzle lost its smooth lofted fairing')
        petals = [obj for obj in objects if re.fullmatch(r'NozzlePetal\d+', obj.Name)]
        if len(petals) != 12 or len(petals) != manifest['nozzle_petals']:
            errors.append('Expected 12 separately modelled curved nozzle petals')
        # Every component must remain volumetric in FCStd/STEP, independent of
        # Blender materials or edge highlights. Graphics also have real depth.
        non_solid_components = [obj.Name for obj in objects
                                if any(not s.isClosed() or s.Volume <= 1e-7 for s in obj.Shape.Solids)]
        if non_solid_components:
            errors.append('Open or zero-volume component: '+str(non_solid_components))
        detail_depths = {}
        shoulder_bolt_connections = {}
        for side in ('Left','Right'):
            bolt = doc.getObject('HoodShoulderBolt'+side)
            plate = doc.getObject('HoodShoulderPlate'+side)
            overlap = bolt.Shape.common(plate.Shape).Volume
            shoulder_bolt_connections[side] = overlap
            if overlap < .01:
                errors.append('Detached hood shoulder bolt: '+side)
        hood_mark_gaps = {}
        for mark in (o for o in objects if o.Name.startswith('HoodMark')):
            side = 'Left' if mark.Shape.CenterOfMass.x < 0 else 'Right'
            gap = mark.Shape.distToShape(doc.getObject('HoodShoulderCrown'+side).Shape)[0]
            hood_mark_gaps[mark.Name] = gap
            if gap > .01:
                errors.append('Hood stripe detached from curved crown: '+mark.Name)
        side_frame_bolt_gaps = {}
        side_frame_bolt_targets = {}
        side_frame_connections = {}
        spine_holes = []
        for sign,side in ((-1,'Left'),(1,'Right')):
            frame = doc.getObject('SideGuard'+side).Shape
            shoe = doc.getObject('SideFrameShoe'+side).Shape
            side_frame_connections[side]={
                'shoe_frame_overlap_mm3':shoe.common(frame).Volume,
                'light_frame_overlap_mm3':doc.getObject('CyanSideTube'+side).Shape.common(frame).Volume,
                'frame_closure_gap_mm':frame.distToShape(doc.getObject('SideClosure'+side).Shape)[0]}
            if (side_frame_connections[side]['shoe_frame_overlap_mm3']<=.01 or
                side_frame_connections[side]['light_frame_overlap_mm3']<=.01 or
                side_frame_connections[side]['frame_closure_gap_mm']>.01):
                errors.append('Detached side frame, light or recessed service plate: '+side)
            for i in range(4):
                name = f'SideFrameBolt{side}{i}'
                target = 'SideFrameShoe'+side if i<2 else 'SideGuard'+side
                gap = doc.getObject(name).Shape.distToShape(doc.getObject(target).Shape)[0]
                side_frame_bolt_gaps[name] = gap
                side_frame_bolt_targets[name] = target
                if gap > .01:
                    errors.append('Side frame bolt detached from its mounting face: '+name)
            spine = doc.getObject('SideFrontSpine'+side).Shape
            spine_plane_x=spine.optimalBoundingBox(False,False).Center.x
            for row in range(7):
                for col in range(4):
                    y,z = 42+col*6,80+row*4
                    reprojection=manifest.get('side_profile_reprojection')
                    scale=reprojection['scale'] if reprojection else 1
                    if reprojection:
                        ey,ez=reprojection['eye_mm'][1:]
                        y,z=ey+scale*(y-ey),ez+scale*(z-ez)
                    hole_open = not spine.isInside(App.Vector(spine_plane_x,y,z),.001,True)
                    web_present = spine.isInside(App.Vector(spine_plane_x,y+2.5*scale,z+2*scale),.001,True)
                    spine_holes.append(hole_open and web_present)
        if not all(spine_holes):
            errors.append('Side spine perforations or surrounding material missing')
        cheek_connections = {}
        for side in ('Left','Right'):
            cheek=doc.getObject('FrontCheek'+side).Shape
            bridge=doc.getObject('FrontCheekBridge'+side).Shape
            spine=doc.getObject('SideFrontSpine'+side).Shape
            overlap=cheek.common(bridge).Volume
            gap=bridge.distToShape(spine)[0]
            cheek_connections[side]={'cheek_bridge_overlap_mm3':overlap,'bridge_spine_gap_mm':gap}
            if overlap < .01 or gap > .01:
                errors.append('Detached front cheek bridge: '+side)
        control_end_overlaps={}
        for side in ('Left','Right'):
            overlap=doc.getObject('ControlRailEnd'+side).Shape.common(doc.getObject('ControlRail').Shape).Volume
            control_end_overlaps[side]=overlap
            if overlap < .01:
                errors.append('Control rail end detached from rail: '+side)
        for prefix, axis, minimum in [('WingPaint','X',2.8),('WingSpine','X',3.4),
                                     ('HoodShoulderPlate','X',3.5),('RearArmourCheek','Y',8)]:
            for side in ('Left','Right'):
                obj = doc.getObject(prefix+side)
                depth = getattr(obj.Shape.BoundBox, axis+'Length') if obj else 0
                detail_depths[prefix+side] = depth
                if depth < minimum:
                    errors.append('Armour lost its modeled relief: '+prefix+side)
        wing_connections={}
        if any(o.Name.startswith('WingHubBolt') for o in objects):
            errors.append('Unsupported exposed screws on the wing hub marking')
        for side in ('Left','Right'):
            blade=doc.getObject('WingEdge'+side).Shape
            raised=doc.getObject('WingRaisedFace'+side).Shape
            paint=doc.getObject('WingPaint'+side).Shape
            fold=doc.getObject('WingFoldFacet'+side).Shape
            wing_connections[side]={
                'paint_raised_overlap_mm3':paint.common(raised).Volume,
                'raised_blade_gap_mm':raised.distToShape(blade)[0],
                'fold_blade_overlap_mm3':fold.common(blade).Volume,
                'inner_blade_gap_mm':doc.getObject('WingInnerPaint'+side).Shape.distToShape(blade)[0],
                'mark_paint_gap_mm':doc.getObject('WingHubMark'+side).Shape.distToShape(paint)[0]}
            if (wing_connections[side]['paint_raised_overlap_mm3']<=.01 or
                wing_connections[side]['fold_blade_overlap_mm3']<=.01 or
                max(wing_connections[side][k] for k in ('raised_blade_gap_mm','inner_blade_gap_mm','mark_paint_gap_mm'))>.01):
                errors.append('Detached curved wing layers: '+side)
        handle_connections={}
        for side in ('Left','Right'):
            arm=doc.getObject('HandleArm'+side).Shape
            inset=doc.getObject('HandleInset'+side).Shape
            grip=doc.getObject('HandleGrip').Shape
            cuff=doc.getObject('HandleGripCuff'+side).Shape
            inset_overlap=inset.common(arm).Volume
            gaps=[arm.distToShape(grip)[0],cuff.distToShape(grip)[0]]
            marks=[doc.getObject(f'HandleMark{side}{i}').Shape.common(inset).Volume for i in range(3)]
            body_overlap=arm.common(doc.getObject('SideClosure'+side).Shape).Volume
            handle_connections[side]={'inset_arm_overlap_mm3':inset_overlap,
                'grip_joint_gaps_mm':gaps,'mark_inset_overlap_mm3':marks,
                'arm_sidewall_overlap_mm3':body_overlap}
            if inset_overlap<=.01 or max(gaps)>.01 or min(marks)<=.01 or body_overlap<=.01:
                errors.append('Detached handle surface or grip joint: '+side)
        roof_parts=[o.Shape for o in objects if o.Name.startswith(('SlopedUpperArmour','RoofSideClosure'))]
        rim=doc.getObject('InstrumentRim').Shape
        panel=doc.getObject('TopInstrumentPanel').Shape
        mount=doc.getObject('InstrumentMount').Shape
        access=doc.getObject('RoofAccessPanel').Shape
        roof_connections={'rim_panel_overlap_mm3':rim.common(panel).Volume,
            'rim_mount_overlap_mm3':rim.common(mount).Volume,
            'mount_roof_overlap_mm3':sum(mount.common(s).Volume for s in roof_parts),
            'access_roof_overlap_mm3':sum(access.common(s).Volume for s in roof_parts),
            'side_cap_gap_mm':[doc.getObject('SlopedUpperArmour').Shape.distToShape(o.Shape)[0]
                               for o in objects if o.Name.startswith('RoofSideClosure')]}
        if any(roof_connections[k]<=.01 for k in ('rim_panel_overlap_mm3','rim_mount_overlap_mm3',
                'mount_roof_overlap_mm3','access_roof_overlap_mm3')) or max(roof_connections['side_cap_gap_mm'])>.01:
            errors.append('Detached rounded roof or instrument assembly')
        rail=doc.getObject('RearPortRail').Shape
        carrier=doc.getObject('RearRailCarrier').Shape
        seat=doc.getObject('RearRailBezel').Shape
        slider=doc.getObject('RearRedInsert').Shape
        rear_connections={'panel_carrier_overlap_mm3':rail.common(carrier).Volume,
            'carrier_shell_overlap_mm3':carrier.common(doc.getObject('RearServicePanel').Shape).Volume,
            'seat_panel_overlap_mm3':seat.common(rail).Volume,
            'slider_seat_overlap_mm3':slider.common(seat).Volume,
            'index_slider_overlap_mm3':doc.getObject('RearRailIndex').Shape.common(slider).Volume,
            'vent_inlay_overlap_mm3':[doc.getObject(f'RearRailVent{i}').Shape.common(rail).Volume for i in range(7)]}
        if any(rear_connections[k]<=.001 for k in ('panel_carrier_overlap_mm3','carrier_shell_overlap_mm3',
                'seat_panel_overlap_mm3','slider_seat_overlap_mm3','index_slider_overlap_mm3')) or min(rear_connections['vent_inlay_overlap_mm3'])<=.001:
            errors.append('Detached rear panel or slider detail')
        cavities=[rail.common(Part.makeSphere(.15,App.Vector(42+i*2.25,247.66106424,210.93081714))).Volume for i in range(7)]
        rear_connections['vent_cavity_overlap_mm3']=cavities
        if max(cavities)>1e-6:errors.append('Rear vertical slots lost their physical recess')
        rear_connections['beacons']=[]
        for side in (-1,1):
            def lamp(prefix):
                return next(o.Shape for o in objects if o.Name.startswith(prefix) and o.Shape.optimalBoundingBox(False,False).Center.x*side>0)
            body=next(o.Shape for o in objects if re.fullmatch(r'RearBeacon_?\d+',o.Name) and o.Shape.optimalBoundingBox(False,False).Center.x*side>0)
            base=lamp('RearBeaconBase');lens=lamp('RearBeaconLens')
            bands=[o.Shape for o in objects if o.Name.startswith('RearBeaconBand') and o.Shape.optimalBoundingBox(False,False).Center.x*side>0]
            gaps=[body.distToShape(base)[0],lens.distToShape(body)[0]]
            overlaps=[s.common(body).Volume for s in bands]
            rear_connections['beacons'].append({'side':side,'joint_gap_mm':gaps,'band_body_overlap_mm3':overlaps})
            if len(bands)!=3 or max(gaps)>.01 or min(overlaps)<=.01:errors.append('Detached beacon body or rings')
        hinges = [obj for obj in objects if re.fullmatch(r'NozzlePetalHinge\d+',obj.Name)]
        if len(hinges) != 12:
            errors.append('Missing independent nozzle petal hinges')
        nozzle_detail_connections=[]
        for i in range(12):
            petal=doc.getObject(f'NozzlePetal{i}').Shape
            ridge=doc.getObject(f'NozzlePetalRidge{i}').Shape
            hem=doc.getObject(f'NozzlePetalEndHem{i}').Shape
            gaps=[ridge.distToShape(petal)[0],hem.distToShape(petal)[0]]
            gaps.append(doc.getObject(f'NozzlePetalInset{i}').Shape.distToShape(petal)[0])
            gaps.extend(doc.getObject(f'NozzlePetalGuide{i}_{j}').Shape.distToShape(ridge)[0] for j in range(2))
            root_overlap=petal.common(doc.getObject('BassNozzleMouthRing').Shape).Volume
            nozzle_detail_connections.append({'petal':i,'detail_gaps_mm':gaps,'root_roll_overlap_mm3':root_overlap})
            if max(gaps)>.01 or root_overlap<=.01:
                errors.append('Detached nozzle panel detail or root: '+str(i))
        warning_overlap=doc.getObject('BassWarningPlaque').Shape.common(doc.getObject('BassNozzleShell').Shape).Volume
        if warning_overlap<=.1:errors.append('Nozzle warning plaque detached after shell reshaping')
        lower_petals=[o for o in objects if o.Name.startswith('LowerPodRib')]
        lower_edges=[o for o in objects if o.Name.startswith('LowerPodEdgeRail')]
        if len(lower_petals)!=36 or len(lower_edges)!=72:
            errors.append('Missing small exhaust petals or solid edge rails')
        lower_petal_compound=Part.makeCompound([o.Shape for o in lower_petals])
        lower_edge_gaps={o.Name:o.Shape.distToShape(lower_petal_compound)[0] for o in lower_edges}
        if any(gap>.01 for gap in lower_edge_gaps.values()):
            errors.append('Detached small exhaust petal edge rail')
        lower_connections={}
        for obj in (o for o in objects if re.fullmatch(r'LowerPod_\w+',o.Name)
                    and not o.Name.startswith(('LowerPodRib','LowerPodRim'))):
            # Belly parts intentionally overlap. Intersecting their unfused
            # compound can return an empty Boolean; inspect each saved part.
            overlap={n:obj.Shape.common(doc.getObject(n).Shape).Volume for n in
                     ('MainEnclosureShell','BottomChassis','ClosedBellyPan','RearLowerSlope')}
            lower_connections[obj.Name]=overlap
            if max(overlap.values())<=.1:errors.append('Small exhaust shell detached from belly: '+obj.Name)
        if len(lower_connections)!=2:errors.append('Expected two small exhaust shell connection checks')
        side_ring_connections={}
        for side in ('Left','Right'):
            hub=doc.getObject('SpeakerHubNeck'+side).Shape
            lip=doc.getObject('SpeakerOuterLip'+side).Shape
            flange=doc.getObject('PerforatedSpeakerFlange'+side).Shape
            connections={
                'hub_wing_overlap_mm3':hub.common(doc.getObject('WingEdge'+side).Shape).Volume,
                'hub_cone_overlap_mm3':hub.common(doc.getObject('SpeakerVisualCone'+side).Shape).Volume,
                'hub_paint_overlap_mm3':hub.common(doc.getObject('WingPaint'+side).Shape).Volume,
                'seal_body_overlap_mm3':doc.getObject('SpeakerRearSeal'+side).Shape.common(shell.Shape).Volume,
                'lip_flange_overlap_mm3':lip.common(flange).Volume,
                'flange_solid_count':len(flange.Solids),
                'bridge_wire_flange_overlap_mm3':[doc.getObject(f'SpeakerBridgeWire{side}{i}').Shape.common(flange).Volume
                                                  for i in range(2)]}
            if min(connections[k] for k in ('hub_wing_overlap_mm3','hub_cone_overlap_mm3',
                                           'seal_body_overlap_mm3','lip_flange_overlap_mm3'))<=.1:
                errors.append('Disconnected recessed side ring: '+side)
            if connections['hub_paint_overlap_mm3']>.01:
                errors.append('Side ring hub protrudes into wing paint: '+side)
            if connections['flange_solid_count']!=2 or min(connections['bridge_wire_flange_overlap_mm3'])<.01:
                errors.append('Invalid split side flange or detached bridge wire: '+side)
            ends=[]
            for suffix in ('105','218'):
                wire=doc.getObject('VisibleWire'+side+suffix).Shape
                for cap in (f for f in wire.Faces if f.findPlane(1e-6) is not None):
                    overlap=wire.common(Part.makeSphere(3,cap.CenterOfMass)).common(lip).Volume
                    ends.append(overlap)
            connections['lower_wire_end_overlap_mm3']=ends
            if len(ends)!=4 or min(ends)<=.01:errors.append('Detached lower side wire end: '+side)
            side_ring_connections[side]=connections
        shape = Part.read(str(step))
        step_names = re.findall(r"PRODUCT\(\s*'([^']*)'", step.read_text())
        chinese_step_names = [name for name in step_names if re.search(r'[\u4e00-\u9fff]', name)]
        if len(chinese_step_names) != len(visible):
            errors.append('STEP does not preserve every visible Chinese part label')
        compound = Part.makeCompound([obj.Shape for obj in visible])
        solid_count = sum(len(obj.Shape.Solids) for obj in visible)
        if len(shape.Solids) != solid_count or not shape.isValid():
            errors.append('STEP solid count or validity differs')
        relative_volume_error = abs(shape.Volume-compound.Volume)/max(compound.Volume, 1)
        if relative_volume_error > 1e-6:
            errors.append('STEP volume differs from saved visible CAD')
        # Bounds of actual trimmed surfaces, independent of triangulation caches.
        bbox = compound.optimalBoundingBox(False, False)
        step_bbox = shape.optimalBoundingBox(False, False)
        bbox_delta = max(abs(getattr(bbox, k)-getattr(step_bbox, k)) for k in
                         ('XMin', 'XMax', 'YMin', 'YMax', 'ZMin', 'ZMax'))
        if bbox_delta > .01:
            errors.append('STEP bounds differ from saved visible CAD')
        report = {'passed': not errors, 'scope': 'saved static appearance study only',
                  'physical_validation': False, 'errors': errors,
                  'visible_features': len(visible), 'step_solids': len(shape.Solids),
                  'group_count': len(groups), 'non_chinese_labels': non_chinese,
                  'chinese_named_objects': len(doc.Objects)-len(non_chinese),
                  'chinese_step_part_names': len(chinese_step_names),
                  'screen_panel_mm': screen_dims, 'active_area_mm': [200, 150],
                  'woofer_reservation_mm': [88, 40],
                  'woofer_shell_overlap_mm3': reserve_shell_overlap,
                  'restored_reference_modules': restored_modules,
                  'central_support_shafts': support_details,
                  'support_ground_levels_mm': ground_levels,
                  'removed_rear_supports_present': old_supports,
                  'closure_probes_passed': sum(closure_samples), 'closure_probe_count': len(closure_samples),
                  'underbody_loop_connections': loop_connections,
                  'nozzle_loft_surface_count': curved_faces, 'curved_nozzle_petals': len(petals),
                  'non_volumetric_components': non_solid_components,
                  'armour_relief_depths_mm': detail_depths, 'nozzle_hinges': len(hinges),
                  'nozzle_detail_connections':nozzle_detail_connections,
                  'handle_connections':handle_connections,
                  'wing_connections':wing_connections,
                  'roof_connections':roof_connections,
                  'rear_connections':rear_connections,
                  'warning_shell_overlap_mm3':warning_overlap,
                  'shoulder_bolt_plate_overlap_mm3': shoulder_bolt_connections,
                  'hood_mark_crown_gap_mm': hood_mark_gaps,
                  'side_frame_bolt_gap_mm': side_frame_bolt_gaps,
                  'side_frame_bolt_contact_targets': side_frame_bolt_targets,
                  'side_frame_connections': side_frame_connections,
                  'side_spine_perforation_probes_passed': sum(spine_holes),
                  'side_spine_perforation_probe_count': len(spine_holes),
                  'front_cheek_connections': cheek_connections,
                  'control_end_rail_overlap_mm3': control_end_overlaps,
                  'lower_exhaust_petals':len(lower_petals),'lower_exhaust_edge_rails':len(lower_edges),
                  'lower_exhaust_edge_gap_max_mm':max(lower_edge_gaps.values(),default=None),
                  'lower_exhaust_body_overlap_mm3':lower_connections,
                  'side_ring_connections':side_ring_connections,
                  'step_relative_volume_error': relative_volume_error,
                  'step_bbox_max_delta_mm': bbox_delta,
                  'bbox_mm': [bbox.XLength, bbox.YLength, bbox.ZLength],
                  'fcstd_sha256': digest, 'step_sha256': hashlib.sha256(step.read_bytes()).hexdigest()}
        (out/'readback-verification.json').write_text(json.dumps(report, indent=2)+'\n')
        if not errors:
            manifest['bbox_mm'] = report['bbox_mm']
            manifest['bbox_min_mm'] = [bbox.XMin, bbox.YMin, bbox.ZMin]
            manifest['bbox_max_mm'] = [bbox.XMax, bbox.YMax, bbox.ZMax]
            manifest['bounds_basis'] = 'saved FCStd independent readback; optimal trimmed-surface bounds without triangulation'
            (out/'concept-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
        print(json.dumps(report, indent=2))
        if errors:
            raise RuntimeError('Appearance package verification failed')
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    verify(Path(__file__).resolve().parents[1])
