# v150 黄翼前缘

从保存的 v140 出发，将黄翼前缘第三、第四站的局部 Y 偏移从 2.5、2.0 mm 增至 4.5、2.5 mm。重建五件翼板形体，沿用 v140 相机对整机渲染。既有参考样点的像素坐标保持，报告记录样点原基线与本轮比较基线。[构建与接合](candidate-check.json) · [参考样点](reference-observations.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v150 | 85.834483% | 82.470789% | 89.579860% |

第 210 帧黄翼最大采样偏差为投影屏宽的 8.10%，RMS 从 4.411 升至 4.416 px。其余三组已有样点的距离相同，四组样点仅覆盖可见的局部边界。三组整机均值均下降，正式模型采用 v140。[逐点数据](visible-wing-edges.json) · [局部对照](visible-wing-edges.png)

五件变更形体通过高级检查和九项接合检查。独立读回确认五件变更网格一致、853 个 STEP 实体有效闭合、四支柱几何一致。FreeCAD 原生四视角确认 696 个可见对象和 70 组显示颜色。[保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

复建使用 `tools/experiment_drone_gold_wing_outline.py`，传入 v140 FCStd 和解压网格，参数为 `--inset 5 --front-offsets .5 5.5 4.5 2.5`。使用 `tools/finalize_drone_petal_axial.py` 恢复原生显示并导出 STEP，按 v140 的相机重放。[v140 输入及相机](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
