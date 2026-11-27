# v138 大喷口叶片末段偏移

从保存的 v130 出发，在喷口局部 Z=110 mm 处接续叶片末段。轴向伸长至 1.45 倍，沿局部 Y 偏移 4 mm，两者均以 17 mm 原轴向跨度为基准，径向收径量为 0 mm。共改动 46 件叶片及末段细节，沿用原根部、导轨和铰座。本轮单独观察 v124 延长与中心偏移的作用。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU | 叶片末端最大采样偏差 |
| --- | ---: | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% | 22.736% |
| v138 | 85.854161% | 82.439230% | 89.606856% | 21.939% |

七组既有末端标注的 RMS 均下降。静态 `still-04` 的最大采样偏差从投影屏宽的 6.550% 降到 5.077%，最差视角 `video-06` 从 22.736% 降到 21.939%。视频十方位归到叶片的参考轮廓外像素从 17,528 增至 17,998，静态均值也略降。正式模型采用 v130。末端标注覆盖可辨认局部，可见边缘包含遮挡边界。[逐点数据](visible-petal-edges.json) · [局部对照](visible-petal-edges.png) · [视频区域归属](video-ids/boundary-regions.json)

95 项接合复核未发现退步。FCStd 与 STEP 独立读回确认 696 个可见对象、853 个有效闭合 STEP 实体、46 件变更网格逐顶点及逐面一致、四支柱几何一致。FreeCAD 原生四视角确认 70 组显示颜色及保存可见性。[构建](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从 v130 的保存 FCStd 和解压网格运行 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --station 110 --factor 1.45 --tip-centre-shift 4`。使用 `tools/finalize_drone_petal_axial.py` 恢复原生颜色并导出 STEP，沿用 v130 的三组相机与 v110 的既有末端标注。归档保留报告和对照板，试件模型和网格可复建。[v130 输入与相机](../v130-underbody-loop-path/README.md) · [相邻参数试验](../v124-petal-terminal-taper/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
