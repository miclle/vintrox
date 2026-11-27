# v173 前脸颊桥收缩候选

以 v164 为基线，将两侧前脸颊及桥板横向缩至 99.5%。视频十方位 85.9009%，静态七图 82.5251%，拼图十格 89.6544%。以相同相机和遮罩从 v164 重建并复跑 27 个视角，三组均值分别提高 0.003618、0.002222 和 0.003343 个百分点。拼图第 02 格单独下降 0.001188 个百分点。采用 v173。[候选数据](candidate-results.json)

保存读回确认 696 个可见对象、853 个闭合 STEP 实体，两侧桥板与侧脊间隙均为 0 mm。四根支柱的实体对称差为 0 mm³，保留 210 × 160 × 2 mm 实测平面屏、外挂筒、侧控件和格栅。FreeCAD 原生四视图颜色和可见性通过。[保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从保存的 FCStd 重建 696 件网格后，27 个固定视角的逐视角轮廓指标与试验网格一致。整圈 90% 和主要部件完整轮廓偏差 5% 仍待达成。曲面罩为外观假设，遮挡结构缺少独立观测。[视频十方位](video-comparison/comparison-board.png) · [独立静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png) · [网格重建记录](mesh-archive.json)

从仓库根目录重建并重放视频视角。静态七图和拼图分别使用本目录内的 `stills-comparison/cameras.json` 和 `sheet-comparison/cameras.json`，并写入单独的输出目录。

```sh
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
VINTROX_REPLAY=$(mktemp -d)
VINTROX_PACKAGE=cad/drone-concept/comparison/v173-front-cheek-contract
PYTHONPATH="$VINTROX_FREECAD/lib" "$VINTROX_FREECAD/bin/python" \
  tools/export_saved_drone_meshes.py --output "$VINTROX_REPLAY/meshes.json"
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
  --model "$VINTROX_PACKAGE/candidate.FCStd" --output "$VINTROX_REPLAY/video-renders" \
  --comparison "$VINTROX_PACKAGE/video-comparison/cameras.json"
PYTHONPATH="$VINTROX_FREECAD/lib" "$VINTROX_FREECAD/bin/python" \
  tools/compare_drone_reference.py --renders "$VINTROX_REPLAY/video-renders" \
  --output "$VINTROX_REPLAY/video-comparison" --cameras "$VINTROX_PACKAGE/video-comparison/cameras.json"
```


当前 v173 的视频十方位可见轮廓归因已归档。[外部多余区域归因](boundary-regions.json) · [诊断板](boundary-regions-board.png)。该诊断只按现有遮罩区分外部多余像素和封闭暗区，不改变 IoU，也不证明应删除或缩短对应零件。外部多余像素优先集中在喷口叶片、下部喷口肋、前罩底缘、屏框和回环，下一轮按跨视角可见实体核对。
