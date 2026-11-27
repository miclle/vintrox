# v143 大喷口叶片轴向延长

从保存的 v140 出发，在局部 Z=113 mm 接续，把 31 件叶片及末段细节的轴向跨度增至 1.65 倍。接续面至根部的形体按原构造保留。复建使用 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --station 113 --factor 1.65`，再用 `tools/finalize_drone_petal_axial.py` 恢复显示属性、导出 STEP 并重建变更网格。[v140 输入与固定相机](../v140-shoulder-petal-pod/README.md)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v143 | 85.858998% | 82.472106% | 89.611333% |

五组末端标注的 RMS 下降，一组持平，第 150 帧由 7.68 升到 8.16 px。第 180 帧 RMS 从 31.22 降至 29.37 px，最差标注仍偏离投影屏宽的 21.94%。静态整机均值微降，正式模型采用 v140。[逐点数据](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

84 项接合检查通过，31 件变更网格独立读回一致，853 个 STEP 实体有效闭合。四支柱几何一致。原生四视角复核 696 个可见对象和 70 组显示颜色。归档保留参数、报告和对照板。[构建](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从同一固定相机向 53 个既有参考标注的像素中心发射视线，并与全模型保存网格求交。第 60、180 帧各有 5 条视线落在 CAD 投影之外，两版结果相同。正后方和两张静态图合计有 6 条视线先击中低音锥盆，随后才击中叶片，两版均如此。其余视角有 2 个原本落在投影之外的标注点在 v143 中直接击中叶片。首击对象与同视角对象 ID 图逐点交叉检查，差异出现在 ID 图按流程排除的两个支柱座像素。视线分析使用不透明三角网格，局部标注没有可直接测量的三维深度。[v140 视线记录](v140-petal-occlusion.json) · [v143 视线记录](v143-petal-occlusion.json) · [复算脚本](../../../../tools/diagnose_drone_petal_occlusion.py)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
