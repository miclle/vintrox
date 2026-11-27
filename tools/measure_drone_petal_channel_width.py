"""Compare visible guide separation with the existing rear-view observations.

Reference marks are manually observed bright rail positions with about two pixels
of uncertainty; they do not uniquely identify a rail centre versus its bright edge.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from measure_drone_petal_pitch import PAIRS, ROW


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    for name in ['ids','renders','comparison','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    metadata_path = args.ids/'object-id-manifest.json'
    metadata = json.loads(metadata_path.read_text())
    render_metadata_path = args.renders/'render-manifest.json'
    render_metadata = json.loads(render_metadata_path.read_text())
    comparison = json.loads((args.comparison/'comparison-report.json').read_text())
    assert metadata['fcstd_sha256']==render_metadata['fcstd_sha256']==comparison['fcstd_sha256']
    assert metadata['camera_config_sha256']==render_metadata['camera_config_sha256']==comparison['camera_config_sha256']
    id_path = args.ids/'video-04.png'
    pixels = np.asarray(Image.open(id_path).convert('RGB'))
    objects = {item['name']:item['rgb'] for item in metadata['objects']}
    records = []
    for index, reference in zip([9,8,7],PAIRS):
        rail_centres, rail_ranges = [], []
        whole = np.zeros(pixels.shape[1],bool)
        for name in [f'NozzlePetalRidge{index}',f'NozzlePetalGuide{index}_0',f'NozzlePetalGuide{index}_1']:
            mask = np.all(pixels[ROW]==objects[name],axis=1)
            whole |= mask
            if 'Guide' in name:
                columns = np.flatnonzero(mask)
                rail_ranges.append([int(columns.min()),int(columns.max())] if len(columns) else None)
                rail_centres.append(float((columns.min()+columns.max())/2) if len(columns) else None)
        columns = np.flatnonzero(whole)
        both_visible = all(x is not None for x in rail_centres)
        separation = abs(rail_centres[1]-rail_centres[0]) if both_visible else None
        records.append({'petal_index':index,'reference_positions_px':reference,
                        'reference_separation_px':reference[1]-reference[0],
                        'rail_ranges_px':rail_ranges,'rail_centres_px':rail_centres,
                        'both_rails_visible':both_visible,'centre_separation_px':separation,
                        'separation_error_px':separation-(reference[1]-reference[0]) if both_visible else None,
                        'whole_assembly_range_px':[int(columns.min()),int(columns.max())],
                        'whole_assembly_span_px':int(columns.max()-columns.min())})
    source = args.comparison/'reference-frames/frame-05.png'
    render = args.renders/'video-04.png'
    crop=(360,535,585,650)
    scale=3
    width,height=(crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale
    board=Image.new('RGB',(width*2,height+45),(15,18,20))
    draw=ImageDraw.Draw(board)
    font=ImageFont.load_default(size=16)
    for column,path in enumerate([source,render]):
        board.paste(Image.open(path).convert('RGB').crop(crop).resize((width,height),Image.Resampling.NEAREST),(column*width,45))
        draw.text((column*width+8,10),'REFERENCE BRIGHT RAIL POSITIONS' if column==0 else 'CAD VISIBLE GUIDE CENTRES',fill='white',font=font)
        for record in records:
            values=record['reference_positions_px'] if column==0 else record['rail_centres_px']
            for x in values:
                if x is None:continue
                u=column*width+(x-crop[0])*scale
                v=45+(ROW-crop[1])*scale
                draw.line((u,v-12,u,v+12),fill=(0,240,255),width=2)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    png=args.output.with_suffix('.png')
    board.save(png)
    errors=[r['separation_error_px'] for r in records if r['both_rails_visible']]
    result={'fcstd_sha256':metadata['fcstd_sha256'],'camera_config_sha256':metadata['camera_config_sha256'],
            'measurement_script_sha256':digest(Path(__file__)),
            'object_id_manifest_sha256':digest(metadata_path),'render_manifest_sha256':digest(render_metadata_path),
            'source_frame':120,'row_px':ROW,'manual_uncertainty_px':2,
            'observations':records,'measured_pairs_count':len(errors),
            'rms_separation_error_px':float(np.sqrt(np.mean(np.array(errors)**2))) if errors else None,
            'image_path':str(png),'image_sha256':digest(png),
            'source_files':[{'path':str(p),'sha256':digest(p)} for p in [source,render,id_path]],
            'limitations':['three central guide pairs only','reference bright positions may be edges rather than rail centres',
                            'object-ID visibility is approximate at antialiased pixels','not a complete nozzle acceptance test']}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'rms_separation_error_px':result['rms_separation_error_px'],'observations':records}))


if __name__=='__main__':
    main()
