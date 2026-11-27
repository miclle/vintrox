# v127 与 v128 底部回环

以保存的 v120 为基线，只重建两个镜像回环。v127 沿用 v111 的 30% 路径方案，横向位移减半，保留 2.2 mm 圆截面半径。v128 在该方案上将前段四个控制点分别向前移 3、4、2.5、1 mm，并恢复前两个移动点的原始高度。四个端点沿用 v120。参考中的遮挡段按可见弧线推定。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v120 | 85.842979% | 82.434163% | 89.583531% |
| v127 | 85.847713% | 82.457683% | 89.586427% |
| v128 | 85.844711% | 82.473869% | 89.585530% |

第 120 帧正后方采样，v127 两侧 RMS 由 27.04、22.98 px 降至 23.13、19.54 px，v128 分别为 23.13、19.51 px。第 180 帧最远采样点偏差由投影屏宽的 19.25% 升至 21.93% 和 26.33%。该侧前段在相同相机下仍部分被小喷口挡住，向前移进一步缩短了可见弧段。两组整机均值的提升有限，正式入口继续采用 v120。[v127 可见边缘](v127/visible-loop-edges.png) · [v128 可见边缘](v128/visible-loop-edges.png)

两组均确认 696 个可见对象、853 个有效闭合 STEP 实体、两个回环的网格与保存 CAD 一致，以及四根支柱的保护实体一致。每组 26 项支撑交叠比较均无退步。直接读取最终 FCStd 后，用端点处半径 3 mm 的球与回环、腹板相交，四个端点均有约 38.78 mm³ 的连接体积。FreeCAD 原生四视图通过颜色与可见性核对。[v127 保存接合](v127/saved-contact-check.json) · [v128 保存接合](v128/saved-contact-check.json) · [v127 原生显示](v127/native-display/native-display-verification.json) · [v128 原生显示](v128/native-display/native-display-verification.json)

- v127 [视频](v127/video-comparison/comparison-board.png) · [静态](v127/stills-comparison/comparison-board.png) · [拼图](v127/sheet-comparison/comparison-board.png)
- v128 [视频](v128/video-comparison/comparison-board.png) · [静态](v128/stills-comparison/comparison-board.png) · [拼图](v128/sheet-comparison/comparison-board.png)

复建使用 v120 的保存 FCStd 和解压网格。按 v111 的回环生成与打包命令，将输入改为本目录各组的 `path-fit.json`，半径使用 `--radius 2.2`。沿用 v120 三组相机重放全部叠加和差异图，再用视频对象 ID 与现有标注复测可见边缘。两个拟合输入保留既有参考标注和历史拟合数值，当前候选距离以各自的 `visible-loop-edges.json` 为准。[v120 输入](../v120-barrel-rear-cap/README.md) · [生成与重放命令](../v111-underbody-loop-path/README.md)
