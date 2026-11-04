"""Summarize unchanged-camera loop comparisons and create common crop boards."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    args = parser.parse_args()
    candidate, baseline = args.candidate, args.baseline
    model_hash = digest(candidate/'candidate.FCStd')
    baseline_hash = digest(baseline/'candidate.FCStd')
    comparisons = {}
    for family in ['video', 'stills']:
        paths = [p/(family+'-comparison')/'comparison-report.json' for p in [baseline, candidate]]
        previous, current = [json.loads(p.read_text()) for p in paths]
        assert current['fcstd_sha256'] == model_hash
        assert previous['fcstd_sha256'] == baseline_hash
        for key in ['camera_config_sha256', 'comparison_script_sha256', 'mask_method', 'excluded_from_cad']:
            assert current[key] == previous[key], key
        assert [r['view'] for r in previous['views']] == [r['view'] for r in current['views']]
        rows = [{'view': c['view'], 'baseline_iou': b['silhouette_iou'],
                 'candidate_iou': c['silhouette_iou'],
                 'delta_iou': c['silhouette_iou']-b['silhouette_iou']}
                for b, c in zip(previous['views'], current['views'])]
        comparisons[family] = {'baseline_report_sha256': digest(paths[0]),
                               'candidate_report_sha256': digest(paths[1]),
                               'baseline_mean_iou': previous['mean_silhouette_iou'],
                               'candidate_mean_iou': current['mean_silhouette_iou'],
                               'delta_mean_iou': current['mean_silhouette_iou']-previous['mean_silhouette_iou'],
                               'views': rows}
    board = Image.new('RGB', (1500, 750), (20, 20, 20))
    draw = ImageDraw.Draw(board)
    for i, frame in enumerate([60, 120, 180]):
        view = f'video-{frame//30:02d}'
        sources = [candidate/'video-comparison/reference-frames'/f'frame-{frame//30+1:02d}.png',
                   baseline/'video-renders'/(view+'.png'), candidate/'video-renders'/(view+'.png')]
        for j, (path, label) in enumerate(zip(sources, ['SOURCE', 'V69', 'V79'])):
            im = Image.open(path).convert('RGBA')
            black = Image.new('RGBA', im.size, (0, 0, 0, 255))
            black.alpha_composite(im)
            crop = black.convert('RGB').crop((200, 550, 750, 760))
            crop.thumbnail((490, 210))
            board.paste(crop, (j*500, i*250+30))
            draw.text((j*500+5, i*250+5), f'{label} frame {frame}', fill='white')
    board.save(candidate/'loop-closeup.png')
    board = Image.new('RGB', (1400, 1100))
    for i, view in enumerate(['isometric', 'front', 'rear', 'right']):
        im = Image.open(candidate/'native-display'/f'v79-{view}.png')
        im.thumbnail((700, 550))
        board.paste(im, ((i%2)*700, (i//2)*550))
    board.save(candidate/'native-display/native-board.png')
    report = {'fcstd_sha256': model_hash, 'baseline_fcstd_sha256': baseline_hash,
              'script_sha256': digest(Path(__file__)), 'comparisons': comparisons,
              'image_alignment': 'original fixed cameras; identical rectangular crops; no image warp',
              'adoption': 'not adopted: video mean regresses despite static improvement',
              'limitations': ['crop board is illustrative; original full-view metrics remain authoritative',
                             'manual centreline observations do not prove full-part contour accuracy',
                             'formal v61 and preferred exterior study v69 remain unchanged',
                             '90 percent IoU and complete major-part 5 percent targets remain incomplete']}
    (candidate/'candidate-review.json').write_text(json.dumps(report, indent=2)+'\n')
    print([(f, r['candidate_mean_iou'], r['delta_mean_iou']) for f, r in comparisons.items()])


if __name__ == '__main__':
    main()
