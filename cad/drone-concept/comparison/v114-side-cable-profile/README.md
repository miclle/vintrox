# v114 红翼侧外挂筒卷线

从保存 v107 出发，只替换红翼侧外挂筒的一件卷线实体。对比两档线材截面半径，以及保留 1.8 mm 截面半径、将下部圈径的控制值乘以 0.85 的候选。三组使用同一套十方位视频和七张静态参考相机，并保留四根支柱、实测平面屏、外挂筒、侧控件和格栅。[线径近景](tube-radius-comparison.png) · [基线卷线读回](baseline-cable-check.json)

| 卷线参数 | 视频十方位平均 IoU | 静态七图平均 IoU |
| --- | ---: | ---: |
| v107，截面半径 1.8 mm | 85.7083020% | 82.4451438% |
| 截面半径 1.5 mm | 85.7138806% | 82.4574028% |
| 截面半径 2.1 mm | 85.7036159% | 82.4293875% |
| 截面半径 1.8 mm，下部圈径控制值缩小 15% | 85.7139468% | 82.4491980% |

1.5 mm 候选的视频和静态均值分别提高 0.00558 和 0.01226 个百分点，正后视下降约 0.0122 个百分点。改线径时两组中心线采样距离在数值精度内一致。收小下部圈径后，历史拟合点的中心线 RMS 从 4.20 升至 4.48 px，第三视角从 5.23 升至 5.38 px。局部近景仍可见下部圈形和外挂筒端头之间的差异。当前采用 v107。中心线距离仅覆盖部分可见段，主要部件完整轮廓 5% 和整圈 90% IoU 目标仍待达成。

三组均确认卷线是单一有效闭合实体，与两端护套有正体积交叠，13 组支撑交叠检查无退步。独立读回确认 696 个可见对象、852 个有效闭合 STEP 实体、变更件与网格一致，原生 FreeCAD 四视图颜色和可见性通过。曲面罩和隐藏结构仍按参考推定。

- [1.5 mm FCStd](tube-radius1p5/candidate.FCStd) · [STEP](tube-radius1p5/candidate.step) · [视频十方位](tube-radius1p5/video-comparison/comparison-board.png) · [静态七图](tube-radius1p5/stills-comparison/comparison-board.png)
- [2.1 mm FCStd](tube-radius2p1/candidate.FCStd) · [STEP](tube-radius2p1/candidate.step) · [视频十方位](tube-radius2p1/video-comparison/comparison-board.png) · [静态七图](tube-radius2p1/stills-comparison/comparison-board.png)
- [下部圈径 FCStd](lower-coil85/candidate.FCStd) · [STEP](lower-coil85/candidate.step) · [卷线读回](lower-coil85/side-cable-check.json) · [视频十方位](lower-coil85/video-comparison/comparison-board.png) · [静态七图](lower-coil85/stills-comparison/comparison-board.png)

## 复建

从仓库根目录运行下列命令。2.1 mm 候选使用 `--radius 2.1`。下部圈径候选使用 `--radius 1.8 --lower-coil-scale .85`。两份线径候选的构建记录保存了添加圈径参数之前的脚本哈希。默认圈径系数为 1。以最终 FCStd 和网格重放 v107 的两套固定相机，使用 `tools/measure_drone_side_cable.py` 复算扫掠截面和端头交叠。[固定相机与渲染命令](../v107-handle-arm-inward-tilt/README.md)

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
export PYTHONPATH="$VINTROX_FREECAD/lib"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_side_cable_radius.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --radius 1.5 --output "$VINTROX_RUN/diagnostic"
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```
