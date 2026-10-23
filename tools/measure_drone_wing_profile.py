"""Project saved wing solids without convex-hull shortcuts across the root.

A 3x triangle raster preserves concave contours. Source frame 30 supplied the
construction outline; the two root-only views are additional manual checks.
"""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_erosion
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project

ADDITIONAL=[(180,'Right',[[280,466],[279,487],[287,512],[304,533],[327,546],
                         [351,552],[377,548],[403,536],[423,515],[435,493]]),
            (60,'Left',[[642,419],[661,451],[661,486],[650,513],[631,533],
                        [605,543],[577,541],[550,526],[527,505],[510,476]])]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def silhouette(shapes,frame,cameras):
    scale=3
    mask=Image.new('1',(940*scale,800*scale))
    draw=ImageDraw.Draw(mask)
    for shape in shapes:
        verts,triangles=shape.tessellate(.08)
        pixels=project(np.array([list(v) for v in verts]),frame,cameras)*scale
        for tri in triangles:draw.polygon([tuple(pixels[i]) for i in tri],fill=1)
    filled=np.asarray(mask)
    boundary=filled&~binary_erosion(filled)
    y,x=np.nonzero(boundary)
    return np.column_stack([x,y])/scale


def outward_intersection(shape,side,y,z):
    section=shape.common(Part.makeLine(App.Vector(-200,y,z),App.Vector(200,y,z)))
    if not section.Vertexes:raise ValueError('Fold sampling line missed the saved surface')
    return max(v.Point.x*side for v in section.Vertexes)


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    parser.add_argument('--output',type=Path,default=folder/'wing-profile-check.json')
    args=parser.parse_args()
    source=folder/'wing-outline-fit.json';fit=json.loads(source.read_text())
    camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    doc=App.openDocument(str(args.model))
    try:
        observations=[]
        for frame,side,px,used in [(30,'Left',fit['source_outline_px'],True),
                                    *[(f,s,p,False) for f,s,p in ADDITIONAL]]:
            shapes=[doc.getObject(prefix+side).Shape for prefix in
                    ('WingEdge','WingPaint','WingFoldFacet','WingInnerPaint')]
            if doc.getObject('WingRaisedFace'+side):shapes.append(doc.getObject('WingRaisedFace'+side).Shape)
            boundary=silhouette(shapes,frame,cameras)
            distances,idx=cKDTree(boundary).query(px)
            observations.append({'source_frame':frame,'side':side,'used_for_construction':used,
                'reference_px':px,'saved_nearest_px':boundary[idx].tolist(),'distance_px':distances.tolist(),
                'distance_rms_px':float(np.sqrt(np.mean(distances**2))),'max_distance_px':float(max(distances))})
        joints={}
        for sign,side in [(-1,'Left'),(1,'Right')]:
            blade=doc.getObject('WingEdge'+side).Shape
            paint=doc.getObject('WingPaint'+side).Shape
            fold=doc.getObject('WingFoldFacet'+side).Shape
            raised=doc.getObject('WingRaisedFace'+side)
            # The v21 baseline fused this layer into WingEdge.
            raised=raised.Shape if raised else blade
            z=248.67*1.01-8.8
            high=outward_intersection(paint,sign,(142.5-2)*1.12+33,z)
            low=outward_intersection(fold,sign,(142.5+2)*1.12+33,z)
            joints[side]={'paint_raised_overlap_mm3':paint.common(raised).Volume,
                'raised_blade_gap_mm':raised.distToShape(blade)[0],
                'fold_blade_overlap_mm3':fold.common(blade).Volume,
                'inner_blade_gap_mm':doc.getObject('WingInnerPaint'+side).Shape.distToShape(blade)[0],
                'mark_paint_gap_mm':doc.getObject('WingHubMark'+side).Shape.distToShape(paint)[0],
                'fold_sample_z_mm':z,'high_sample_y_mm':(142.5-2)*1.12+33,
                'low_sample_y_mm':(142.5+2)*1.12+33,'outward_high_x_mm':high,
                'outward_low_x_mm':low,'surface_step_mm':high-low}
        result={'fcstd_sha256':digest(args.model),'source_fit_sha256':digest(source),
            'camera_config_sha256':digest(camera),'measurement_script_sha256':digest(Path(__file__)),
            'source_video_sha256':cameras['reference_video_sha256'],'raster_scale':3,
            'observations':observations,'saved_joints':joints,
            'limitations':['manual reference edges; source frame 30 also supplied construction points',
                'projects edge, raised face, paint, fold and inner skin; excludes rear rib, hub and markings',
                'additional views inspect only ten visible colored root points each',
                'three-times triangle raster approximates projected union; about one-third pixel sampling',
                'fold depth is an appearance assumption, not measured from the original 3D model',
                'no full-wing independent multi-view acceptance or physical qualification']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'views':[{k:o[k] for k in ('source_frame','distance_rms_px','max_distance_px')}
                         for o in observations],'saved_joints':joints},indent=2))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
