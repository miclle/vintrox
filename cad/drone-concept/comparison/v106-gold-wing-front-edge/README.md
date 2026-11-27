# v106 黄翼前缘试件

保存 v103 的黄翼后缘内收 5 mm。在局部 Y 方向调整前缘第 1 至 4 站，偏移为 `.5 5.5 2.5 2` mm，重建金属包边、内侧彩色面、折面、抬高面和外侧彩色面。实测平面屏、四根支柱、外挂筒、侧控件和格栅保留。五件实体通过高级检查，九项接合距离无退步。独立读回确认 852 个闭合 STEP 实体、五件变化网格一致，原生 FreeCAD 显示 696 个对象，RGB 最大通道差 0.001961。[形体检查](candidate-check.json) · [读回](readback-verification.json) · [局部源代码检查](wing-source-verification.json) · [原生显示](native-display/native-display-verification.json)

视频十方位和静态七图平均 IoU 为 85.5948200% 和 82.3655109%。相对 v103 分别增加 0.001786 和 0.006200 个百分点。视频 07 的采样 RMS 从 5.47 降至 4.41 px，最大偏差从屏幕投影宽度的 14.21% 降至 8.10%。视频 01 和静态图 06 分别回落 0.090416 和 0.088397 个百分点。采用本试件改善黄翼前缘的最大采样偏差。 [逐视角结果](candidate-review.json) · [黄翼采样](visible-wing-edges.json) · [边缘叠加](visible-wing-edges.png)

视频 08 的九个前缘样点在构建候选前记录，并排除于站位拟合。相对 v103，RMS 从 4.71 降至 2.45 px，最大偏差从 6.32 降至 4.12 px，占该视角投影屏宽的 1.14%。[观察点](video08-front-observations.json) · [测量](video08-front-measurement.json) · [叠加](video08-front-overlay.png)

比较沿用 v103 固定相机和分割规则，并保留全部十视频、七静态图结果。四根新增支柱及其附属件只在参考比较中排除。人工样点覆盖部分可见边缘，参考曲面屏和保存平面屏之间仍有差异，遮挡部位缺少独立观测。完整主要部件 5% 和整圈 90% 仍未达成。[十视频叠加](video-comparison/comparison-board.png) · [七静态图叠加](stills-comparison/comparison-board.png)

从仓库根目录重放。网格解压后的 SHA-256 见[归档清单](mesh-archive.json)。

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v106-gold-wing-front-edge
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

静态图使用 `stills-comparison/cameras.json` 和单独的输出目录。复建几何时将 v103 的保存 FCStd 及解压网格传入 `tools/experiment_drone_gold_wing_outline.py`，参数为 `--inset 5 --front-offsets .5 5.5 2.5 2`，然后用 `tools/finalize_drone_petal_axial.py` 恢复保存颜色并从最终 FCStd 导出 STEP。
