# v281 大喷口镜像叶片末段延长

在 v276 的固定相机下复查 53 个既有叶片末端采样点。视频第 02 和 06 方位的 10 条射线均落在空处，参考裁图中多条末段实体边可见。第 03 方位有两个点先击中叶片、一个先击中小喷口，其余三个落空。射线给出遮挡关系，单个像素的三维对应仍有歧义。[参考和 CAD 近景](v276-tip-crops.png) · [v276 射线记录](v276-petal-occlusion.json)

选择第 0、4、5、11 号镜像叶片的末段及附属件，以局部 Z 109.5 mm 为接续面，将末段轴向伸至 1.75 倍，并按每 17 mm 原跨度沿径向内移 2 mm。20 件改动通过保存读回，76 项接合无退步，13 件支撑总成差集为零。[保存几何与参数](candidate-check.json)

| 固定相机对照 | v276 | v281 |
| --- | ---: | ---: |
| 视频十方位平均 IoU | 86.019486% | 86.007356% |
| 静态七图平均 IoU | 82.574760% | 82.567404% |
| 拼图十格平均 IoU | 89.777430% | 89.788746% |
| 视频 02 末端最大偏差／投影屏宽 | 20.96% | 17.63% |
| 视频 06 末端最大偏差／投影屏宽 | 21.94% | 20.68% |

七个采样视角中有六个 RMS 下降，视频 05 上升。视频 02 和 06 的 10 条射线仍全部落空，同两个视角的整机 IoU 分别下降 0.06016 和 0.06526 个百分点。继续采用 v276。v281 的验证覆盖 FCStd 保存实体和固定相机筛选，候选 STEP 与原生显示尚未复查。[局部对照](visible-petal-edges.png) · [采样报告](visible-petal-edges.json) · [v281 射线记录](petal-occlusion.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

用 v276 保存 FCStd 和重建网格运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 1.75 --tip-radial-shift -2 --leaf-indices 0 4 5 11`。沿用 v276 的三组固定相机，以及 v257 的参考标注。对候选与基线分别运行 `tools/diagnose_drone_petal_occlusion.py` 和 `tools/render_drone_object_ids.py`，再用 `tools/compare_drone_visible_petal_edges.py` 比较已标注点到可见叶片族边界的距离。[v276 相机与网格](../v276-front-cheek-x099/README.md) · [v257 标注](../v257-mirrored-nozzle-tips/visible-petal-edges.json) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
