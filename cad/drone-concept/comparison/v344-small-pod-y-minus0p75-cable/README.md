# v344 小喷口 Y−0.75 mm 与外挂筒卷线候选

以已推送的 v341 保存 CAD 为基线，在两侧 152 件小喷口总成上追加对称刚体 Y−0.25 mm，累计相对 v339/v340 链为 Y−0.75 mm，并保留 v321 的红翼侧下段卷线。四根新增支柱、实测 `210 × 160 × 2 mm` 平面屏、曲面透明罩、外挂筒、屏幕侧控件和格栅均保留。候选经保存 GUI 载荷恢复，颜色和可见性由 `candidate.FCStd` 复现。

| 固定相机比较 | IoU |
| --- | ---: |
| 视频十方位 | 86.2369% |
| 静态七图 | 82.7143% |
| 拼图十格 | 89.9778% |

三组均高于 v341 的 86.2294%、82.7098% 和 89.9722%，但视频整圈仍低于 90%，主要部件投影屏宽 5% 偏差目标也没有被整机指标证明，因此 v344 保留为当前最佳研究候选，正式外观入口仍按文档记录的 v339。

比较使用真实 CAD 三角网格、固定透视相机和半透明叠加。没有图像变形、拉伸、逐部件配准或省略可见零件。评分按既有规则排除四根支柱及其座脚区域。

独立读回确认 FCStd `696` 个可见对象、`853` 个有效闭合实体，STEP `853` 个有效闭合实体，体积相对误差 `5.37e-7`，支柱干涉为 0。`candidate.FCStd` 已恢复并核对保存 GUI 颜色/可见性。原生 FreeCAD 窗口截图仍受锁屏会话限制，未宣称原生窗口验收通过。平面屏输入、曲面罩和不可观察内部细节仍按外观推导记录，不代表制造、装配、光学或实物验收。

## 复现

运行 `tools/experiment_drone_small_pod_pose.py`，基线为 v341 保存模型，参数为 `--offset 0 -0.25 0 --rotation-vector 0 0 0`。随后使用 `tools/restore_candidate_display.py` 从 v341 恢复 GUI 载荷，再用 `tools/export_candidate_drone_meshes.py` 导出网格。视频、静态与拼图分别使用 `comparison/cameras.json`、`still-cameras.json` 和 `contact-sheet-cameras.json`，并通过 `tools/render_drone_concept.py` 与 `tools/compare_drone_reference.py` 生成固定相机渲染、叠加和差异。
