# v87-pod-brow-combination 小喷口与前罩组合研究（未采用）

v87 从研究优选 v69 的保存 CAD 出发，组合两个对象集合互不重叠的真实 CAD 候选：v84 的完整 `LowerPod*` 小喷口口环／压条根部变化（152 个对象）和 v85 的 `ProjectingBrow`、`BrowUnderside` 前罩横向收缩（2 个对象）。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、外挂筒、屏幕侧控件及格栅均保持；没有图像变形、逐部件配准或删件。

固定相机比较结果：

- 视频十方位平均轮廓 IoU：`0.855413186493`（v69：`0.855533200917`），略退步。
- 静态七图平均轮廓 IoU：`0.822790416692`（v69：`0.822596196183`），略提升。
- 视频存在退步视角，不能以静态增益替代整圈结果，因此不替换 v69；正式入口 v61 也保持。

候选证据包括：

- [FCStd](candidate.FCStd)、[STEP](candidate.step)、[网格绑定](meshes.json)、[构建检查](candidate-check.json)
- [保存读回](readback-verification.json)：698 个保存对象、696 个可见对象、1008 个有效闭合 STEP 实体，变化网格与保存读回一致，四支柱保护差集为零
- [视频十方位叠加／差异](video-comparison/comparison-board.png)和[静态七图叠加／差异](stills-comparison/comparison-board.png)
- [视频对象 ID 边界归因](video-ids/boundary-regions.json)：`NozzlePetal` 仍是主要外侧多余像素来源，`LowerPodRib` 排名下降但未消除
- [原生 FreeCAD 显示审计](native-display/native-display-verification.json)：696 个可见对象与网格契约一致，颜色最大通道差 `0.001960814`，四视图截图已保存且文件哈希保持
- [彩色预览](previews/hero.png)、[背面](previews/rear.png)、[正面](previews/front.png)、[右侧](previews/right.png)

复现流程使用 `tools/experiment_drone_combine_pod_brow.py`、Blender `tools/render_drone_concept.py`、FreeCAD Python `tools/compare_drone_reference.py`、`tools/render_drone_object_ids.py`、`tools/analyze_drone_boundary_regions.py` 和 `tools/readback_drone_loop_radius_candidate.py`。候选属于外观研究，不能证明打印、装配、光学、声学、热、电气或实物验收。
