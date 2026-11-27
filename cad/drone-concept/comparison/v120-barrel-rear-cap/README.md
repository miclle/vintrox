# v120 红翼侧外挂筒后端盖

参考视频第 60、90 帧可见后端盖的同心圆边和偏置凹口。以保存的 v119 为基线，重建一件后端盖。凹口中心的 X、Z 根据两帧标注估计，Y 使用现有端盖深度。两帧的凹口中心投影距离分别由 19.88、42.07 px 降至 0.20、1.45 px，这两帧均参与位置估计。凹口底面、背面连接和材料均为外观假设。第 120 帧的卷线遮挡凹口，仍用于核对外缘。[三视角近景](cap-variants.png) · [凹口投影数据](socket-centers.json)

| 固定相机平均轮廓 IoU | v119 | 初版端盖 | v120 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 85.839653% | 85.833243% | 85.842979% |
| 静态七图 | 82.429948% | 82.423415% | 82.434163% |
| 参考拼图十格 | 89.582675% | 89.576554% | 89.583531% |

初版轴向外伸更长，凹口落在参考位置的另一侧，三组均值下降。v120 收回圆边并调整凹口位置，视频五个视角上升、一个视角回落，静态四个视角上升，拼图一个视角回落。沿用原相机、分割规则和新增四支柱排除规则。整圈 90% 和主要部件轮廓偏差 5% 仍待达成。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

采用 v120。后端盖与筒内衬及卷线护套具有正体积交叠，保存模型的凹口和底面探针通过。保存读回确认 696 个可见对象、853 个闭合 STEP 实体、四支柱和实测平面屏。端盖生成函数与保存实体的体积对称差为零。FreeCAD 原生四视图的颜色与可见性通过复核。[构建与搭接](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

沿原十方位相机用对象 ID 归属轮廓外侧多余像素。大喷口叶片约 17,527 像素，前罩内衬约 11,775 像素，小喷口脊条约 11,086 像素。参考暗边、玻璃和遮挡会影响像素归属，这些数据用于挑选要逐视角检查的零件。视频平均 IoU 仍按原轮廓计算。[差异板](boundary-diagnostic/boundary-regions-board.png) · [逐视角归属](boundary-diagnostic/boundary-regions.json)

v130 接替正式入口后，本目录保留相机、对照板、网格清单和验证报告。重放 v120 需要从本地清理前的备份恢复原模型和网格，再按本目录三组 `cameras.json` 运行渲染和叠加。端盖的生成函数为 `tools/drone_concept.py` 中的 `barrel_rear_cap_shape`。[清理记录](../../../../docs/storage-cleanup.md) · [网格清单](mesh-archive.json) · [渲染命令](../v107-handle-arm-inward-tilt/README.md)
