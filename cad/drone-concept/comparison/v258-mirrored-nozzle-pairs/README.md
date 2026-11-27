# v258 大喷口端部镜像对照

从 v257 保存模型出发，沿用原相机，调整第 0、4、5、11 号叶片的端部及其附属件。对象 ID 对照将两处最远采样分别定位到第 5 号末端折边和第 0 号叶片附近。20 件改动通过保存读回，76 项接合检查无退步，13 件支撑实体差集为零。[几何检查](candidate-check.json)

| 固定相机 | v257 | v258 |
| --- | ---: | ---: |
| 视频十方位平均 IoU | 85.932372% | 85.928370% |
| 静态七图平均 IoU | 82.550767% | 82.546536% |
| 拼图十格平均 IoU | 89.682051% | 89.686000% |
| 视频第 02 视角末端最大偏差／投影屏宽 | 20.96% | 19.36% |
| 视频第 06 视角末端最大偏差／投影屏宽 | 21.94% | 20.89% |

两处侧后视端部偏差下降，整机轮廓的 IoU 分别下降 0.01904、0.03164 个百分点。静态均值退步集中在 `still-05`，该视角下降 0.02962 个百分点。正式交付继续采用 v257。v258 的独立 STEP 与原生显示检查待开展。[叶片采样](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

使用 v257 的保存 FCStd 和网格运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 1.28 --tip-radial-shift 2.5 --tip-centre-shift 1.5 --leaf-indices 0 4 5 11`。用 v257 的三组相机重放固定视角，沿用同一批参考标注和对象 ID 测量。[基线与相机](../v257-mirrored-nozzle-tips/README.md)
