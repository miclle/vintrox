"""Read the saved swept cable centerline and both terminal connections."""
import argparse,hashlib,json
from pathlib import Path
import FreeCAD as App
import Part
import numpy as np
from scipy.spatial import cKDTree
from fit_drone_lower_pod_outline import project


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'cad/drone-concept/comparison'
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,default=root/'cad/drone-concept/vintrox-drone-concept.FCStd')
    p.add_argument('--output',type=Path,default=folder/'side-cable-check.json');args=p.parse_args()
    fit_path=folder/'side-cable-fit.json';fit=json.loads(fit_path.read_text());camera=folder/'cameras.json';cameras=json.loads(camera.read_text())
    doc=App.openDocument(str(args.model))
    try:
        shape=doc.getObject('SideCableLeft').Shape
        faces=[f for f in shape.Faces if f.Surface.isUPeriodic()]
        if not faces:raise ValueError('Expected periodic cable sweep faces')
        path=[];radii=[];area=sum(f.Area for f in faces)
        for face in faces:
            u0,u1,v0,v1=face.ParameterRange
            for v in np.linspace(v0,v1,max(24,int(2600*face.Area/area))):
                section=np.array([list(face.valueAt(float(u),float(v))) for u in np.linspace(u0,u1,32,endpoint=False)])
                # NURBS parameters are not uniform angles. Fit each actual
                # section circle rather than using the arithmetic mean.
                mean=section.mean(axis=0)
                _,_,basis=np.linalg.svd(section-mean,full_matrices=False)
                xy=(section-mean)@basis[:2].T
                fit_circle=np.linalg.lstsq(np.c_[2*xy,np.ones(len(xy))],np.sum(xy**2,axis=1),rcond=None)[0]
                center=mean+fit_circle[:2]@basis[:2]
                path.append(center);radii.extend(np.linalg.norm(section-center,axis=1))
        bop_errors=[]
        try:shape.check(True)
        except ValueError as error:bop_errors.append(str(error))
        path=np.array(path);groups={}
        for key,source in fit['groups'].items():
            observations=[];dd=[]
            for o in source['observations']:
                pp=project(path,o['source_frame'],cameras);dist,ii=cKDTree(pp).query(o['reference_px']);dd.extend(dist)
                observations.append({'source_frame':o['source_frame'],'reference_px':o['reference_px'],
                                     'saved_nearest_px':pp[ii].tolist(),'distance_px':dist.tolist()})
            groups[key]={'observations':observations,'distance_rms_px':float(np.sqrt(np.mean(np.array(dd)**2))),'max_distance_px':float(max(dd))}
        caps=[f for f in shape.Faces if type(f.Surface).__name__=='Plane'];contacts=[]
        for terminal,boot_name,mount_name in zip(fit['inferred_terminal_centers_mm'],
                ('UtilityCableBootLeft','SideCableTopBootLeft'),('UtilityLinerLeft','SideStatusPlateLeft')):
            cap=min(caps,key=lambda f:(f.CenterOfMass-App.Vector(*terminal)).Length)
            boot=doc.getObject(boot_name);mount=doc.getObject(mount_name)
            contacts.append({'boot':boot_name,'mount':mount_name,'saved_cap_center_mm':list(cap.CenterOfMass),
                'terminal_error_mm':(cap.CenterOfMass-App.Vector(*terminal)).Length,
                'cable_mount_gap_mm':shape.distToShape(mount.Shape)[0],
                'boot_valid':bool(boot and boot.Shape.isValid()),
                'boot_solids':len(boot.Shape.Solids) if boot else 0,
                'cable_boot_overlap_mm3':shape.common(Part.makeSphere(3,cap.CenterOfMass)).common(boot.Shape).Volume if boot else 0,
                'boot_mount_overlap_mm3':boot.Shape.common(mount.Shape).Volume if boot else 0})
        result={'fcstd_sha256':digest(args.model),'source_fit_sha256':digest(fit_path),
                'camera_config_sha256':digest(camera),'source_video_sha256':fit['source_video_sha256'],
                'measurement_script_sha256':digest(Path(__file__)),'groups':groups,
                'valid':shape.isValid(),'solids':len(shape.Solids),'cap_count':len(caps),
                'bop_check_passed':not bop_errors,'bop_errors':bop_errors,'swept_face_count':len(faces),
                'sampled_section_radius_range_mm':[float(min(radii)),float(max(radii))],
                'centerline_method':'least-squares circle on 32 samples of each saved periodic surface section',
                'saved_centerline_mm':path.tolist(),'centerline_order':'per saved face; not a single ordered polyline','contacts':contacts,
                'limitations':fit['limitations']+['whole saved sweep includes inferred hidden terminal leads',
                    'contacts verify appearance geometry only, not strain relief or electrical performance']}
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ['valid','solids','cap_count','sampled_section_radius_range_mm','contacts']},indent=2))
        print(json.dumps({k:{v:g[v] for v in ['distance_rms_px','max_distance_px']} for k,g in groups.items()}))
    finally:App.closeDocument(doc.Name)


if __name__=='__main__':main()
