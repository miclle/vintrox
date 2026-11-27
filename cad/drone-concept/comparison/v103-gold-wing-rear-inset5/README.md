# v103 黄翼中段后缘内收 5 mm

v103 采用局部坐标 Y 最大内收 5 mm。相对 v97，视频十方位平均轮廓 IoU 由 85.5731710% 上升至 85.5930336%，静态七图由 82.3587197% 上升至 82.3593108%。video-08 和 still-03 分别下降 0.11656、0.17897 个百分点。

video-07 两个中段后缘样点从 12.04、10.63 px 降至 4.24、4.24 px。整组可见边界 RMS 从 6.57 降至 5.47 px，另一侧边的最大采样距离仍为 14.14 px，占该视角投影屏宽 14.21%。这些手工样点覆盖可见边缘，主要部件的完整 5% 目标仍未证实。

原生 FreeCAD 四视图目视检查通过，696 个可见对象与网格一致，颜色最大通道差 0.001960814。三件生成形体与保存实体的体积对称差为零，折面重新三角化后顶点数量有差异，正式渲染使用保存读回的网格。 [原生检查](native-display/native-display-verification.json) · [局部源代码检查](wing-source-verification.json)

以保存 v97 为基线，按五个站位重建黄翼金属包边、内侧彩色面和后缘折面三件实体。翼根、翼尖、实测平面屏、四支柱、外挂筒、侧控件和格栅保留。三个实体通过高级几何检查和保存读回，七项接合距离无退步，STEP 含 852 个有效闭合实体。[CAD 参数](candidate-check.json) · [独立读回](readback-verification.json)

[视频十方位叠加](video-comparison/comparison-board.png) · [静态七图叠加](stills-comparison/comparison-board.png) · [逐视角结果](candidate-review.json) · [黄翼边界](visible-wing-edges.png) · [边界数据](visible-wing-edges.json)

渲染来自最终 FCStd 读回网格。比较沿用 v97 相机、分割规则和新增四支柱排除范围。参考曲面屏及遮挡区域存在识别限制。整圈 90% 和主要部件完整轮廓 5% 目标仍待达成。

从仓库根目录重放，解压网格字节的 SHA-256 见[网格清单](mesh-archive.json)。

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v103-gold-wing-rear-inset5
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

静态图使用 `stills-comparison/cameras.json` 和独立输出目录。几何复建使用 `tools/experiment_drone_gold_wing_outline.py`，传入 v97 FCStd、该版本的网格和 `--inset 5`，随后用 `tools/finalize_drone_petal_axial.py` 恢复保存 GUI 外观并导出 STEP。
