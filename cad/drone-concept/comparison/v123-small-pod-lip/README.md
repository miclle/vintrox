# v123 小喷口口环微调

以 v120 保存模型为基线，将两侧小喷口口环的局部轴向位置从 36 移至 37.8 mm，主半径从 27.5 收至 27.39 mm。保留喷口根部与叶片末端，重建 150 个对象。沿用 v120 的实测平面屏、四支柱、外挂筒、侧控件、格栅和全部固定相机。[参数](lip-fit.json) · [构建检查](candidate-check.json)

| 固定相机平均轮廓 IoU | 视频十方位 | 静态七图 | 拼图十格 |
| --- | ---: | ---: | ---: |
| v120 | 85.842979% | 82.434163% | 89.583531% |
| v123 | 85.841932% | 82.428480% | 89.584485% |

四组既有口沿采样的 RMS 均下降，各组约改善 2.2–3.3 px。所测最大偏差从投影屏宽的 10.59% 降至 8.73%。这些点已经用于先前研究，且只覆盖可见边缘的一部分。视频和静态整机均值回落，正式模型继续采用 v120。[口沿和回环](visible-pod-loop-edges.png) · [逐点数据](visible-pod-loop-edges.json)

保存读回确认 696 个可见对象、853 个有效闭合 STEP 实体。150 件变更网格重三角化一致，四支柱受保护实体保持。36 个端面和 328 项接合无退步，FreeCAD 原生四视图颜色与可见性通过。[读回](readback-verification.json) · [端面与接合](terminal-contact-check.json) · [原生显示](native-display/native-display-verification.json)

复建用 v120 保存模型与解压网格、此处参数和 v83 的生成、接合验证、打包与对象 ID 流程。叠加沿用 v120 的视频、静态、拼图相机。归档保留参数、对照板和报告。[复建流程](../v83-small-pod-lip/README.md) · [视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)
