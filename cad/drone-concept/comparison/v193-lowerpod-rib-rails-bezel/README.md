# v193 LowerPodRib and screen bezel refinement

从 v173 同时组合两项互不重叠的真实 CAD 局部修订。36 件 LowerPodRib 与 72 件 LowerPodEdgeRail 按 99.25% 收缩，屏框和压边每边外扩 0.1 mm。实测平面屏、可视区、外挂筒、侧控件、格栅和四根支柱保持。

| 固定相机 | v173 | v193 |
| --- | ---: | ---: |
| 视频十方位 | 85.90093% | 85.91005% |
| 静态七图 | 82.52506% | 82.53388% |
| 拼图十格 | 89.65442% | 89.66409% |

独立保存读回确认 696 个可见对象、853 个闭合 STEP 实体，底部喷口边轨最大间隙为 0 mm，四根支柱对称差为 0 mm³。FreeCAD 原生四视图确认 70 组颜色、696 个可见对象，文件关闭后哈希保持。整圈 90% 和主要部件完整轮廓偏差 5% 仍未达成。[逐视角结果](candidate-results.json) · [实体检查](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

网格不随仓库保存。使用保存的候选 FCStd 和 `tools/export_saved_drone_meshes.py` 在临时目录重建渲染输入，避免提交超过 GitHub 普通 Git 限制的单个大文件。

当前保存的左右音箱外沿固定视角测量已归档。[外沿测量](side-ring-check.json)。四个已有参考视角的手工边界拟合 RMS 为约 5.98 px，最大距离约 15.93 px。该测量复用已有参考标注，不能替代完整轮廓验收。

still-05 的保存 CAD 对象 ID 归因已补充到 [局部边界报告](stills-comparison/still-05-boundary-regions.json) 和 [诊断图](stills-comparison/still-05-boundary-regions-diagnostic.png)。在固定相机和真实遮挡下，填洞参考轮廓之外的 56,398 像素中，主要归因对象为 `ClosedBellyPan`、`ControlRail`、`BassVisualCone`、`HoodShoulderCrownLeft`、`BottomChassis` 和 `WingFoldFacetLeft`。该排序用于下一轮检查目标，不改变主 IoU，也不证明这些对象应被删减。脚本为 [analyze_drone_still_boundary_regions.py](stills-comparison/analyze_drone_still_boundary_regions.py)，网格仍从当前 FCStd 临时重建。
