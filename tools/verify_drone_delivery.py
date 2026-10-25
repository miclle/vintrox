"""Audit the current Drone model, previews, comparisons and reference bindings.

This checks saved artifacts, not physical suitability or artistic equivalence.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    root = Path(__file__).resolve().parents[1]
    cad = root/'cad/drone-concept'
    comparison = cad/'comparison'
    model_hash = digest(cad/'vintrox-drone-concept.FCStd')
    errors = []
    images = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    with ZipFile(cad/'vintrox-drone-concept.FCStd') as archive:
        gui_files = list(dict.fromkeys(n.get('file') for n in
            ET.fromstring(archive.read('GuiDocument.xml')).iter() if n.get('file')))
        require(len(gui_files)==2094 and
                [n for n in archive.namelist() if n in set(gui_files)]==gui_files,
                'GUI resource order differs from XML registration order')

    def check_render_identity(manifest):
        require(manifest.get('rendered_fcstd_sha256',model_hash)==model_hash,
                'Expected renders made directly from the current saved model')

    geometry = read(cad/'concept-manifest.json')
    saved = read(cad/'readback-verification.json')
    require(saved['passed'], 'Saved geometry verification failed')
    require(saved['fcstd_sha256'] == geometry['fcstd_sha256'] == model_hash, 'Stale geometry reports')
    require(saved['step_sha256'] == digest(cad/'vintrox-drone-concept.step'), 'Stale STEP')
    index = read(comparison/'review-index.json')
    require(index['fcstd_sha256'] == model_hash, 'Stale reference review index')
    require(len(index['inputs']) == 9, 'Expected eight images and one video')
    side = read(comparison/index['side_frame'])
    require(side['fcstd_sha256'] == model_hash, 'Stale saved side frame check')
    require(side['measurement_script_sha256']==digest(root/'tools/measure_drone_side_frame.py'),
            'Changed side frame measurement script')
    require(side['source_fit_sha256'] == digest(comparison/'side-frame-fit.json'),
            'Changed side frame source fit')
    side_source = read(comparison/'side-frame-fit.json')
    require(side_source['camera_config_sha256'] == digest(comparison/'cameras.json'),
            'Changed side frame source cameras')
    require(side_source['source_video_sha256'] == digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed side frame source video')
    require(side['camera_fit_sha256'] == digest(comparison/'camera-fit.json'),
            'Changed side frame camera fit')
    require(set(side['profiles']) == {'outer','spine','light'}, 'Missing side profile checks')
    light=read(comparison/index['side_light'])
    require(light['fcstd_sha256']==model_hash, 'Stale side light readback')
    require(light['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed side light cameras')
    require(light['measurement_script_sha256']==digest(root/'tools/measure_drone_side_light.py'),
            'Changed side light measurement script')
    video_folder=(comparison/index['video_comparison']).parent
    require(light['render_manifest_sha256']==digest(video_folder.with_name(video_folder.name+'-renders')/'render-manifest.json'),
            'Changed side light rendered input')
    require(light['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed side light source video')
    for item in light['images'].values():
        require(digest(root/item['path'])==item['sha256'], 'Changed side light image')
        require([s['row_px'] for s in item['samples']]==[430,450,470,490], 'Missing side light samples')
    reprojection=geometry['side_profile_reprojection']
    eye=next(v['eye_mm'] for v in read(comparison/'cameras.json')['views'] if v['source_frame']==180)
    expected_scale=(108.0-eye[0])/(116.76-eye[0])
    require(reprojection['outer_x_mm']==108.0 and reprojection['eye_mm']==eye and
            abs(reprojection['scale']-expected_scale)<1e-12, 'Changed reviewed side-profile transform')
    for joint in light['saved_joints'].values():
        require(joint['light_solids']==1 and joint['straight_tube_radii_mm']==[round(1.8*expected_scale,6)] and
                joint['bend_centerline_radii_mm']==[round(4.0*expected_scale,6)], 'Invalid rounded side light')
        require(joint['shoe_guard_overlap_mm3']>.01 and joint['light_guard_overlap_mm3']>.01 and
                max(joint['screw_shoe_gap_mm'])<.01, 'Detached side detail')
    rounding=read(comparison/index['side_rounding_detail'])
    require(rounding['fcstd_sha256']==model_hash and
            rounding['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale side rounding detail')
    require(digest(root/rounding['image_path'])==rounding['image_sha256'], 'Changed side rounding image')
    for item in rounding['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed side rounding source')
    detail = read(comparison/index['side_frame_detail'])
    require(detail['fcstd_sha256'] == model_hash, 'Stale side detail board')
    require(detail['camera_config_sha256'] == digest(comparison/'cameras.json'),
            'Changed side detail cameras')
    require(digest(root/detail['image_path']) == detail['image_sha256'], 'Changed side detail board')
    for item in detail['source_files']:
        require(digest(root/item['path']) == item['sha256'], 'Changed side detail input')
    for source in index['inputs']:
        require(digest(root/source['source']) == source['sha256'], 'Changed reference: '+source['source'])

    def check_renders(folder):
        manifest = read(folder/'render-manifest.json')
        require(manifest['fcstd_sha256'] == model_hash, 'Stale renders: '+str(folder))
        check_render_identity(manifest)
        for item in manifest['images']:
            path = folder/item['path']
            require(digest(path) == item['sha256'], 'Changed render: '+str(path))
            images.append(str(path.relative_to(root)))
        return manifest

    display = check_renders(cad/'renders')
    expected = {'closeup','hero','rear','front','right','armour-detail','nozzle-detail','top','underside'}
    require({i['view'] for i in display['images']} == expected, 'Missing display view')
    require(display['cad_geometry_features'] == saved['visible_features'], 'Render feature count differs')
    for key in ('turntable', 'review_board'):
        item = display[key]
        require(digest(cad/'renders'/item['path']) == item['sha256'], 'Changed '+key)
    video = cad/'renders'/display['turntable']['path']
    probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
        'format=duration:stream=width,height,nb_frames','-of','json',str(video)],text=True))
    require(abs(float(probe['format']['duration'])-12) < .1, 'Turntable duration differs')
    require(display['turntable']['unique_angles'] == 96, 'Expected 96 rendered angles')

    for key in ('video_comparison', 'still_comparison'):
        path = comparison/index[key]
        report = read(path)
        folder = comparison/(path.parent.name+'-renders')
        render = check_renders(folder)
        require(report['fcstd_sha256'] == model_hash, 'Stale comparison: '+key)
        require(report['render_manifest_sha256'] == digest(folder/'render-manifest.json'), 'Comparison/render mismatch: '+key)
        require(report['camera_config_sha256'] == render['camera_config_sha256'] == digest(path.parent/'cameras.json'),
                'Comparison/camera mismatch: '+key)
        require(len(report['views']) == (10 if key == 'video_comparison' else 7), 'Missing comparison views')
    points = read(comparison/index['landmarks'])
    require(points['fcstd_sha256'] == model_hash, 'Stale landmark check')
    nozzle = read(comparison/index['nozzle_outline'])
    source_fit = comparison/'nozzle-mouth-fit.json'
    require(nozzle['fcstd_sha256'] == model_hash, 'Stale saved nozzle outline')
    require(nozzle['source_fit_sha256'] == digest(source_fit), 'Changed nozzle source fit')
    require(nozzle['camera_fit_sha256'] == digest(comparison/'camera-fit.json'), 'Changed nozzle camera fit')
    require(read(source_fit)['camera_config_sha256'] == digest(comparison/'cameras.json'), 'Changed nozzle cameras')
    require(nozzle['terminal_arc_count'] == geometry['nozzle_petals'], 'Nozzle terminal arc count differs')
    require(nozzle['measurement_script_sha256']==digest(root/'tools/measure_drone_nozzle_outline.py') and
            nozzle['center_spread_mm']<.001 and nozzle['max_distance_px']<22.75,
            'Nozzle shared terminal circle is stale or exceeds the local contour target')
    fins = read(comparison/index['cooling_fins'])
    require(fins['fcstd_sha256'] == model_hash, 'Stale saved cooling fins')
    require(fins['camera_fit_sha256'] == digest(comparison/'camera-fit.json'), 'Changed fin camera fit')
    require(fins['source_video_sha256'] == digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed fin reference video')
    require(fins['saved_fin_count'] == 15 and fins['grip_wrap_parts'] == fins['grip_wrap_solids'] == 10,
            'Missing fin or grip parts')
    brow = read(comparison/index['brow_outline'])
    require(brow['fcstd_sha256'] == model_hash, 'Stale saved brow outline')
    require(brow['camera_fit_sha256'] == digest(comparison/'camera-fit.json'), 'Changed brow camera fit')
    require(brow['source_video_sha256'] == digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed brow reference video')
    require(brow['saved_front_face_count'] >= 1 and len(brow['distance_px']) == 25, 'Missing brow observations')
    cheek=read(comparison/index['cheek_position'])
    require(cheek['fcstd_sha256']==model_hash, 'Stale cheek position check')
    require(cheek['camera_fit_sha256']==digest(comparison/'camera-fit.json'), 'Changed cheek camera fit')
    require(cheek['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed cheek reference video')
    require(len(cheek['observations'])==2, 'Missing cheek placement observations')
    require(len(cheek['end_mount_observations'])==2, 'Missing lower mount observations')
    loop=read(comparison/index['loop_profile'])
    require(loop['fcstd_sha256']==model_hash, 'Stale saved underbody arc check')
    require(loop['camera_fit_sha256']==digest(comparison/'camera-fit.json'), 'Changed underbody arc camera fit')
    require(loop['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed underbody arc cameras')
    require(loop['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed underbody arc reference')
    require(len(loop['source_centerline_px'])==9 and len(loop['saved_centerlines_mm'])==2,
            'Missing underbody arc observations or saved paths')
    loop_detail=read(comparison/index['loop_detail'])
    require(loop_detail['fcstd_sha256']==model_hash, 'Stale underbody arc detail')
    require(loop_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed underbody detail cameras')
    require(digest(root/loop_detail['image_path'])==loop_detail['image_sha256'], 'Changed underbody detail image')
    for item in loop_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed underbody detail source')
    lower=read(comparison/index['lower_pod_outline'])
    lower_fit=read(comparison/'lower-pod-outline-fit.json')
    require(lower['fcstd_sha256']==model_hash, 'Stale small exhaust outline')
    require(lower['source_fit_sha256']==digest(comparison/'lower-pod-outline-fit.json'),
            'Changed small exhaust source fit')
    require(lower['camera_config_sha256']==lower_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed small exhaust cameras')
    require(lower['source_video_sha256']==lower_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed small exhaust source video')
    require(lower_fit['fit_script_sha256']==digest(root/'tools/fit_drone_lower_pod_outline.py'),
            'Changed small exhaust source fitting script')
    require(len(lower['observations'])==4 and sum(len(o['reference_px']) for o in lower['observations'])==37,
            'Missing small exhaust source observations')
    require(len(lower['additional_view_checks'])==2 and
            sum(len(o['reference_px']) for o in lower['additional_view_checks'])==20,
            'Missing small exhaust additional view checks')
    require(set(lower['saved_terminal_geometry'])=={'-1','1'} and
            all(g['petal_count']==18 for g in lower['saved_terminal_geometry'].values()),
            'Missing saved small exhaust terminal edges')
    lower_detail=read(comparison/index['lower_pod_detail'])
    require(lower_detail['fcstd_sha256']==model_hash, 'Stale small exhaust detail')
    require(lower_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed small exhaust detail cameras')
    require(digest(root/lower_detail['image_path'])==lower_detail['image_sha256'], 'Changed small exhaust detail image')
    for item in lower_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed small exhaust detail source')
    ring=read(comparison/index['side_ring'])
    ring_fit=read(comparison/'side-ring-fit.json')
    require(ring['fcstd_sha256']==model_hash, 'Stale saved side ring surface check')
    require(ring['source_fit_sha256']==digest(comparison/'side-ring-fit.json'), 'Changed side ring source fit')
    require(ring['camera_config_sha256']==ring_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed side ring cameras')
    require(ring['source_video_sha256']==ring_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed side ring source video')
    require(ring_fit['fit_script_sha256']==digest(root/'tools/fit_drone_side_ring.py'), 'Changed side ring fitting script')
    require(set(ring['saved_lip_geometry'])=={'-1','1'} and len(ring['observations'])==4 and
            sum(len(o['reference_px']) for o in ring['observations'])==56, 'Missing side ring geometry or observations')
    ring_detail=read(comparison/index['side_ring_detail'])
    require(ring_detail['fcstd_sha256']==model_hash, 'Stale side ring detail')
    require(ring_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed side ring detail cameras')
    require(digest(root/ring_detail['image_path'])==ring_detail['image_sha256'], 'Changed side ring detail image')
    for item in ring_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed side ring detail source')
    nozzle_root=read(comparison/index['nozzle_root'])
    root_fit=read(comparison/'nozzle-root-fit.json')
    require(nozzle_root['fcstd_sha256']==model_hash, 'Stale nozzle root check')
    require(nozzle_root['source_fit_sha256']==digest(comparison/'nozzle-root-fit.json'),
            'Changed nozzle root source fit')
    require(nozzle_root['camera_config_sha256']==root_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed nozzle root cameras')
    require(nozzle_root['source_video_sha256']==root_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed nozzle root source video')
    require(root_fit['fit_script_sha256']==digest(root/'tools/fit_drone_nozzle_root.py'),
            'Changed nozzle root fitting script')
    require(len(nozzle_root['observations'])==3 and
            sum(len(o['reference_px']) for o in nozzle_root['observations'])==23,
            'Missing nozzle root observations')
    require(nozzle_root['measurement_script_sha256']==digest(root/'tools/measure_drone_nozzle_root.py') and
            nozzle_root['five_view_source_sha256']==digest(comparison/'source-registration-study/five-video-root-fit.json') and
            len(nozzle_root['five_view_observations'])==5 and
            sum(len(r['reference_px']) for r in nozzle_root['five_view_observations'])==45 and
            nozzle_root['five_view_rms_px']<3.7, 'Expanded saved root reconstruction check failed')
    root_detail=read(comparison/index['nozzle_root_detail'])
    require(root_detail['fcstd_sha256']==model_hash, 'Stale nozzle root detail')
    require(root_detail['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed nozzle root detail cameras')
    require(digest(root/root_detail['image_path'])==root_detail['image_sha256'],
            'Changed nozzle root detail image')
    for item in root_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed nozzle root detail source')
    handle=read(comparison/index['handle_profile'])
    handle_fit=read(comparison/'handle-profile-fit.json')
    require(handle['fcstd_sha256']==model_hash, 'Stale handle profile check')
    require(handle['source_fit_sha256']==digest(comparison/'handle-profile-fit.json'),
            'Changed handle source fit')
    require(handle['camera_config_sha256']==handle_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed handle cameras')
    require(handle['source_video_sha256']==handle_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed handle source video')
    require(handle_fit['fit_script_sha256']==digest(root/'tools/fit_drone_handle_profile.py'),
            'Changed handle fitting script')
    require(len(handle['observations'])==2 and
            [len(o['reference_px']) for o in handle['observations']]==[21,12] and
            [o['used_for_construction'] for o in handle['observations']]==[True,False],
            'Missing handle construction or additional view checks')
    handle_detail=read(comparison/index['handle_detail'])
    require(handle_detail['fcstd_sha256']==model_hash, 'Stale handle detail')
    require(handle_detail['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed handle detail cameras')
    require(digest(root/handle_detail['image_path'])==handle_detail['image_sha256'],
            'Changed handle detail image')
    for item in handle_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed handle detail source')
    roof=read(comparison/index['roof_instrument'])
    require(roof['fcstd_sha256']==model_hash, 'Stale roof/instrument readback')
    require(roof['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed roof cameras')
    require(roof['measurement_script_sha256']==digest(root/'tools/measure_drone_roof_instrument.py'),
            'Changed roof measurement script')
    for file,key,script in [('roof-instrument-fit.json','source_fit_sha256','fit_drone_roof_instrument.py'),
                            ('roof-crown-fit.json','roof_fit_sha256','fit_drone_roof_crown.py')]:
        source=read(comparison/file)
        require(roof[key]==digest(comparison/file), 'Changed roof source fit: '+file)
        require(source['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed roof fit cameras')
        require(source['source_video_sha256']==roof['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
                'Changed roof source video')
        require(source['fit_script_sha256']==digest(root/'tools'/script), 'Changed roof fit script: '+script)
    require(len(roof['observations'])==3 and sum(len(o['reference_px']) for o in roof['observations'])==10,
            'Missing instrument corner observations')
    require(len(roof['roof_observations'])==2 and sum(len(o['reference_px']) for o in roof['roof_observations'])==14,
            'Missing visible roof boundary observations')
    roof_detail=read(comparison/index['roof_detail'])
    require(roof_detail['fcstd_sha256']==model_hash, 'Stale roof detail')
    require(roof_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed roof detail cameras')
    require(digest(root/roof_detail['image_path'])==roof_detail['image_sha256'], 'Changed roof detail image')
    for item in roof_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed roof detail source')
    wing=read(comparison/index['wing_profile'])
    wing_fit=read(comparison/'wing-outline-fit.json')
    require(wing['fcstd_sha256']==model_hash, 'Stale curved wing readback')
    require(wing['source_fit_sha256']==digest(comparison/'wing-outline-fit.json'), 'Changed wing source fit')
    require(wing['camera_config_sha256']==wing_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed wing cameras')
    require(wing['source_video_sha256']==wing_fit['reference_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed wing source video')
    require(wing['measurement_script_sha256']==digest(root/'tools/measure_drone_wing_profile.py'),
            'Changed wing measurement script')
    require([len(o['reference_px']) for o in wing['observations']]==[24,10,10] and wing['raster_scale']==3,
            'Missing wing observations or raster resolution')
    for joint in wing['saved_joints'].values():
        require(joint['paint_raised_overlap_mm3']>.01 and joint['fold_blade_overlap_mm3']>.01 and
                max(joint[k] for k in ('raised_blade_gap_mm','inner_blade_gap_mm','mark_paint_gap_mm'))<.01,
                'Detached wing layers')
    wing_detail=read(comparison/index['wing_detail'])
    require(wing_detail['fcstd_sha256']==model_hash and
            wing_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale wing detail')
    require(digest(root/wing_detail['image_path'])==wing_detail['image_sha256'], 'Changed wing detail image')
    for item in wing_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed wing detail source')
    crease=read(comparison/'wing-crease-check.json')
    require(crease['fcstd_sha256']==model_hash and
            crease['measurement_script_sha256']==digest(root/'tools/measure_drone_wing_crease.py') and
            crease['source_fit_sha256']==digest(comparison/'wing-crease-study/crease-joint-fit.json') and
            crease['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale gold wing crease check')
    require([r['source_frame'] for r in crease['observations']]==[30,210,180] and
            all(r['current']['rms_px']<r['baseline']['rms_px'] for r in crease['observations'] if r['side']==1),
            'Gold wing crease observations missing or regressed')
    require(len(crease['preserved_edges'])==2 and
            all(r['bidirectional_sample_distance_max_mm']<1e-6 for r in crease['preserved_edges']) and
            len(crease['crease_endpoint_distance_mm'])==2 and
            max(crease['crease_endpoint_distance_mm'])<1e-6, 'Gold wing fixed edges or endpoints changed')
    for key,stem in [('knob_outline','knob-outline'),('side_status','side-status'),('side_socket','side-socket'),('side_cable','side-cable')]:
        check=read(comparison/index[key]);fit=read(comparison/(stem+'-fit.json'))
        require(check['fcstd_sha256']==model_hash, 'Stale '+stem+' readback')
        require(check['source_fit_sha256']==digest(comparison/(stem+'-fit.json')), 'Changed '+stem+' fit')
        require(check['camera_config_sha256']==fit['camera_config_sha256']==digest(comparison/'cameras.json'),
                'Changed '+stem+' cameras')
        require(check['source_video_sha256']==fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
                'Changed '+stem+' reference video')
        require(fit['fit_script_sha256']==digest(root/('tools/fit_drone_'+stem.replace('-','_')+'.py')) and
                check['measurement_script_sha256']==digest(root/('tools/measure_drone_'+stem.replace('-','_')+'.py')),
                'Changed '+stem+' measurement scripts')
    knob=read(comparison/index['knob_outline'])
    require([len(o['reference_px']) for o in knob['observations']]==[10,8,9], 'Missing knob outline observations')
    knob_detail=read(comparison/index['knob_detail'])
    require(knob_detail['fcstd_sha256']==model_hash and
            knob_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale knob detail')
    require(digest(root/knob_detail['image_path'])==knob_detail['image_sha256'], 'Changed knob detail image')
    for item in knob_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed knob detail source')
    status=read(comparison/index['side_status'])
    require(len(status['groups']['fitted']['observations'])==3 and len(status['groups']['held_out']['observations'])==2,
            'Missing side status fitted or held-out views')
    for joint in status['saved_joints'].values():
        require(joint['plate_solids']==1 and joint['plate_shell_overlap_mm3']>.01 and
                len(joint['detail_plate_gaps_mm'])==5 and max(joint['detail_plate_gaps_mm'].values())<.01,
                'Detached recessed status panel or markings')
    require(len(status['cavity_probes'])==6 and all(p['recess_probe_overlap_mm3']<1e-6 and
            p['backing_probe_overlap_mm3']>.001 and max(p['outward_occlusion_overlap_mm3'])<1e-6
            for p in status['cavity_probes']), 'Status panel recess, backing or occlusion check failed')
    require(len(status['view_visibility'])==5 and sum(len(v['rays']) for v in status['view_visibility'])==75 and
            max(r['cladding_intersection_length_mm'] for v in status['view_visibility'] for r in v['rays'])<.01,
            'Side status markings occluded by cladding in reference cameras')
    status_detail=read(comparison/index['side_status_detail'])
    require(status_detail['fcstd_sha256']==model_hash and
            status_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale side status detail')
    require(digest(root/status_detail['image_path'])==status_detail['image_sha256'], 'Changed side status detail image')
    for item in status_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed side status detail source')
    socket=read(comparison/index['side_socket'])
    require([len(o['reference_px']) for o in socket['observations']]==[7,12,11,6],
            'Missing side socket rim observations')
    for joint in socket['saved_joints'].values():
        require(joint['body_solids']==joint['back_solids']==1 and
                max(joint['lip_body_gap_mm'],joint['body_back_gap_mm'])<.01 and
                min(joint['lip_body_overlap_mm3'],joint['body_back_overlap_mm3'],joint['back_shell_overlap_mm3'])>.01,
                'Detached rolled side socket or backing')
        require(joint['mouth_cavity_body_intersection_mm']<.01, 'Filled side socket mouth')
    require(len(socket['view_visibility'])==4 and sum(len(v['rays']) for v in socket['view_visibility'])==36 and
            max(r['cladding_intersection_length_mm'] for v in socket['view_visibility'] for r in v['rays'])<.01,
            'Side socket rim occluded by cladding')
    socket_detail=read(comparison/index['side_socket_detail'])
    require(socket_detail['fcstd_sha256']==model_hash and
            socket_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale side socket detail')
    require(digest(root/socket_detail['image_path'])==socket_detail['image_sha256'], 'Changed side socket detail image')
    for item in socket_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed side socket detail source')
    flange=read(comparison/index['flange_detail'])
    require(flange['fcstd_sha256']==model_hash, 'Stale flange detail readback')
    require(flange['measurement_script_sha256']==digest(root/'tools/measure_drone_flange_detail.py'),
            'Changed flange measurement script')
    require(flange['source_review_sha256']==digest(comparison/'flange-detail-review.json'), 'Changed flange source interpretation')
    for source in read(comparison/'flange-detail-review.json')['sources']:
        require(digest(root/source['path'])==source['sha256'], 'Changed flange reference image')
    for side in flange['sides'].values():
        require(side['valid'] and side['solids']==2 and len(side['holes'])==34 and
                not side['old_screw_heads_present'], 'Invalid split perforated flange')
        require(all(abs(h['radius_mm']-1.7)<1e-5 and h['flange_axis_intersection_mm']<.01 for h in side['holes']),
                'Flange hole blocked or wrong radius')
        require(len(side['web_probes'])==30 and min(p['material_length_mm'] for p in side['web_probes'])>1 and
                len(side['split_axis_intersection_mm'])==8 and max(side['split_axis_intersection_mm'])<.01, 'Missing flange web or split')
        require(len(side['bridge_wires'])==2 and all(w['valid'] and w['solids']==1 and w['cap_count']==2 and
                min(w['end_flange_overlap_mm3'])>.01 for w in side['bridge_wires']), 'Detached flange bridge wire')
        require(side['bowl_valid'] and side['bowl_solids']==1 and len(side['cavity_probes'])==4 and
                all(p['mouth_probe_overlap_mm3']<1e-6 and p['deeper_wall_intersection_mm']>1
                    for p in side['cavity_probes']), 'Side ring bowl lacks a real recessed wall')
    flange_detail=read(comparison/index['flange_comparison'])
    require(flange_detail['fcstd_sha256']==model_hash and
            flange_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale flange comparison')
    require(digest(root/flange_detail['image_path'])==flange_detail['image_sha256'], 'Changed flange comparison image')
    for source in flange_detail['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed flange comparison input')
    rear_rake=read(comparison/index['rear_rake'])
    require(rear_rake['fcstd_sha256']==model_hash, 'Stale rear rake readback')
    require(rear_rake['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed rear rake cameras')
    require(rear_rake['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed rear rake source video')
    require(rear_rake['measurement_script_sha256']==digest(root/'tools/measure_drone_rear_rake.py'),
            'Changed rear rake measurement script')
    require(len(rear_rake['parts'])==6 and all(p['valid'] and p['closed'] and
            p['solids']==1 and p['bop_check_passed'] for p in rear_rake['parts']),
            'Invalid or self-intersecting reconstructed rear pieces')
    require(len(rear_rake['contacts'])==6 and all(p['gap_mm']<.01 for p in rear_rake['contacts']),
            'Disconnected rear trim through structural frame')
    require(len(rear_rake['probes'])==12 and all(
            p['overlap_mm3']>.5 if p['kind']=='sloped_panel' else p['overlap_mm3']<1e-7
            for p in rear_rake['probes']), 'Incorrect rear sloped material or retained vertical spur')
    require([len(o['reference_px']) for o in rear_rake['observations']]==[10,10,6],
            'Missing rear corner reference traces')
    rear_rake_detail=read(comparison/index['rear_rake_detail'])
    require(rear_rake_detail['fcstd_sha256']==model_hash, 'Stale rear rake detail')
    require(rear_rake_detail['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed rear rake detail cameras')
    require(digest(root/rear_rake_detail['image_path'])==rear_rake_detail['image_sha256'],
            'Changed rear rake detail image')
    for item in rear_rake_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed rear rake detail source')
    transition=read(comparison/index['rear_transition'])
    require(transition['fcstd_sha256']==model_hash, 'Stale rear transition readback')
    require(transition['measurement_script_sha256']==digest(root/'tools/measure_drone_rear_transition.py'),
            'Changed rear transition measurement script')
    require(transition['camera_config_sha256']==digest(comparison/'cameras.json') and
            transition['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed rear transition source or cameras')
    require(transition['object_id_manifest_sha256']==digest(
            (comparison/index['contour_attribution']).parent/'object-id-manifest.json'),
            'Changed rear transition object-ID input')
    require([len(o['reference_px']) for o in transition['observations']]==[6,7,7,7],
            'Missing visible rear transition boundary samples')
    require(transition['max_distance_px']<22.75, 'Rear transition sampled boundary exceeds local target')
    # The adjacent service panel is separated by a visible-piece seam.
    # Connectivity runs through the structural frame, which also meets the panel.
    attached=[c for c in transition['contacts'] if c['objects'][1]!='RearServicePanel']
    require(len(transition['contacts'])==6 and len(attached)==4 and
            all(c['gap_mm']<.01 for c in attached), 'Detached curved rear transition')
    require(len(transition['parts'])==2 and all(p['valid'] and p['solids']==1 for p in transition['parts']) and
            not transition['rear_armour_bolt_objects'], 'Invalid rear transition or retained obsolete screws')
    transition_detail=read(comparison/index['rear_transition_detail'])
    require(transition_detail['fcstd_sha256']==model_hash and
            transition_detail['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Stale rear transition comparison')
    require(digest(root/transition_detail['image_path'])==transition_detail['image_sha256'],
            'Changed rear transition comparison image')
    for item in transition_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed rear transition comparison source')
    cable=read(comparison/index['side_cable'])
    require(cable['valid'] and cable['bop_check_passed'] and cable['solids']==1 and cable['cap_count']==2 and
            max(abs(r-1.8) for r in cable['sampled_section_radius_range_mm'])<1e-4,
            'Invalid swept side cable or section radius')
    require([len(o['reference_px']) for o in cable['groups']['fitted']['observations']]==[44,40] and
            [len(o['reference_px']) for o in cable['groups']['held_out']['observations']]==[31],
            'Missing side cable fitted or held-out observations')
    require(len(cable['contacts'])==2 and all(c['terminal_error_mm']<.01 and c['boot_valid'] and
            c['boot_solids']==1 and min(c['cable_boot_overlap_mm3'],c['boot_mount_overlap_mm3'])>.01
            for c in cable['contacts']), 'Detached side cable terminal or boot')
    cable_detail=read(comparison/index['side_cable_detail'])
    require(cable_detail['fcstd_sha256']==model_hash and
            cable_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale side cable comparison')
    require(digest(root/cable_detail['image_path'])==cable_detail['image_sha256'], 'Changed side cable comparison image')
    for source in cable_detail['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed side cable comparison input')
    front=read(comparison/index['front_control'])
    front_fit=read(comparison/'front-control-fit.json')
    require(front['fcstd_sha256']==model_hash, 'Stale front control readback')
    require(front['source_fit_sha256']==digest(comparison/'front-control-fit.json'), 'Changed front control fit')
    require(front['camera_config_sha256']==front_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed front control cameras')
    require(front['source_video_sha256']==front_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed front control source video')
    require(front_fit['fit_script_sha256']==digest(root/'tools/fit_drone_front_control.py') and
            front['measurement_script_sha256']==digest(root/'tools/measure_drone_front_control.py'),
            'Changed front control measurement scripts')
    require(set(front['groups'])=={'rail','buttons','knobs'}, 'Missing front control observation groups')
    for name,count in [('rail',4),('buttons',4),('knobs',3)]:
        observations=front['groups'][name]['observations']
        require(len(observations)==3 and all(len(o['reference_px'])==count for o in observations),
                'Incomplete front control observations: '+name)
    require(len(front['saved_joints'])==21 and max(j['gap_mm'] for j in front['saved_joints'].values())<.01,
            'Detached front control parts')
    front_detail=read(comparison/index['front_detail'])
    require(front_detail['fcstd_sha256']==model_hash, 'Stale front control detail')
    require(front_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed front detail cameras')
    require(digest(root/front_detail['image_path'])==front_detail['image_sha256'], 'Changed front detail image')
    for item in front_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed front detail source')
    rear=read(comparison/index['rear_rail'])
    rear_fit=read(comparison/'rear-rail-fit.json')
    require(rear['fcstd_sha256']==model_hash, 'Stale rear panel readback')
    require(rear['source_fit_sha256']==digest(comparison/'rear-rail-fit.json'), 'Changed rear panel fit')
    require(rear['camera_config_sha256']==rear_fit['camera_config_sha256']==digest(comparison/'cameras.json'),
            'Changed rear panel cameras')
    require(rear['source_video_sha256']==rear_fit['source_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed rear panel source video')
    require(rear_fit['fit_script_sha256']==digest(root/'tools/fit_drone_rear_rail.py') and
            rear['measurement_script_sha256']==digest(root/'tools/measure_drone_rear_rail.py'),
            'Changed rear panel measurement scripts')
    require(len(rear['observations'])==3 and sum(len(o['reference_px']) for o in rear['observations'])==12,
            'Missing rear panel observations')
    require(len(rear['beacon_observations'])==2 and sum(len(o['reference_px']) for o in rear['beacon_observations'])==24,
            'Missing beacon silhouette observations')
    require(len(rear['vent_cavity_probes'])==7 and max(o['plate_overlap_mm3'] for o in rear['vent_cavity_probes'])<1e-6,
            'Rear slot cavity checks failed')
    rear_detail=read(comparison/index['rear_detail'])
    require(rear_detail['fcstd_sha256']==model_hash, 'Stale rear panel detail')
    require(rear_detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed rear detail cameras')
    require(digest(root/rear_detail['image_path'])==rear_detail['image_sha256'], 'Changed rear detail image')
    for item in rear_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed rear detail source')
    detail=read(comparison/index['cheek_detail'])
    require(detail['fcstd_sha256']==model_hash, 'Stale cheek detail board')
    require(detail['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed cheek detail cameras')
    require(digest(root/detail['image_path'])==detail['image_sha256'], 'Changed cheek detail image')
    for item in detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed cheek detail source')
    attribution_path=comparison/index['contour_attribution']
    attribution=read(attribution_path)
    require(attribution['fcstd_sha256']==model_hash, 'Stale contour attribution')
    require(attribution['comparison_report_sha256']==digest(comparison/index['video_comparison']),
            'Changed contour attribution comparison')
    ids=read(attribution_path.parent/'object-id-manifest.json')
    check_render_identity(ids)
    require(ids['fcstd_sha256']==model_hash and len(ids['images'])==10, 'Stale or missing object ID views')
    require(ids['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed object ID cameras')
    for item in ids['images']:
        require(digest(attribution_path.parent/item['path'])==item['sha256'], 'Changed object ID render')
    fairing=read(comparison/index['nozzle_fairing'])
    require(fairing['fcstd_sha256']==model_hash and
            fairing['camera_config_sha256']==digest(comparison/'cameras.json'), 'Stale nozzle fairing comparison')
    require(fairing['measurement_script_sha256']==digest(root/'tools/measure_drone_nozzle_fairing.py'),
            'Changed nozzle fairing measurement script')
    require(fairing['object_id_manifest_sha256']==digest(attribution_path.parent/'object-id-manifest.json'),
            'Changed nozzle fairing object-ID input')
    require(fairing['reference_video_sha256']==digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'),
            'Changed nozzle fairing reference video')
    require([len(o['reference_px']) for o in fairing['observations']]==[11,12,12],
            'Missing nozzle fairing samples')
    require(fairing['max_px']<22.75,
            f"Nozzle fairing local target exceeded: {fairing['max_px']:.2f} px > 22.75 px")
    for item in fairing['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed nozzle fairing comparison source')
    require(digest(root/fairing['image_path'])==fairing['image_sha256'], 'Changed nozzle fairing comparison board')
    fairing_detail=read(comparison/index['nozzle_fairing_detail'])
    require(fairing_detail['fcstd_sha256']==model_hash and fairing_detail['camera_config_sha256']==
            digest(comparison/'cameras.json'), 'Stale nozzle fairing detail board')
    require(digest(root/fairing_detail['image_path'])==fairing_detail['image_sha256'],
            'Changed nozzle fairing detail board')
    for item in fairing_detail['source_files']:
        require(digest(root/item['path'])==item['sha256'], 'Changed nozzle fairing detail source')
    surface=read(comparison/index['nozzle_surfaces'])
    require(surface['fcstd_sha256']==model_hash and surface['measurement_script_sha256']==
            digest(root/'tools/measure_drone_nozzle_surfaces.py'), 'Stale nozzle surface checks')
    require(surface['passed'] and len(surface['parts'])==5 and all(p['valid'] and
            p['closed'] and p['solids']==1 for p in surface['parts']), 'Invalid nozzle surfaces')
    require(len(surface['contacts'])==6 and all(c['gap_mm']<.01 for c in surface['contacts']),
            'Detached nozzle surface patch or collar')
    require(len(surface['surface_probes'])==15 and all(p['forward_exposure_mm']>.1
            for p in surface['surface_probes']), 'Nozzle surface patch hidden by shell')
    require(surface['woofer_shell_overlap_mm3']<1e-6, 'Nozzle surface intersects woofer reservation')
    cavity=read(comparison/index['rear_cavity'])
    require(cavity['fcstd_sha256']==model_hash and cavity['measurement_script_sha256']==
            digest(root/'tools/measure_drone_rear_cavity.py'), 'Stale rear cavity checks')
    require(cavity['baseline_fcstd_sha256']==index['preservation_baseline_model_sha256'],
            'Changed rear cavity preservation baseline')
    lip_contact=read(comparison/'nozzle-lip-contact-check.json')
    require(lip_contact['passed'] and lip_contact['fcstd_sha256']==model_hash and
            lip_contact['measurement_script_sha256']==digest(root/'tools/measure_drone_nozzle_lip.py') and
            len(lip_contact['parts'])==3 and len(lip_contact['interior_contact_probes'])==24 and
            len(lip_contact['petal_contacts'])==12, 'Nozzle lip layering/contact check failed')
    require(index['rear_cavity_baseline_sha256']==index['preservation_baseline_model_sha256']==
            '73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07',
            'Expected exact v52 preservation checkpoint')
    preservation=read(comparison/index['rear_cavity_preservation'])
    width=read(comparison/index['rear_side_width'])
    transfer=read(comparison/index['rear_side_width_archive'])
    native=read(comparison/index['rear_side_width_gui'])
    profile_source=read(comparison/index['rear_profile_source'])
    require(profile_source['passed'] and
            profile_source['generator_sha256']==digest(root/'tools/drone_concept.py') and
            profile_source['source_module_sha256']==digest(root/'tools/drone_belly_relief.py') and
            profile_source['baseline_fcstd_sha256']==index['rear_cavity_baseline_sha256'] and
            profile_source['candidate_fcstd_sha256']==width['candidate_fcstd_sha256'] and
            len(profile_source['parts'])==7 and
            set(p['name'] for p in profile_source['parts'])==set(index['iteration_expected_changes']) and
            all(p['advanced_check_passed'] and p['source_difference_mm3']<1e-6
                for p in profile_source['parts']),
            'Belly relief source/readback mismatch')
    require(transfer['passed'] and transfer['fcstd_sha256']==model_hash and
            transfer['baseline_fcstd_sha256']==index['rear_cavity_baseline_sha256'] and
            transfer['candidate_fcstd_sha256']==width['candidate_fcstd_sha256'] and
            transfer['gui_document_preserved_exactly'] and transfer['changed_count']==7 and
            transfer['unchanged_shape_payloads']==691 and
            len(transfer['shape_payloads'])==698 and all(p['exact_payload_match'] for p in transfer['shape_payloads']),
            'Unchanged BRep or GUI payload preservation failed')
    require(native['passed'] and native['fcstd_sha256']==model_hash and
            native['object_count']==700 and native['visible_shapes']==696 and native['view_providers']==700 and
            native['native_matches_serialized_colors'] and not native['serialized_mismatches'] and
            len(native['colors'])==696,
            'Native GUI open verification failed')
    require(width['passed'] and width['fcstd_sha256']==model_hash and
            width['candidate_fcstd_sha256']==digest(comparison/index['rear_side_width_candidate']) and
            width['measurement_script_sha256']==digest(root/'tools/measure_drone_belly_relief.py') and
            len(width['candidate_comparisons'])==7 and
            all(p['symmetric_difference_mm3']<1e-6 for p in width['candidate_comparisons']),
            'Belly relief candidate/readback mismatch')
    require(len(width['preserved_objects'])==691 and len(width['shafts'])==4 and
            all(p['name'] in width['preserved_objects'] and p['symmetric_difference_mm3']<1e-6 for p in width['shafts']) and
            all(name in width['preserved_objects'] for name in
                ['BassInnerThroat','BassVisualCone','BassDustCap','RearRecessLiner',
                 'BassNozzleRolledLip','BassNozzleMouthRing',*[f'NozzlePetal{i}' for i in range(12)]]),
            'Changed protected shafts, cavity or nozzle endpoints')
    require(width['central_strip_width_mm']==64 and width['central_strip_symmetric_difference_mm3']<1e-6 and
            width['outer_floor_z_mm']==52.5 and len(width['floor_probes'])==12 and
            all(p['inside_at_floor_plus_0_1'] and p['outside_at_floor_minus_0_1'] for p in width['floor_probes']),
            'Central support strip or closed belly shelf differs from the selected geometry')
    require(len(width['contacts'])==7 and all(p['gap_mm']<.01 and p['overlap_mm3']>.001 for p in width['contacts']) and
            len(width['service_screws'])==4 and all(p['advanced_check_passed'] and p['plate_gap_mm']<.01 for p in width['service_screws']),
            'Belly, support seat, loop or service plate contact failed')
    markings=read(comparison/index['warning_marking'])
    require(markings['fcstd_sha256']==model_hash and
            markings['baseline_fcstd_sha256']==index['preservation_baseline_model_sha256'] and
            markings['measurement_script_sha256']==digest(root/'tools/measure_drone_nozzle_markings.py') and
            markings['camera_sha256']==digest(comparison/'cameras.json') and
            markings['observations_sha256']==digest(comparison/'nozzle-marking-study/observations.json'),
            'Stale warning marking observations or saved render')
    require(markings['metrics']['current']['triangle']['count']==9 and
            markings['metrics']['current']['plaque']['count']==23 and
            markings['metrics']['current']['triangle']['rms_px']<4.5 and
            markings['metrics']['current']['plaque']['rms_px']<1.3,
            'Warning marking boundary realization regressed')
    require(digest(Path(markings['image_path']))==markings['image_sha256'], 'Changed marking board')
    for source in markings['source_files']:
        require(digest(Path(source['path']))==source['sha256'], 'Changed marking comparison input')
    channel=read(comparison/'petal-hardware-width.json')
    require(channel['fcstd_sha256']==model_hash and channel['measurement_script_sha256']==digest(root/'tools/measure_drone_petal_channel_width.py') and
            channel['camera_config_sha256']==digest(comparison/'cameras.json') and
            channel['object_id_manifest_sha256']==digest(attribution_path.parent/'object-id-manifest.json'),
            'Stale petal guide separation diagnostic')
    measured=[r for r in channel['observations'] if r['both_rails_visible']]
    require({r['petal_index'] for r in measured}=={8,9} and channel['measured_pairs_count']==2 and
            channel['rms_separation_error_px']<=.8, 'Visible guide separation regressed')
    require(digest(root/channel['image_path'])==channel['image_sha256'], 'Changed guide separation image')
    for source in channel['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed guide separation evidence')
    petal_still=read(comparison/'petal-hardware-still04.json')
    require(petal_still['fcstd_sha256']==model_hash and
            petal_still['camera_config_sha256']==digest((comparison/index['still_comparison']).parent/'cameras.json') and
            petal_still['script_sha256']==digest(root/'tools/compare_drone_petal_detail.py'),
            'Stale fixed still-04 hardware detail')
    require(digest(root/petal_still['image_path'])==petal_still['image_sha256'], 'Changed still-04 detail')
    for source in petal_still['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed still-04 comparison evidence')
    rim=read(comparison/'status-rim-check.json')
    require(rim['measurement_script_sha256']==digest(root/'tools/measure_drone_status_rim_edge.py') and
            len(rim['results'])==2, 'Stale status rim boundary check')
    current_rim=rim['results'][1]
    require(current_rim['fcstd_sha256']==model_hash and
            current_rim['camera_config_sha256']==digest(comparison/'cameras.json') and
            current_rim['reference_px']==[[563,420],[563,450],[563,475],[563,487],[556,499],[543,512],[529,524]] and
            current_rim['rms_px']<=1.20 and current_rim['max_px']<=3.01,
            'Status rim boundary regressed')
    for row in rim['results']:
        require(row['id_manifest_sha256']==digest(root/row['id_manifest_path']), 'Changed rim ID evidence')
    require(digest(root/rim['image_path'])==rim['image_sha256'], 'Changed rim comparison image')
    for source in rim['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed rim comparison source')
    visibility=read(comparison/'status-rim-visibility.json')
    require(visibility['camera_config_sha256']==digest(comparison/'cameras.json') and
            visibility['script_sha256']==digest(root/'tools/measure_drone_status_rim.py') and
            visibility['results'][1]['fcstd_sha256']==model_hash and
            len(visibility['results'][1]['rays'])==50 and not visibility['new_occlusions'] and
            not any(r['occluded'] for r in visibility['results'][1]['rays']),
            'Status slot or bracket visibility regressed')
    notch=read(comparison/'guard-notch-check.json')
    require(notch['measurement_script_sha256']==digest(root/'tools/measure_drone_guard_notch.py') and
            len(notch['results'])==2, 'Stale guard-notch boundary check')
    current_notch=notch['results'][1]
    require(current_notch['fcstd_sha256']==model_hash and
            current_notch['camera_config_sha256']==digest(comparison/'cameras.json') and
            current_notch['reference_px']==[[563,487],[556,499],[543,512],[529,524]] and
            current_notch['rms_px']<=6.23 and current_notch['max_px']<=12.01,
            'Guard-notch fitted-view boundary missing or regressed')
    for row in notch['results']:
        require(row['id_manifest_sha256']==digest(root/row['id_manifest_path']),
                'Changed guard-notch ID evidence')
    require(digest(root/notch['image_path'])==notch['image_sha256'], 'Changed guard-notch comparison image')
    for source in notch['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed guard-notch comparison source')
    require(preservation['passed'] and preservation['fcstd_sha256']==model_hash and
            preservation['baseline_fcstd_sha256']==index['rear_cavity_baseline_sha256'] and
            set(preservation['changed_objects'])==set(index['iteration_expected_changes']) and
            set(preservation.get('removed_objects',[]))==set(index.get('iteration_expected_removals',[])) and
            set(preservation.get('added_objects',[]))==set(index.get('iteration_expected_additions',[])),
            'Unexpected geometry or appearance change outside this iteration')
    require(cavity['passed'] and len(cavity['parts'])==4 and all(p['valid'] and p['closed'] and
            p['solids']==1 for p in cavity['parts']), 'Invalid rear cavity geometry')
    require(len(cavity['shafts'])==4 and all(p['symmetric_difference_mm3']<1e-6
            for p in cavity['shafts']), 'Rear cavity changed protected shafts')
    require(len(cavity['void_probes'])==6 and all(p['current_overlap_mm3']<1e-6
            for p in cavity['void_probes']), 'Rear cavity remains filled')
    require(len(cavity['wall_probes'])==4 and all(p['liner_overlap_mm3']>.01
            for p in cavity['wall_probes']), 'Rear cavity wall missing')
    require(len(cavity['contacts'])==3 and all(p['gap_mm']<.01 and p['overlap_mm3']>.001
            for p in cavity['contacts']), 'Rear cavity light or liner detached')
    for key in index['rear_cavity_details']:
        detail=read(comparison/key)
        require(detail['fcstd_sha256']==model_hash and detail['camera_config_sha256']==
                digest(comparison/'cameras.json'), 'Stale rear cavity detail')
        require(digest(root/detail['image_path'])==detail['image_sha256'], 'Changed rear cavity board')
        for source in detail['source_files']:
            require(digest(root/source['path'])==source['sha256'], 'Changed rear cavity detail source')
    nozzle_side=read(comparison/index['nozzle_side'])
    require(nozzle_side['fcstd_sha256']==model_hash and nozzle_side['measurement_script_sha256']==
            digest(root/'tools/measure_drone_nozzle_side.py'), 'Stale nozzle exposed-side checks')
    require(nozzle_side['camera_config_sha256']==digest(comparison/'cameras.json') and
            nozzle_side['object_id_manifest_sha256']==digest(attribution_path.parent/'object-id-manifest.json'),
            'Changed nozzle side camera or ID input')
    require(len(nozzle_side['boundary_objects'])==12 and len(nozzle_side['observations'])==2 and
            all(len(o['samples'])==7 for o in nozzle_side['observations']), 'Missing nozzle exposed-side samples')
    require(nozzle_side['max_px']<22.75 and nozzle_side['max_source_threshold_spread_px']<=2,
            'Nozzle exposed-side target or source stability failed')
    require(digest(root/nozzle_side['image_path'])==nozzle_side['image_sha256'], 'Changed nozzle side board')
    for source in nozzle_side['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed nozzle side source image')
    pitch=read(comparison/index['petal_pitch'])
    require(pitch['fcstd_sha256']==model_hash and pitch['measurement_script_sha256']==
            digest(root/'tools/measure_drone_petal_pitch.py'), 'Stale petal pitch diagnostic')
    require(pitch['camera_config_sha256']==digest(comparison/'cameras.json') and
            pitch['object_id_manifest_sha256']==digest(attribution_path.parent/'object-id-manifest.json'),
            'Changed petal pitch camera or ID input')
    require(pitch['native_source_frame_verified'] and pitch['reference_video_sha256']==
            digest(root/'references/alexander-shevchuk-drone/video-cam.mp4'), 'Changed petal pitch reference video')
    require(pitch['source_frame']==120 and pitch['row_px']==590 and len(pitch['observations'])==3,
            'Missing central petal guide samples')
    require(pitch['max_offset_px']<22.75, 'Central petal pitch target exceeded')
    require(digest(root/pitch['image_path'])==pitch['image_sha256'], 'Changed petal pitch board')
    for source in pitch['source_files']:
        require(digest(root/source['path'])==source['sha256'], 'Changed petal pitch source')
    seam=read(comparison/index['rear_seam'])
    require(seam['passed'] and seam['fcstd_sha256']==model_hash and
            seam['baseline_fcstd_sha256']==index['preservation_baseline_model_sha256'] and
            seam['measurement_script_sha256']==digest(root/'tools/measure_drone_rear_seam.py'),
            'Stale or failed rear common-face repair')
    require(len(seam['parts'])==2 and len(seam['slots'])==2 and
            seam['coplanar_y248_overlap_mm2']<1e-6 and seam['volume_overlap_mm3']<1e-6,
            'Rear carrier retains coincident faces')
    require(seam['seam_scope_z_min_mm']==134 and seam['union_added_volume_mm3']<1e-6 and
            abs(seam['union_removed_volume_mm3']-seam['expected_slot_removed_volume_mm3'])<1e-4,
            'Upper rear seam changed geometry outside the two slots')
    lighting=read(comparison/index['cavity_emitters'])
    require(lighting['passed'] and lighting['fcstd_sha256']==model_hash and
            lighting['measurement_script_sha256']==digest(root/'tools/measure_drone_cavity_emitters.py'),
            'Stale or failed cavity lighting readback')
    require(len(lighting['parts'])==12 and all(p['valid'] and p['closed'] and p['solids']==1
            and p['nozzle_shell_overlap_mm3']<1e-6 for p in lighting['parts']), 'Cavity lighting intersects nozzle shell')
    require(len(lighting['contacts'])==14 and all(c['gap_mm']<.01 and c['overlap_mm3']>.001
            for c in lighting['contacts']), 'Detached cavity rail, clamp or reflector')
    rail=read(comparison/index['cavity_rail'])
    require(rail['fcstd_sha256']==model_hash and len(rail['samples'])==12 and
            rail['measurement_script_sha256']==digest(root/'tools/measure_drone_cavity_rail.py') and
            rail['source_fit_sha256']==digest(comparison/'cavity-emitter-study/primary-rail-fit.json') and
            rail['object_id_manifest_sha256']==digest(attribution_path.parent/'object-id-manifest.json'),
            'Stale or incomplete cavity rail comparison')
    rail_fit=read(comparison/'cavity-emitter-study/primary-rail-fit.json')
    require(rail_fit['script_sha256']==digest(root/'tools/fit_drone_cavity_rail.py') and
            rail_fit['camera_config_sha256']==digest(comparison/'cameras.json'), 'Changed cavity rail fit inputs')
    for path,sha in rail_fit['source_files'].items():
        require(digest(root/path)==sha, 'Changed cavity rail reference frame')
    for path,sha in rail['source_files'].items():
        require(digest(root/path)==sha, 'Changed cavity rail ID image')
    result = {'passed':not errors, 'errors':errors, 'fcstd_sha256':model_hash,
              'visible_features':saved['visible_features'], 'step_solids':saved['step_solids'],
              'verified_images':len(images), 'reference_inputs':len(index['inputs']),
              'diagnostic_object_id_views':len(ids['images']),
              'turntable':probe, 'physical_validation':False,
              'visual_target_status':'not established by artifact integrity checks'}
    (cad/'delivery-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
