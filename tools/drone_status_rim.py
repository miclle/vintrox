"""Inset side-shell bevel fitted at frame 180, checked in the full fixed orbit.
Depth and mirrored geometry are appearance assumptions. The opening flares
outward to preserve oblique sightlines to the unchanged controls.
"""
import FreeCAD as App
import Part
import numpy as np

REFERENCE_EDGE=[[529,524],[543,512],[556,499],[563,487],[563,420]]
CAMERAS={'views': [{'name': 'video-06', 'source_frame': 180, 'time_seconds': 6, 'eye_mm': [1100.478706826763, 481.9590609254328, 317.0386845391606], 'target_mm': [0.501566808748322, 140.6149973153713, 170.38720767320478], 'ortho_scale_mm': 412.280701754386, 'projection': 'PERSP', 'lens_mm': 87.56332021440045, 'sensor_width_mm': 36}]}

def restore_status_rim(shape, side, full):
    inner_x=100.5;flare=3.8
    cameras=CAMERAS
    eye=np.array(next(p for p in cameras['views'] if p['source_frame']==180)['eye_mm'])
    pose=next(p for p in cameras['views'] if p['source_frame']==180)
    forward=np.array(pose['target_mm'])-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    focal=pose['lens_mm']/pose['sensor_width_mm']*940
    scale=(108-eye[0])/(116.76-eye[0])
    full=full.copy()
    full.scale(scale)
    full.translate(App.Vector(side*(108-scale*116.76),eye[1]*(1-scale),eye[2]*(1-scale)))
    local=Part.makeBox(106-inner_x,42,63,App.Vector((inner_x if side>0 else -106),193,127))
    patch=full.common(local)
    profiles=[]
    for x,extra in [(inner_x-.05,0),(104.6103319,flare),(106,flare+1.5)]:
        edge=[]
        for px,py in REFERENCE_EDGE:
            ray=forward+(px-470)/focal*right+(400-py)/focal*up
            q=eye+ray*((x-eye[0])/ray[0]);edge.append((q[1]+extra,q[2]))
        # Extend beyond the patch: pre-existing shell, not this cutter, closes
        # the socket end of the opening. The lower diagonal follows the trace.
        outline=[(185,115),(edge[0][0]-10,115),*edge,(edge[-1][0],195),(185,195)]
        vertices=[App.Vector(side*x,y,z) for y,z in outline]
        profiles.append(Part.Wire(Part.makePolygon(vertices+[vertices[0]]).Edges))
    opening=Part.makeLoft(profiles,True,True)
    result=shape.fuse(patch.cut(opening).removeSplitter()).removeSplitter()
    result.check(True)
    if not result.isValid() or not result.isClosed() or len(result.Solids)!=len(shape.Solids):
        raise ValueError("Invalid restored status rim")
    return result
