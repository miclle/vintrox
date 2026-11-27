# v104 黄翼中段后缘内收 2.5 mm

v104 测试局部坐标 Y 最大内收 2.5 mm。视频十方位平均轮廓 IoU 为 85.5897114%，静态七图为 82.3593684%。video-08 和 still-03 分别下降 0.04477、0.09169 个百分点。video-07 两个中段后缘样点下降至 7.81、7.62 px，整组 RMS 从 6.57 降至 5.92 px。采用 5 mm 档以改善该段边缘。 [v103 记录](../v103-gold-wing-rear-inset5/README.md)

以保存 v97 为基线，按五个站位重建黄翼金属包边、内侧彩色面和后缘折面三件实体。翼根、翼尖、实测平面屏、四支柱、外挂筒、侧控件和格栅保留。三个实体通过高级几何检查和保存读回，七项接合距离无退步，STEP 含 852 个有效闭合实体。[CAD 参数](candidate-check.json) · [独立读回](readback-verification.json)

[视频十方位叠加](video-comparison/comparison-board.png) · [静态七图叠加](stills-comparison/comparison-board.png) · [逐视角结果](candidate-review.json) · [黄翼边界](visible-wing-edges.png) · [边界数据](visible-wing-edges.json)

渲染来自最终 FCStd 读回网格。比较沿用 v97 相机、分割规则和新增四支柱排除范围。参考曲面屏及遮挡区域存在识别限制。整圈 90% 和主要部件完整轮廓 5% 目标仍待达成。

从仓库根目录重放，解压网格字节的 SHA-256 见[网格清单](mesh-archive.json)。

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v104-gold-wing-rear-inset2p5
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

静态图使用 `stills-comparison/cameras.json` 和独立输出目录。几何复建使用 `tools/experiment_drone_gold_wing_outline.py`，传入 v97 FCStd、该版本的网格和 `--inset 2.5`，随后用 `tools/finalize_drone_petal_axial.py` 恢复保存 GUI 外观并导出 STEP。
