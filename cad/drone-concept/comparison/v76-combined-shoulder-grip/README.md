# v76 后肩与提手组合候选（未采用）

v76 从研究优选 v69 组合两个互不重叠的真实 CAD 试验：v70 的 `RearArmourCheekLeft/Right` 后肩截面，以及 v75 的十件 `GripBand0–9` 提手包覆。屏幕、外挂筒、屏幕侧控件、格栅、四根新增支柱和其余 686 件保存几何保持。

组合候选的 FCStd、STEP、固定十视频／七静态渲染、叠加差异、颜色网格、原生 FreeCAD 视图和读回报告已绑定最终保存哈希。最终保存模型为 698 个对象、696 个可见对象，STEP 为 1008 个有效闭合实体；13 件支撑实体与 v69 对称差为零。原生只读显示为 696 件可见对象，颜色与网格最大通道差为 `0.0019608`，关闭后文件哈希未变。

**未采用。** 固定相机视频十方位平均轮廓 IoU 为 **85.489985%**，静态七图为 **82.187082%**，相对 v69 的变化为 **−0.063335／−0.072537 个百分点**；视频仅 2/10、静态仅 2/7 视角改善。完整结果保留全部退步视角，未改变相机、分割阈值、四支柱排除规则或主 IoU。外观目标 90% 和主要部件完整轮廓 5% 仍未达到。

组合没有被简单丢弃：两个局部候选在各自视角曾有收益，但联合后退步，说明它们不能独立推广为整体比例修正。下一步应在真实遮挡下联合核对后肩、提手、前罩及大喷口的投影边界，避免用互不相关的局部指标推动整机替换。

局部候选的来源与限制：v70 后肩指数研究见 [v70](../v70-loop2p2-shoulder125/README.md)，v75 提手圆弧研究见 [v75](../v75-grip-arcs/README.md)。拟合点和轮廓均来自已经查阅过的参考图片／视频，不是新留出证据；参考曲面屏由实测平面屏加透明罩假设表示，不是原作网格或制造尺寸。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建检查](candidate-check.json) · [读回](readback-verification.json)
- [十视频叠加／差异](video-comparison/comparison-board.png) · [七静态叠加／差异](stills-comparison/comparison-board.png)
- [原生四视角](native-display/native-board.png) · [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)
- [对象 ID 与外侧区域诊断](video-ids/boundary-regions.json) · [候选逐视角结论](candidate-review.json)

复现组合使用 `tools/experiment_drone_combine_candidates.py`，输入 v69、v70、v75 的保存 FCStd 与 v69 网格；输出目录必须为空。渲染使用 `tools/render_drone_concept.py` 与 v69 的固定 cameras.json，叠加使用 `tools/compare_drone_reference.py`，STEP 读回使用 `tools/readback_drone_loop_radius_candidate.py --expected-step-solids 1008`，原生显示使用 `tools/verify_drone_native_display.FCMacro`。流程不使用图像变形、逐部件配准或删除可见零件。

正式 v61 与研究优选 v69 保持，v76 仅作为组合研究归档。未作制造、打印、装配、承力、声学、热、电气或实物验收。
