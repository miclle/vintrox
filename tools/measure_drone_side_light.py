"""Read saved side-frame joints and compare four visible light-band widths.

Brightness widths are a local display-space diagnostic, not the silhouette score.
The fixed sample rows avoid wires crossing the source light; lighting still matters.
"""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bright_runs(path):
    pixels=np.asarray(Image.open(path).convert('RGB'))
    records=[]
    for y in (430,450,470,490):
        strip=pixels[y,250:280]
        on=(strip[:,1]>160)&(strip[:,2]>160)
        starts=np.flatnonzero(np.diff(np.r_[False,on,False].astype(int))==1)
        ends=np.flatnonzero(np.diff(np.r_[False,on,False].astype(int))==-1)
        if len(starts)==0:
            records.append({'row_px':y,'span_px':None,'width_px':0})
        else:
            i=int(np.argmax(ends-starts))
            records.append({'row_px':y,'span_px':[int(starts[i]+250),int(ends[i]+249)],
                            'width_px':int(ends[i]-starts[i])})
    return records


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    parser=argparse.ArgumentParser()
    parser.add_argument('--renders',type=Path,required=True)
    parser.add_argument('--comparison',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=folder/'side-light-check.json')
    args=parser.parse_args()
    paths={'reference':args.comparison/'reference-frames/frame-07.png',
           'previous_cad':folder/'iteration-43-renders/video-06.png',
           'current_cad':args.renders/'video-06.png'}
    model=root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    doc=App.openDocument(str(model))
    try:
        joints={}
        for side in ('Left','Right'):
            light=doc.getObject('CyanSideTube'+side).Shape
            guard=doc.getObject('SideGuard'+side).Shape
            shoe=doc.getObject('SideFrameShoe'+side).Shape
            radii=sorted({round(f.Surface.Radius,6) for f in light.Faces
                          if isinstance(f.Surface,Part.Cylinder)})
            bends=sorted({round(f.Surface.MajorRadius,6) for f in light.Faces
                          if isinstance(f.Surface,Part.Toroid)})
            joints[side]={'light_solids':len(light.Solids),'straight_tube_radii_mm':radii,
                'bend_centerline_radii_mm':bends,'light_guard_overlap_mm3':light.common(guard).Volume,
                'shoe_guard_overlap_mm3':shoe.common(guard).Volume,
                'screw_shoe_gap_mm':[doc.getObject(f'SideFrameBolt{side}{i}').Shape.distToShape(shoe)[0] for i in range(2)]}
        result={'fcstd_sha256':digest(model),'camera_config_sha256':digest(folder/'cameras.json'),
            'measurement_script_sha256':digest(Path(__file__)),
            'render_manifest_sha256':digest(args.renders/'render-manifest.json'),
            'source_video_sha256':digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'source_frame':180,'threshold':{'green_gt':160,'blue_gt':160,'x_range_half_open':[250,280]},
            'images':{k:{'path':str(p),'sha256':digest(p),'samples':bright_runs(p)} for k,p in paths.items()},
            'saved_joints':joints,
            'limitations':['four fixed rows on one visible straight section; not a full light contour check',
                'brightness widths depend on source/render lighting and the stated threshold',
                'corner radii inferred from appearance, not measured manufacturing dimensions',
                'local diagnostic does not change the primary foreground masks or IoU score']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result,indent=2))
    finally:App.closeDocument(doc.Name)

if __name__=='__main__':main()
