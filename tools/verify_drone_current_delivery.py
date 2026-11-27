"""Verify the current saved appearance package and its fixed-camera evidence."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
from xml.etree import ElementTree
from zipfile import ZipFile


SUPPORT_PREFIXES = ['SupportShaft', 'SupportFoot', 'SupportSocket', 'CentralSupportSeat']
DISPLAY_VIEWS = {'closeup', 'hero', 'rear', 'front', 'right', 'armour-detail',
                 'nozzle-detail', 'top', 'underside'}


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def verify(root: Path) -> dict:
    cad = root / 'cad/drone-concept'
    model_path = cad / 'vintrox-drone-concept.FCStd'
    model_hash = digest(model_path)
    step_hash = digest(cad / 'vintrox-drone-concept.step')
    geometry = read(cad / 'concept-manifest.json')
    saved = read(cad / 'readback-verification.json')
    package = cad / 'comparison' / geometry['revision']
    errors = []

    def require(condition, message):
        if not condition:
            errors.append(message)

    def check_media(folder, item):
        require(digest(folder / item['path']) == item['sha256'],
                f"Changed image or video: {folder / item['path']}")

    require(saved['passed'] and not saved['errors'], 'Saved CAD/STEP readback failed')
    require(saved['fcstd_sha256'] == geometry['fcstd_sha256'] == model_hash,
            'Saved FCStd reports differ from the current model')
    require(saved['step_sha256'] == geometry['step_sha256'] == step_hash,
            'Saved STEP reports differ from the current export')
    require(digest(package / 'candidate.FCStd') == model_hash
            and digest(package / 'candidate.step') == step_hash,
            'Reference package CAD or STEP differs from the current files')
    visible_count = saved['visible_features']
    require(geometry['visible_features'] == visible_count, 'Visible feature count differs')
    with ZipFile(model_path) as archive:
        gui = ElementTree.fromstring(archive.read('GuiDocument.xml'))
        files = list(dict.fromkeys(node.get('file') for node in gui.iter() if node.get('file')))
        file_set = set(files)
        require(files and [name for name in archive.namelist() if name in file_set] == files,
                'GUI resources are missing or out of XML registration order')
        visible = {node.attrib['name'] for node in gui.findall('.//ViewProvider')
                   if node.find('./Properties/Property[@name="Visibility"]/Bool[@value="true"]')
                   is not None}
        feature_names = {item['name'] for item in geometry['features']}
        require(len(visible & feature_names) == visible_count, 'Saved GUI visibility differs')

    previews = read(cad / 'renders/render-manifest.json')
    require(previews['fcstd_sha256'] == model_hash
            and previews['cad_geometry_features'] == visible_count, 'Stale presentation renders')
    require(len(previews['images']) == len(DISPLAY_VIEWS)
            and {item['view'] for item in previews['images']} == DISPLAY_VIEWS,
            'Presentation viewpoints differ')
    for item in [*previews['images'], previews['review_board'], previews['turntable']]:
        check_media(cad / 'renders', item)
    turntable = previews['turntable']
    probe = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=nb_frames',
        '-select_streams', 'v:0', '-of', 'json', str(cad / 'renders' / turntable['path']),
    ], text=True))
    require(abs(float(probe['format']['duration']) - 12) < .1
            and turntable['duration_seconds'] == 12
            and int(probe['streams'][0]['nb_frames']) >= turntable['unique_angles'] == 96,
            'Turntable duration or angle count differs')

    mesh_archive = read(package / 'mesh-archive.json')
    if mesh_archive.get('method') == 'rebuild-from-saved-fcstd':
        exporter = root / 'tools/export_saved_drone_meshes.py'
        exporter_hash = mesh_archive.get('exporter_sha256')
        require(mesh_archive['fcstd_sha256'] == model_hash
                and (exporter_hash is None or exporter_hash == digest(exporter))
                and mesh_archive['visible_features'] == visible_count,
                'Mesh rebuild record differs from current CAD or exporter')
    elif 'parts' in mesh_archive:
        parts = mesh_archive['parts']
        require(bool(parts), 'Mesh archive has no parts')
        archive_hash = hashlib.sha256()
        for part in parts:
            part_hash = hashlib.sha256()
            with (package / part['path']).open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    part_hash.update(chunk)
                    archive_hash.update(chunk)
            require(part_hash.hexdigest() == part['sha256'],
                    f"Changed mesh archive part: {part['path']}")
        require(archive_hash.hexdigest() == mesh_archive['sha256'],
                'Combined mesh archive hash differs')
    else:
        check_media(package, mesh_archive)
    native_folder = package / 'native-display'
    native = read(native_folder / 'native-display-verification.json')
    require(native['status'] == 'native-open-and-view-capture-completed', 'Native display audit failed')
    native_model, = native['models']
    require(native_model['fcstd_sha256'] == native_model['mesh_fcstd_sha256'] == model_hash,
            'Native display audit differs from current CAD')
    if mesh_archive.get('method') != 'rebuild-from-saved-fcstd':
        require(native_model['palette_contract_sha256'] == mesh_archive['uncompressed_sha256'],
                'Native display audit differs from current mesh archive')
    require(native_model['visible_objects'] == visible_count
            and native_model['native_visibility_equals_mesh']
            and native_model['file_unchanged_after_native_close']
            and native_model['native_color_triples'] > 1
            and 0 <= native_model['max_native_vs_mesh_channel_difference'] <= .5 / 255 + 1e-6,
            'Native visibility or colors differ')
    require(len(native_model['views']) == 4
            and {item['view'] for item in native_model['views']} == {'isometric', 'front', 'rear', 'right'},
            'Missing native display viewpoints')
    for item in native_model['views']:
        check_media(native_folder, item)

    references = root / 'references/alexander-shevchuk-drone'
    source_video_hash = digest(references / 'video-cam.mp4')
    contact_sheet = references / 'video-cam.jpeg'
    contact_sheet_hash = digest(contact_sheet)
    source_index = read(cad / 'comparison/review-index.json')
    sheet_source, = [item for item in source_index['inputs']
                     if item['source'] == contact_sheet.relative_to(root).as_posix()]
    require(sheet_source['sha256'] == contact_sheet_hash, 'Changed reference contact sheet')
    source_stills = {path.relative_to(root).as_posix()
                     for path in [*references.glob('alexander-shevchuk-*.jpg'),
                                  references / 'closeup-2026-10-19.png']}
    scores = {}
    comparisons = [('video', 'video', 'cameras.json'),
                   ('stills', 'still', 'still-cameras.json'),
                   ('sheet', 'sheet', 'contact-sheet-cameras.json')]
    for group, render_group, camera_file in comparisons:
        comparison = package / f'{group}-comparison'
        renders = package / f'{render_group}-renders'
        camera_path = comparison / 'cameras.json'
        cameras = read(camera_path)
        report = read(comparison / 'comparison-report.json')
        manifest_path = renders / 'render-manifest.json'
        manifest = read(manifest_path)
        require(report['fcstd_sha256'] == manifest['fcstd_sha256'] == model_hash,
                f'Stale {group} comparison')
        require(report['camera_config_sha256'] == manifest['camera_config_sha256']
                == digest(camera_path) == digest(cad / 'comparison' / camera_file),
                f'Changed {group} fixed cameras')
        require(report['render_manifest_sha256'] == digest(manifest_path),
                f'Changed {group} render manifest')
        require(report['excluded_from_cad'] == manifest['excluded_added_support_prefixes']
                == SUPPORT_PREFIXES, f'Changed {group} support exclusion')
        require(cameras['reference_video_sha256'] == report['reference_video_sha256']
                == source_video_hash, 'Changed reference video')
        names = [item['name'] for item in cameras['views']]
        require(names == [item['view'] for item in manifest['images']]
                == [item['view'] for item in report['views']]
                and len(set(names)) == len(names), f'Incomplete {group} views')
        if group == 'video':
            require([view['source_frame'] for view in cameras['views']] == list(range(0, 300, 30)),
                    'Missing views around the reference video orbit')
            require(sheet_source['comparison_views'] == names, 'Contact sheet views differ')
        elif group == 'stills':
            require(len(names) == 7 and {view['source_image'] for view in cameras['views']} == source_stills,
                    'Missing independent still references')
            for view in cameras['views']:
                require(digest(root / view['source_image']) == view['source_sha256'],
                        f"Changed reference still: {view['source_image']}")
        else:
            width, height = cameras['resolution']
            crops = [[c * width, r * height, (c + 1) * width, (r + 1) * height]
                     for r in range(2) for c in range(5)]
            require([view['source_crop'] for view in cameras['views']] == crops
                    and [view['matched_video_frame'] for view in cameras['views']] == list(range(14, 300, 30))
                    and cameras['orbit_cameras_sha256'] == digest(cad / 'comparison/cameras.json'),
                    'Incomplete sheet cells or changed camera source')
            for view, score in zip(cameras['views'], report['views']):
                require(view['source_image'] == contact_sheet.relative_to(root).as_posix()
                        and view['source_image'] == score['source_image']
                        and view['source_sha256'] == contact_sheet_hash
                        and view['source_crop'] == score['source_crop']
                        and view['matched_video_frame'] == score['matched_video_frame'],
                        f"Changed contact sheet reference: {view['name']}")
        for item in manifest['images']:
            check_media(renders, item)
        for name in names:
            for suffix in ('overlay', 'difference', 'edges', 'comparison'):
                require((comparison / f'{name}-{suffix}.png').is_file(),
                        f'Missing {name} {suffix}')
        require((comparison / 'comparison-board.png').is_file(), f'Missing {group} comparison board')
        ious = [item['silhouette_iou'] for item in report['views']]
        mean = sum(ious) / len(ious)
        require(all(0 <= iou <= 1 for iou in ious)
                and math.isclose(mean, report['mean_silhouette_iou'], abs_tol=1e-12),
                f'Inconsistent {group} IoU')
        scores[group] = {'views': len(names), 'mean_silhouette_iou': mean}

    return {
        'passed': not errors, 'errors': errors, 'revision': geometry['revision'],
        'fcstd_sha256': model_hash, 'step_sha256': step_hash,
        'visible_features': visible_count, 'step_solids': saved['step_solids'],
        'screen_panel_mm': saved['screen_panel_mm'], 'active_area_mm': saved['active_area_mm'],
        'support_shafts': len(saved['central_support_shafts']),
        'native_display_views': len(native_model['views']),
        'native_max_color_channel_difference': native_model['max_native_vs_mesh_channel_difference'],
        'presentation_images': len(previews['images']), 'turntable': probe,
        'reference_video_sha256': source_video_hash,
        'reference_contact_sheet_sha256': contact_sheet_hash,
        'reference_contact_sheet_use': 'Direct cropped cells at their matched video poses',
        'comparisons': scores, 'physical_validation': False,
        'visual_target_status': 'Artifact integrity check; component contour target requires visual evidence',
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='Write the current report to this path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cad = root / 'cad/drone-concept'
    result = verify(root)
    encoded = json.dumps(result, indent=2) + '\n'
    output = args.output or cad / 'delivery-verification-current.json'
    output.write_text(encoded, encoding='utf-8')
    print(encoded, end='')
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
