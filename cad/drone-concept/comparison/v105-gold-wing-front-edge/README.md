# v105 黄翼前缘试件

保存 v103 的黄翼后缘内收 5 mm。在局部 Y 方向调整前缘第 1 至 4 站，偏移为 `.5 5.5 .7 8` mm，重建金属包边、内侧彩色面、折面、抬高面和外侧彩色面。实测平面屏、四根支柱、外挂筒、侧控件和格栅保留。五件实体通过高级检查，九项接合距离无退步。独立读回确认 852 个闭合 STEP 实体、五件变化网格一致，原生 FreeCAD 显示 696 个对象，RGB 最大通道差 0.001961。[形体检查](candidate-check.json) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

视频十方位和静态七图平均 IoU 为 85.6129150% 和 82.3656891%。视频 07 上段样点从 14.14 px 降至 5.83 px，但下段样点从 1.41 px 升至 15.00 px，最大偏差为投影屏宽的 15.07%。保留本试件供对照，正式入口采用 v106。 [逐视角结果](candidate-review.json) · [黄翼采样](visible-wing-edges.json) · [边缘叠加](visible-wing-edges.png)

比较沿用 v103 固定相机和分割规则，并保留全部十视频、七静态图结果。四根新增支柱及其附属件只在参考比较中排除。人工样点覆盖部分可见边缘，参考曲面屏和保存平面屏之间仍有差异，遮挡部位缺少独立观测。完整主要部件 5% 和整圈 90% 仍未达成。[十视频叠加](video-comparison/comparison-board.png) · [七静态图叠加](stills-comparison/comparison-board.png)

从仓库根目录重放。网格解压后的 SHA-256 见[归档清单](mesh-archive.json)。

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v105-gold-wing-front-edge
VINTROX_REPLAY=$(mktemp -d)
gzip -dc "$VINTROX_PACKAGE/meshes.json.gz" > "$VINTROX_REPLAY/meshes.json"
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
  --model "$VINTROX_PACKAGE/candidate.FCStd" --output "$VINTROX_REPLAY/video-renders" \
  --comparison "$VINTROX_PACKAGE/video-comparison/cameras.json"
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
  --renders "$VINTROX_REPLAY/video-renders" --output "$VINTROX_REPLAY/video-comparison" \
  --cameras "$VINTROX_PACKAGE/video-comparison/cameras.json"
```

静态图使用 `stills-comparison/cameras.json` 和单独的输出目录。复建几何时将 v103 的保存 FCStd 及解压网格传入 `tools/experiment_drone_gold_wing_outline.py`，参数为 `--inset 5 --front-offsets .5 5.5 .7 8`，然后用 `tools/finalize_drone_petal_axial.py` 恢复保存颜色并从最终 FCStd 导出 STEP。
