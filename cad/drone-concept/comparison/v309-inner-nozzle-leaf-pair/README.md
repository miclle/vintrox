# v309 大喷口第 1、3 号叶片末段

从 v306 的保存 CAD 延长第 1、3 号镜像叶片，复核 6 件改动形体及 13 件支撑几何。保存模型的实体和接合检查均无新增失败。[保存几何](candidate-check.json)

| 固定相机 | v306 | v309 |
| --- | ---: | ---: |
| 视频十方位 | 86.181044% | 86.180207% |
| 静态七图 | 82.638371% | 82.638050% |
| 拼图十格 | 89.902265% | 89.901394% |

视频第 90 帧的末缘最大偏差由投影屏宽的 8.85% 降至 8.42%。第 60、180 帧的最大偏差仍为 20.96% 和 21.94%。三组整机均值略降，正式采用 v306。[局部边缘](visible-petal-edges.png) · [视频](video-board.png) · [静态图](stills-board.png) · [拼图](sheet-board.png)

沿用 [v307 的重放流程](../v307-nozzle-pair-6-10/README.md)和 v306 保存模型。运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 1.65 --tip-radial-shift 2 --leaf-indices 1 3`，使用同一套相机和末缘标注对照保存几何。
