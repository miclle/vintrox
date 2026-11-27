# v323–v324 大喷口末段改动范围

从 v315 保存模型出发，在局部 Z=109.5 mm 之后将末段轴向放大至 1.5 倍。每 17 mm 的原跨度径向外移 2.5 mm、局部 Y 方向移动 4 mm。v323 调整第 5 至 11 号叶片的 38 件形体，v324 仅对位于对称中心的第 8 号叶片及其细节共 6 件形体应用同一参数。两档保存几何、接合和 13 件支撑几何保护检查均通过。[v323 几何](v323/candidate-check.json) · [v324 几何](v324/candidate-check.json)

| 固定相机 | v315 | v323 | v324 |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 86.204590% | 86.138574% | 86.210847% |
| 静态七图平均 IoU | 82.687714% | — | 82.686413% |
| 拼图十格平均 IoU | 89.958234% | — | 89.967402% |

v323 让第 120 帧的局部末缘 RMS 从 22.93 降至 16.41 px，但视频十方位均值下降，试验止于视频组。v324 在视频和拼图上小幅提升，静态第 05 图下降 0.00911 个百分点，视频第 150 帧末缘 RMS 由 8.91 增至 9.59 px。第 60 和 180 帧的局部最大偏差仍是投影屏宽的 20.96% 和 21.94%。正式评审沿用 v315。[v323 视频](v323/video-comparison/comparison-board.png) · [v324 视频](v324/video-comparison/comparison-board.png) · [静态](v324/stills-comparison/comparison-board.png) · [拼图](v324/sheet-comparison/comparison-board.png) · [局部测量](v324/visible-petal-edges.json)

v324 的独立读回确认 696 个可见对象、853 个闭合 STEP 实体及不变的四支柱几何。FreeCAD 原生四视图核对了 70 组颜色和可见对象。[读回](v324/readback.json) · [原生显示](v324/native-display/native-display-verification.json)

复现时从 [v315 FCStd 和固定相机](../v315-antenna-multiview/README.md) 重建临时网格。在 FreeCAD Python 中运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 1.5 --tip-radial-shift 2.5 --tip-centre-shift 4`。v323 附加 `--leaf-indices 5 6 7 8 9 10 11`，v324 附加 `--leaf-indices 8`。使用 `tools/finalize_drone_petal_axial.py` 打包后，沿 v315 相机和 [v307 标注](../v307-nozzle-pair-6-10/video-observations.json) 复测。候选 FCStd、STEP 和网格可再生成。
