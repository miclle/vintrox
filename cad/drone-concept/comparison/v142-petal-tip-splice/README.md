# v141／v142 大喷口叶片末段接续

两组均以保存的 v140 为输入，在喷口局部坐标中延长接续面以外的末段，并按每 17 mm 原轴向跨度径向内收 1.4 mm。原有相机、参考图和分割规则用于比较完整的保存模型。由于 v140 的第 180 帧可见末端采样偏差最大，本轮用该视角复核调整方向。

| 试件 | 接续位置 | 轴向倍率 | 改动对象 | 高级形体检查 |
| --- | ---: | ---: | ---: | --- |
| v141 | Z=110 mm | 1.10 | 46 | 两片叶片出现曲面曲线错误 |
| v142 | Z=113 mm | 1.14 | 31 | 通过 |

v141 的 `NozzlePetal0` 和 `NozzlePetal4` 新增 `BOPAlgo_InvalidCurveOnSurface`，在最终导出前结束。v142 的 84 项接合检查通过。保存读回确认 31 件变更网格与实体逐顶点、逐面一致，853 个 STEP 实体有效闭合，四支柱几何一致。原生四视图确认 696 个可见对象及 70 组显示颜色。[v141 失败记录](v141-failed-check.json) · [v142 构建](candidate-check.json) · [v142 读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v142 | 85.854719% | 82.472865% | 89.596030% |

v142 在五组既有末端标注中降低了 RMS，两组持平。第 180 帧的 RMS 从 31.22 降到 30.84 px，最大采样偏差仍为投影屏宽的 21.94%。三组整机均值增加不到 0.003 个百分点，正式模型采用 v140。局部标注覆盖可辨认的末端，可见边界还包含零件遮挡处。[逐点数据](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

使用 v140 的 FCStd 和解压网格运行 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --tip-radial-shift -1.4`，并按表设置 `--station` 和 `--factor`。v142 通过 `tools/finalize_drone_petal_axial.py` 导出，沿用 v140 的三组相机以及 v110 的既有末端标注。归档保存参数、检查报告和叠加板，试件大文件可复建。[v140 输入和相机](../v140-shoulder-petal-pod/README.md) · [既有标注](../v110-nozzle-pose-minus7/tip-measurement.json)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
