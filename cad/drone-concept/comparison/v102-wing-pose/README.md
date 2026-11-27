# v102 两侧翼板姿态试验

以保存 v97 为基线，围绕各侧原有轴座中心旋转两组共 18 件翼板对象。全局 X 旋转为 +0.02298°，左右 Y 旋转分别为 −1.75775°、+1.75775°。两侧轴座连接的四项距离检查均无退步。保存读回确认 852 个有效闭合 STEP 实体与 696 个可见对象，18 件变更网格逐顶点和面一致。实测平面屏、四支柱、外挂筒、侧控件和格栅保留。原生 FreeCAD 四视图颜色、可见性及关闭后哈希检查通过。[拟合参数](pose-fit.json) · [接合记录](candidate-check.json) · [独立读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

| 固定相机对比 | v97 | v102 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 85.5731710% | 85.4783666% | −0.0948044 |
| 静态七图平均 IoU | 82.3587197% | 82.4567958% | +0.0980762 |

视频均值回落，v102 保留为未采用候选。红翼侧视的最大采样偏差从投影屏宽的 4.69% 降至 3.60%，黄翼侧视则从 14.21% 升至 15.07%。两组全翼样点用于拟合，另外两组仅覆盖翼根，完整部件的 5% 目标仍未验证。图像中的曲面屏与保存平面屏存在差异，隐藏部位依然缺少可观测轮廓。[十方位叠加](video-comparison/comparison-board.png) · [七图叠加](stills-comparison/comparison-board.png) · [逐视角数据](candidate-review.json) · [翼板可见边界](visible-wing-edges.png) · [采样记录](visible-wing-edges.json)

从仓库根目录重放视频对照。解压后的网格与原生显示检查使用同一 SHA-256。[网格清单](mesh-archive.json)

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v102-wing-pose
VINTROX_REPLAY=$(mktemp -d)
gzip -dc "$VINTROX_PACKAGE/meshes.json.gz" > "$VINTROX_REPLAY/meshes.json"
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
  --model "$VINTROX_PACKAGE/candidate.FCStd" --output "$VINTROX_REPLAY/video-renders" \
  --comparison "$VINTROX_PACKAGE/video-comparison/cameras.json"
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
  --renders "$VINTROX_REPLAY/video-renders" --output "$VINTROX_REPLAY/video-comparison" \
  --cameras "$VINTROX_PACKAGE/video-comparison/cameras.json"
```

静态图使用 `stills-comparison/cameras.json` 和单独的输出目录。重算翼板采样时使用归档的对象 ID 渲染。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v97-petal096-brow0985-on-v96
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_visible_wing_edges.py \
  --baseline "$VINTROX_BASE" --mesh "$VINTROX_BASE/meshes.json" \
  --candidate "$VINTROX_PACKAGE" --fit "$VINTROX_PACKAGE/pose-fit.json"
```
