# v289 底部小喷口叶片轴向延长

在 v287 保存的两个小喷口局部坐标中，以 Z=30 mm 为基准将叶片、压条和脊条的轴向跨度放大 6%。两片封片沿同一轴向调整，用解析锥台恢复保存实体，两端半径各增 0.015 mm 以维持叶片与封片的接合。共 146 件保存形体通过有效性、闭合性和高级几何复核，216 项距离检查通过。已有间隙采用 0.001 mm 的数值容差，接触对采用 0.01 mm 门槛。FCStd 中其余成员与 v287 逐字节一致。[保存几何与接合](candidate-check.json)

| 测量 | v287 | v289 |
| --- | ---: | ---: |
| 叶片外端圆弧，原拟合四视角 RMS | 4.53 px | 4.74 px |
| 叶片外端圆弧，原拟合外两视角 RMS | 7.38 px | 6.28 px |
| 叶片外端圆弧，原拟合外两视角最大偏差 | 12.62 px | 10.86 px |
| 视频十方位平均 IoU | 86.033198% | 86.001886% |
| 静态七图平均 IoU | 82.574760% | 82.533374% |
| 拼图十格平均 IoU | 89.782809% | 89.761067% |

端缘测量覆盖既有人工标注到保存叶片外端圆弧的距离。正式版采用 v287。v289 检查范围为保存 FCStd 和三组固定相机，候选 STEP 及原生窗口显示尚待验证。[参考与 v287 端缘近景](pod-closeups.png) · [v287 样点](base-outline.json) · [v289 样点](outline.json)

初次延长使四对原接触的叶片与封片分离约 0.11–0.12 mm。随后对封片直接做非均匀变换，产生两处高级几何检查失败。最终试件采用解析锥台，两轮失败记录保留。[试验失败记录](failed-geometry-checks.json)

从 v287 保存模型重建网格，在 FreeCAD Python 环境下运行 `PYTHONPATH="$VINTROX_FREECAD/lib:$PWD/tools" "$VINTROX_FREECAD/bin/python" cad/drone-concept/comparison/v289-small-pod-axial-extension/replay.py --base <v287 FCStd> --mesh <v287 网格> --output <新目录> --axial-scale 1.06`。用 `tools/measure_drone_lower_pod_outline.py` 复测，三组渲染沿用 v287 固定相机。[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)
