# v115 天线弯曲路径

从 v107 保存模型出发，只重建后部一件天线。保留底座和 1.1 mm 截面半径，并将天线根部嵌入原底座。路径拟合使用视频第 90、120、150 帧的 27 条上部扫描线，第 0、240 帧的 18 条扫描线用于交叉检查。画面裁掉天线尖端，候选控制点沿用原模型约 385 mm 的尖端高度假设。[拟合输入与结果](fit.json)

| 固定相机平均轮廓 IoU | 视频十方位 | 静态七图 |
| --- | ---: | ---: |
| v107 | 85.708302% | 82.445144% |
| v115，截面半径 1.1 mm | 85.844610% | 82.430215% |
| 同路径，截面半径 2.2 mm | 85.937759% | 82.366372% |

采用 1.1 mm 方案。十个视频方位中九个改善，正后方回落 0.0206 个百分点。静态七图均值下降 0.0149 个百分点，其中 03 回落 0.0643 个百分点。第 0、240 帧的天线可见中心线 RMS 由 7.87、5.06 px 降至 0.96、1.64 px。测量仅覆盖可辨认的上段，真实尖端长度与隐藏部分仍待判定。[v107 扫描线](baseline-antenna-edges.json) · [v115 扫描线](antenna-edges.json)

保存读回确认 696 个可见对象、852 个有效闭合 STEP 实体。天线与底座的交叠体积约 3.80 mm³，变化网格与重开的保存模型一致。FreeCAD 原生四视图通过颜色与可见性复核。实测平面屏、四支柱、外挂筒、侧控件和格栅均保留。曲面罩仍按参考推定，整圈 90% IoU 和主要部件完整轮廓偏差 5% 目标仍待达成。[几何与搭接](candidate-check.json) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

- [v115 视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [参考拼图十格](sheet-comparison/comparison-board.png)
- [2.2 mm 候选视频十方位](radius2p2/video-comparison/comparison-board.png) · [静态七图](radius2p2/stills-comparison/comparison-board.png)

## 复建与复测

随 v119 交付清理了 v115 的模型和中间网格。该轮的相机、对照和测量记录仍可查阅。重放保存的 v115 几何需要另外准备匹配记录哈希的 FCStd 和网格。[当前交付](../v119-barrel-panel/README.md)

以下为历史构建命令，需要另行准备 v107 的 FCStd 和网格。2.2 mm 候选使用独立输出目录和 `--radius 2.2`。构建记录中的脚本哈希对应试验时的版本。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
export PYTHONPATH="$VINTROX_FREECAD/lib"
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
"$VINTROX_FREECAD/bin/python" tools/fit_drone_antenna.py \
  --baseline "$VINTROX_BASE" --output "$VINTROX_RUN/fit.json"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_antenna.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --fit "$VINTROX_RUN/fit.json" --radius 1.1 --output "$VINTROX_RUN/diagnostic"
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```

沿用 v107 的视频和静态相机，渲染最终保存模型的网格。以同组视频相机生成对象 ID，使用 `tools/measure_drone_antenna_edges.py --fit "$VINTROX_RUN/fit.json" --ids <对象ID目录> --output <记录路径>` 复算边缘采样。参考图像使用相机投影和既有分割规则，整机对照排除四支柱及其附件。[相机与渲染流程](../v107-handle-arm-inward-tilt/README.md)
