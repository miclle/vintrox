"""Match reference sheet cells to video frames and recover their orbit cameras."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cameras', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    references = root / 'references/alexander-shevchuk-drone'
    sheet_path = references / 'video-cam.jpeg'
    video_path = references / 'video-cam.mp4'
    video_hash = digest(video_path)
    cameras = json.loads(args.cameras.read_text())
    if cameras['reference_video_sha256'] != video_hash:
        raise ValueError('Video differs from calibrated cameras')
    poses = cameras['views']
    if [pose['source_frame'] for pose in poses] != list(range(0, 300, 30)):
        raise ValueError('Expected calibrated cameras every 30 frames')
    first = poses[0]
    center = complex(*first['target_mm'][:2])
    first_eye = complex(*first['eye_mm'][:2])
    for pose in poses:
        angle = -math.tau * pose['source_frame'] / 300
        expected = center + (first_eye - center) * complex(math.cos(angle), math.sin(angle))
        if abs(complex(*pose['eye_mm'][:2]) - expected) > 1e-6:
            raise ValueError('Expected a clockwise circular camera orbit')
        for key in ('target_mm', 'lens_mm', 'sensor_width_mm', 'projection'):
            if pose[key] != first[key]:
                raise ValueError(f'Camera parameter varies over the orbit: {key}')
        if pose['eye_mm'][2] != first['eye_mm'][2] or pose.get('roll_degrees', 0) != 0:
            raise ValueError('Expected constant camera height with zero roll')

    width, height = cameras['resolution']
    match_size = width // 10, height // 10
    raw = subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(video_path), '-vf',
        f'scale={match_size[0]}:{match_size[1]}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-',
    ])
    frames = np.frombuffer(raw, dtype=np.uint8).reshape(-1, match_size[1], match_size[0], 3)
    if len(frames) != 300:
        raise ValueError('Expected 300 video frames')
    intensity = frames.max(axis=-1).reshape(len(frames), -1).astype(float)
    intensity /= np.linalg.norm(intensity, axis=1)[:, None]

    with Image.open(sheet_path) as source:
        sheet = source.convert('RGB')
    cell_width, cell_height = width // 2, height // 2
    if sheet.size != (cell_width * 5, cell_height * 2):
        raise ValueError('Expected a five-column, two-row reference sheet')
    views = []
    for index in range(10):
        row, column = divmod(index, 5)
        left, top = column * cell_width, row * cell_height
        crop = (left, top, left + cell_width, top + cell_height)
        cell = np.asarray(sheet.crop(crop).resize(match_size, Image.Resampling.LANCZOS))
        cell = cell.max(axis=-1).flatten().astype(float)
        scores = intensity @ (cell / np.linalg.norm(cell))
        runner_up, frame = np.argsort(scores)[-2:]
        if scores[frame] < .99 or scores[frame] - scores[runner_up] < .004:
            raise ValueError(f'Ambiguous source frame for contact sheet cell {index + 1}')
        angle = -math.tau * int(frame) / 300
        eye = center + (first_eye - center) * complex(math.cos(angle), math.sin(angle))
        views.append({
            'name': f'sheet-{index + 1:02d}',
            'source_image': sheet_path.relative_to(root).as_posix(),
            'source_crop': crop,
            'matched_video_frame': int(frame),
            'frame_match_cosine': float(scores[frame]),
            'runner_up_cosine': float(scores[runner_up]),
            'eye_mm': [eye.real, eye.imag, first['eye_mm'][2]],
            **{key: first[key] for key in ('target_mm', 'projection', 'ortho_scale_mm',
                                           'lens_mm', 'sensor_width_mm')},
            'score_interpretation': 'contact sheet diagnostic at matched orbit pose',
        })
    result = {'status': 'direct reference cells with cameras from matching video frames',
              'resolution': [cell_width, cell_height],
              'reference_video_sha256': video_hash,
              'orbit_cameras_sha256': digest(args.cameras),
              'views': views}
    sheet_hash = digest(sheet_path)
    for view in views:
        view['source_sha256'] = sheet_hash
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
