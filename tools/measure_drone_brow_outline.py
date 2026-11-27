"""Fit source brow arcs, then inspect the saved front face in the fixed camera.

Front depth stays fixed to the existing side-view placement: a single frontal
image cannot independently recover depth and width. Other views must cross-check.
"""
import hashlib
import json
from pathlib import Path

import FreeCAD as App
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree

from measure_drone_landmarks import project


OUTER = [[188,321],[194,296],[209,278],[233,267],[265,264],[470,264],
         [704,264],[730,272],[751,291],[766,317],[762,363],[758,406],[193,406]]
INNER = [[212,402],[211,353],[212,320],[217,305],[228,294],[248,287],
         [470,285],[705,287],[730,301],[743,321],[742,360],[738,404]]


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'cad/drone-concept/comparison'
    camera_path = folder/'camera-fit.json'
    camera = json.loads(camera_path.read_text())['parameters']
    model = root/'cad/drone-concept/vintrox-drone-concept.FCStd'
    video = root/'references/alexander-shevchuk-drone/video-cam.mp4'

    def points(parameters, inside=False):
        width,top,radius,border,bottom = parameters
        if inside:
            width -= 2*border; top -= border; radius -= border
        half = width/2
        xz = [(x,top) for x in np.linspace(-half+radius,half-radius,320)]
        for side in (-1,1):
            xz.extend((side*half,z) for z in np.linspace(bottom,top-radius,160))
            xz.extend((side*(half-radius+radius*np.cos(t)),top-radius+radius*np.sin(t))
                      for t in np.linspace(0,np.pi/2,160))
        return np.array([project([x,-46+87.2-.4*z,z-11],9,camera) for x,z in xz])

    def residual(parameters):
        values = []
        for observations,inside in ((OUTER,False),(INNER,True)):
            values.extend(cKDTree(points(parameters,inside)).query(observations)[0])
        width,_,_,_,bottom = parameters
        for side,pixel in ((-1,[193,406]),(1,[758,406])):
            values.extend(project([side*width/2,-46+87.2-.4*bottom,bottom-11],9,camera)-pixel)
        return values

    fit = least_squares(residual,[243,263,24,10,200],
                        bounds=([230,255,15,5,185],[260,270,34,15,210]),
                        diff_step=1e-4,xtol=1e-8,ftol=1e-8,max_nfev=200)
    doc = App.openDocument(str(model))
    try:
        obj = doc.getObject('ProjectingBrow')
        normal = App.Vector(0,1,.4); normal.normalize()
        planes = [f for f in obj.Shape.Faces if f.findPlane(1e-6) is not None
                  and abs(f.normalAt(0,0).dot(normal)) > .9999]
        station = lambda f:f.CenterOfMass.y+.4*f.CenterOfMass.z
        front = min(station(f) for f in planes)
        faces = [f for f in planes if abs(station(f)-front) < 1e-4]
        projected = np.array([project(list(v),9,camera) for face in faces
                              for edge in face.Edges for v in edge.discretize(Number=160)])
        observations = OUTER+INNER
        distance,index = cKDTree(projected).query(observations)
        result = {'fcstd_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
                  'camera_fit_sha256':hashlib.sha256(camera_path.read_bytes()).hexdigest(),
                  'source_video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
                  'measurement_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  'source_frame':270,'outer_source_px':OUTER,'inner_source_px':INNER,
                  'fit_parameter_names':['local_width_mm','local_top_z_mm','corner_radius_mm',
                                         'border_mm','local_bottom_z_mm'],
                  'source_fit_parameters':fit.x.tolist(),'fixed_local_front_y_mm':-46,
                  'source_fit_residual_rms_px':float(np.sqrt(np.mean(np.array(residual(fit.x))**2))),
                  'saved_front_plane_y_plus_point4_z':front,'saved_front_face_count':len(faces),
                  'saved_front_boundary_px':projected[index].tolist(),'distance_px':distance.tolist(),
                  'saved_boundary_distance_rms_px':float(np.sqrt(np.mean(distance**2))),
                  'saved_boundary_max_distance_px':float(max(distance)),
                  'limitations':['manual source edge positions','single-view fit with fixed front depth',
                                 'front planar face boundary excludes the small rounded edge roll',
                                 'other components and the full silhouette are not certified']}
        (folder/'brow-outline-check.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({k:result[k] for k in ('source_fit_parameters','source_fit_residual_rms_px',
                                               'saved_boundary_distance_rms_px','saved_boundary_max_distance_px')}))
    finally:
        App.closeDocument(doc.Name)


if __name__ == '__main__':
    main()
