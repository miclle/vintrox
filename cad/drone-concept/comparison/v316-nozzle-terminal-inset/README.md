# v316 大喷口镜像叶片末段内收

从 v315 保存几何出发，分别调整第 0、4 号及第 5、11 号镜像叶片。固定喷口局部 Z=109.5 mm 接续面，末段轴向放大至 1.65 倍，每 17 mm 原跨度径向内移 3 mm、局部 Y 方向偏移 2 mm。每档复查 10 件修改形体，保存实体及接合检查无新增失败，13 件支撑总成的形体差集为零。[第 0、4 号几何](pair-0-4/candidate-check.json) · [第 5、11 号几何](pair-5-11/candidate-check.json)

| 固定相机或局部测量 | v315 | 第 0、4 号 | 第 5、11 号 |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 86.204590% | 86.197985% | 86.200972% |
| 静态七图平均 IoU | 82.687714% | 82.685193% | 82.683880% |
| 拼图十格平均 IoU | 89.958234% | 89.957573% | 89.960347% |
| 第 60 帧末缘最大偏差 | 20.96% | 20.64% | 18.94% |
| 第 180 帧末缘最大偏差 | 21.94% | 20.68% | 20.68% |

偏差按各视角中的投影屏宽归一化。第 5、11 号方案将第 60、180 帧采样 RMS 从 25.13、25.98 px 降至 23.45、24.15 px。两档视频和静态均值均下降，正式模型采用 v315。测量覆盖已标注的叶片可见边缘，含遮挡边。候选验核覆盖保存几何、接合与固定相机渲染。[第 5、11 号逐点测量](pair-5-11/visible-petal-edges.json) · [视频](pair-5-11/video-board.png) · [静态图](pair-5-11/stills-board.png) · [拼图](pair-5-11/sheet-board.png)

以 v315 的 FCStd 和重建网格运行 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --station 109.5 --factor 1.65 --tip-radial-shift -3 --tip-centre-shift 2` 和空输出目录。两档分别使用 `--leaf-indices 0 4` 与 `--leaf-indices 5 11`。沿用 v315 的三组相机渲染，使用相同的视频相机生成基线与候选对象 ID，运行 `tools/compare_drone_visible_petal_edges.py` 复测。[v315 模型与相机](../v315-antenna-multiview/README.md) · [视频参考标注](../v307-nozzle-pair-6-10/video-observations.json)
