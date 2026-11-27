# v244 喷口叶片末段试验

基于 v242 的保存模型，在喷口局部 Z=113 mm 处接续并将末段轴向跨度放大至 1.18 倍。共修改 31 件叶片及附属细节。保存读回的闭合实体、原有接合及 13 件支撑实体差集通过复查。[构建记录](candidate-check.json)

| 固定相机 | v242 | v244 |
| --- | ---: | ---: |
| 视频十方位平均轮廓 IoU | 85.9252085% | 85.9295876% |
| 静态七图平均轮廓 IoU | 82.5372638% | 82.5351165% |

静态图均值略降，正式入口采用 v242。拼图十格留待后续有望采用的候选复查。[视频对照板](video-comparison/comparison-board.png) · [静态对照板](stills-comparison/comparison-board.png)

按原固定相机和既有参考标注，计算采样点到可见叶片族边缘的距离，并以同相机下实测平面屏的横向投影宽度归一化。v242 和 v244 各有 6 个视角的最大采样偏差超过 5%。v244 在两处侧后视频视角的 RMS 分别由 27.33 降至 26.35 px、由 28.55 降至 27.75 px，最大采样偏差仍分别为 20.77% 和 21.94%。测量只覆盖已标注的末端，叶片遮挡边沿也会参与最近距离计算。[逐点报告](visible-petal-edges.json) · [局部对照板](visible-petal-edges.png)

## 复现

1. 从正式 v242 FCStd 重建临时网格。运行 `tools/experiment_drone_petal_axial.py`，传入 v242 FCStd 与网格，使用 `--construction tip-splice --station 113 --factor 1.18`。保存目录使用新路径。
2. 用 v242 的视频和静态相机运行 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。同样的相机与网格用于 `tools/render_drone_object_ids.py`，候选对象 ID 分别输出到候选目录的 `video-ids` 和 `still-ids`。
3. 运行 `tools/compare_drone_visible_petal_edges.py`。传入 `--baseline <v242 归档目录>`、`--baseline-mesh <v242 临时网格>`、`--candidate <候选目录>`、`--baseline-video-ids <v242 视频 ID>`、`--baseline-still-ids <v242 静态 ID>`，以及 `--observations` 指向下列历史标注。候选 FCStd 位于候选目录的 `candidate.FCStd`。[参考标注](../v110-nozzle-pose-minus7/tip-measurement.json) · [v242 基线](../v242-belly-y097/README.md)
