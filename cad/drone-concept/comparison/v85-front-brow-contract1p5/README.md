# v85-front-brow-contract1p5 前罩收缩研究候选（未采用）

从研究优选 v69 保存 CAD 出发，仅对 `ProjectingBrow` 与 `BrowUnderside` 绕模型中心 X=0 做横向收缩（比例 `0.985`）。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、外挂筒、屏幕侧控件和格栅均保持。未使用图像变形、逐部件配准或删件。

固定相机结果：

- 视频十方位：候选 `0.855533326154`；v69 `0.855533200917`；差值 `0.00001252` 个百分点。
- 静态七图：候选 `0.823050437413`；v69 `0.822596196183`；差值 `0.04542412` 个百分点。

候选没有在全部固定视角稳定改善，因此不替换 v69；正式入口 v61 也保持不变。逐视角叠加、差异图、对象 ID 边界归因、保存读回和原生颜色/可见性审计均已保存。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [网格绑定](meshes.json)
- [读回验证](readback-verification.json) · [评审结论](candidate-review.json)
- [视频叠加板](video-comparison/comparison-board.png) · [静态叠加板](stills-comparison/comparison-board.png)
- [对象 ID 边界归因](video-ids/boundary-regions.json) · [对象 ID 板](video-ids/boundary-regions-board.png)
- [原生显示审计](../native-display-audit-2026-11-05/native-display-verification.json)

复现：使用 `tools/experiment_drone_front_brow_contract.py` 生成候选；使用 Blender `tools/render_drone_concept.py` 生成 v69 相同固定相机渲染；使用 FreeCAD Python `tools/compare_drone_reference.py` 计算叠加和差异；使用 `tools/render_drone_object_ids.py` 与 `tools/analyze_drone_boundary_regions.py` 做遮挡归因。候选属于外观研究，未完成打印、装配、光学、热、电气或实物验收。
