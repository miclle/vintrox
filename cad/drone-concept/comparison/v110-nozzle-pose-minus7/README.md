# v110 大喷口总成姿态试验

以保存 v107 为基线，将包含外罩、叶片、导轨、铰座、标识和低音预留在内的 143 个形体，绕通过喷口根部 (0, 180, 173) mm 的 X 轴同转 −7°。角度由三个固定相机下的历史末端观测预筛后取整。后壳、凹舱、实测平面屏、四根支柱、外挂筒、侧控件和格栅沿用 v107。原有 11 组壳体搭接仍有正体积，外罩与后接口承接面的搭接由 1594.3 降至 11.9 mm³。高级几何检查错误列表保持一致。[几何与搭接检查](candidate-check.json)

| 固定相机平均轮廓 IoU | v107 | v110 |
| --- | ---: | ---: |
| 视频十方位 | 85.708302% | 85.666838% |
| 静态七图 | 82.445144% | 82.421012% |

末端折边的七视角采样 RMS 由 21.53 降至 19.59 px，包含遮挡面上的边线。用对象 ID 比较实际可见的叶片家族边界，七个视角中五个 RMS 下降，video-03 和 video-05 上升，最大采样偏差仍为该视角投影屏宽的 22.81%。固定视频的两个侧视 IoU 分别下降 0.16 和 0.20 个百分点。保留 v110 为候选，当前外观入口采用 v107。[可见边界](visible-petal-edges.png) · [视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png)

FCStd 独立读回确认 696 个可见对象、852 个有效闭合 STEP 实体，142 件变更可见件重新三角化与保存网格一致，低音预留是隐藏形体。FreeCAD 原生四视图核对颜色和可见性，关闭后文件哈希一致。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从仓库根目录运行以下命令。以最终目录的网格和 FCStd 使用 [v107 固定相机流程](../v107-handle-arm-inward-tilt/README.md) 重建两套渲染与叠加。使用同一相机配置运行对象 ID 渲染器，可重放叶片可见边界比较。整圈 90% 和主要部件完整轮廓 5% 目标仍待达成。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
export PYTHONPATH="$VINTROX_FREECAD/lib"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_nozzle_pose.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --output "$VINTROX_RUN/diagnostic" --angle -7
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```
