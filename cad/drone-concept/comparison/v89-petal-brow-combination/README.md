# v89 喷口叶片与前罩组合研究（未采用）

v89 从研究优选 v69 的保存 CAD 出发，合并两个互不重叠的真实 CAD 变化：v88 的 108 个 `NozzlePetal*` 叶片／导轨／根部件切向收缩比例 `0.96`，以及 v85 的 `ProjectingBrow`、`BrowUnderside` 前罩收缩比例 `0.985`。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、外挂筒、侧控件、格栅和四根新增支柱均保持；没有图像变形、逐部件配准或删件。

固定相机结果：视频十方位平均轮廓 IoU 为 `0.855545539678`（v69 `0.855533200917`，提升 `0.00123388` 个百分点），静态七图为 `0.823133886877`（v69 `0.822596196183`，提升 `0.05376907` 个百分点）。静态结果有明显提升，但视频整圈增益很小，90% 整机轮廓及主要部件投影偏差 5% 目标仍未达到，因此不替换正式 v61 或研究优选 v69。

证据包括：

- [FCStd](candidate.FCStd)、[STEP](candidate.step)、[网格绑定](meshes.json)、[候选检查](candidate-check.json)、[评审结论](candidate-review.json)
- [保存读回](readback-verification.json)：698 个对象、696 个可见对象、1071 个有效闭合 STEP 实体；叶片和前罩变化网格逐顶点／逐面一致，四支柱保护通过
- [视频固定相机渲染](video-renders/render-manifest.json)、[静态渲染](still-renders/render-manifest.json)、[视频十方位叠加／差异](video-comparison/comparison-board.png)、[静态七图叠加／差异](stills-comparison/comparison-board.png)
- [对象 ID 边界归因](video-ids/boundary-regions.json)：`NozzlePetal` 仍为最大外侧差异来源（16,351 像素），随后为 `BrowUnderside`、`LowerPodRib` 和 `ScreenBezel`；这只用于遮挡诊断，不改变主评分
- [原生 FreeCAD 显示审计](native-display/native-display-verification.json)：696 个可见对象、颜色最大通道差 `0.001960814`、四视图截图和关闭后哈希保持

复现使用 `tools/experiment_drone_combine_petal_brow.py`、`tools/render_drone_concept.py`、`tools/compare_drone_reference.py`、`tools/render_drone_object_ids.py`、`tools/analyze_drone_boundary_regions.py` 和 `tools/readback_drone_loop_radius_candidate.py`。候选属于外观研究；不代表打印、装配、光学、声学、热、电气或实物验收。
