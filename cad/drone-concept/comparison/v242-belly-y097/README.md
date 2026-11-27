# v242 底壳后缘收缩

v242 从 v240 的保存模型出发，将 `ClosedBellyPan` 沿 Y 向缩至 0.97 倍。前端基准为 Y=25.0 mm，后缘从 211.2 mm 收至 205.614 mm。平面屏本体采用实测 210 × 160 × 2 mm，指定可视区为 200 × 150 mm。曲面罩和参考中不可观察的内部细节仍采用外观假设。

| 固定相机 | v240 | v242 | 增量 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 85.9210114% | 85.9252085% | +0.0041970 个百分点 |
| 静态七图 | 82.5368942% | 82.5372638% | +0.0003696 个百分点 |
| 拼图十格 | 89.6714023% | 89.6719938% | +0.0005916 个百分点 |

v243 测试相对 v240 缩至 0.99 倍。补测后，视频十方位、静态七图和拼图十格分别为 85.9232709%、82.5370219% 和 89.6713090%，三组均低于 v242。保留对照板、逐视角指标及重建参数。[视频](v243-screening/comparison-report.json) · [静态图](v243-screening/stills/comparison-report.json) · [拼图](v243-screening/sheet/comparison-report.json)

保存几何复查中，698 个实体对象的体积、表面积和包络签名仅 `ClosedBellyPan` 有变化。四支柱、支脚、套筒和中央支座的实体差集均为零。底壳仍与主壳、底盘、中央支座和两根回环搭接，两侧检修板与底壳相距 20.12 mm，两侧均与主壳、侧封板和护框有体积搭接，左侧检修板另与外挂筒及其安装座相交。搭接反映当前外观模型的实体关系，实际分件和装配待验证。[几何复查](geometry-comparison.json) · [检修板搭接](service-plate-contacts.json)

正式 FCStd 与 STEP 独立读回通过，696 个可见对象对应 853 个闭合 STEP 实体。FreeCAD 四视图复查了 70 种保存颜色。九张展示图、八方位板、96 个角度的转台和三组固定相机叠加均绑定正式 FCStd。[读回报告](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [展示清单](../../renders/render-manifest.json)

视频、静态图和拼图使用固定相机与相同分割规则，只排除新增支撑总成。保留逐视角叠加和差异。90% 整圈 IoU 和主要部件 5% 轮廓目标仍待达成。[视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

十视频视角累计有 172,699 个 CAD 像素位于填洞后的参考轮廓外。对象 ID 贡献最多的是喷口叶片 18,277 像素、小喷口肋 12,144 像素和前罩下衬 12,086 像素。对象归因受遮挡、暗色边缘及抗锯齿影响，用于定位待复查的边缘。保留原始分割和正式 IoU。[对象归因](video-comparison/boundary-regions.json) · [十方位差异板](video-comparison/boundary-regions-board.png)

v244 喷口叶片末段试验的七视角复测显示，v242 有六个视角的最大末端采样偏差超过投影屏宽的 5%。[逐点对照](../v244-petal-terminal/README.md)

v245 和 v246 进一步延长并沿喷口局部 Y 向偏移叶片末段。两者的侧后视角偏差有所下降，静态图平均 IoU 略降。v245 新增三处高级几何检查失败，v246 仍有六个已采样视角超过 5%。[参数与三组固定相机对照](../v245-v246-petal-terminal/README.md)

## 复现

以 v240 的保存 FCStd 运行 `tools/experiment_drone_closed_belly_y.py --base <v240.FCStd> --output <候选目录> --scale 0.97`。v243 使用 `--scale 0.99`。正式显示恢复使用 `tools/restore_candidate_display.py` 和 v240 的 GUI 载荷。使用 `tools/export_saved_drone_meshes.py` 重建正式网格，用各组保存的相机配置运行 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。对象归因使用相同的保存网格和视频相机，依次运行 `tools/render_drone_object_ids.py` 与 `tools/analyze_drone_boundary_regions.py`。候选源哈希见几何构建记录。网格在本地生成，交付使用普通 Git。[几何构建记录](geometry-check.json) · [颜色恢复记录](display-restore.json)
