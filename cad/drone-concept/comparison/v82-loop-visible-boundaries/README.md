# v82 回环真实可见边界研究（未采用）

从 v69 的两件回环出发，以第 60／120／180 帧的可见内外边缘代替历史高光中心线拟合，保留 11 个原弦长参数站点、9 个低频位移系数和隐藏端点，联合拟合圆截面半径。最终半径约 **4.109314 mm**，投影法向包络预筛 RMS 为 **5.181360 px**。这是手工像素观察及几何假设，不是测绘尺寸或唯一三维恢复。

**未采用**。十视频／七静态固定相机平均 IoU 为 **85.304472%／82.029260%**，均低于 v69 的 85.553320%／82.259620%。视频仅 1/10 改善，静态 0/7 改善。参考填洞轮廓外多出像素由 194,695 增至 207,914；没有改动原主 IoU、前景阈值、相机或排除规则。只改变 `UnderbodyLoop0/1`，其余 696 件几何、实测平面屏、外挂筒、侧控件、格栅及四支柱保持。

本轮修订了观察解释：历史第 120 帧部分“中心线”点实际靠近内侧高光。新的观察显式标记可见内外边缘，但暗色材质与阴影仍有像素歧义。全部帧已在历史研究查阅，不是新留出验证。法向偏移包络只用于拟合，不能代替遮挡后的真实边界检查。

[真实可见边界比较](visible-loop-edges.png)使用最终 FCStd 网格的 opaque 对象 ID，按实际遮挡提取两件回环边界；[数据](visible-loop-edges.json)记录每点最近边界和观察位置实际可见对象。按第 120 帧右侧／左侧、第 180 帧右侧、第 60 帧左侧顺序，v69 的 RMS 为 27.04／22.98／11.85／13.65 px，v81 为 5.39／6.70／8.81／9.18 px，v82 为 **4.35／5.11／7.61／9.11 px**。对应 v82 最大偏差为投影屏幕水平跨度的 **1.81%／2.96%／7.52%／14.74%**，侧面仍未通过 5%。这些是观察到边界的单向距离，含遮挡边与根部边，不能证明完整部件轮廓通过。

第 60 帧最大偏差点 `[651,693]` 在 CAD 中落于 `LowerPod_1`，另有观察落于 `UtilityLinerLeft`；第 180 帧顶部观察落于 `LowerPod_001` 和 `MainEnclosureShell`。同一观测在参考中可见、在 CAD 中被其他部件覆盖，说明周边小喷口／壳体／外挂筒位置和遮挡需要联合核对。保留全部点及误差，没有删去不利观察来提高指标。不能用这些对象 ID 自动认定参考部件身份或要求删除遮挡部件。

[最终保存检查](saved-loop-verification.json)：两件回环有效、闭合、单实体，无高级几何错误；与 13 件支撑相关零件的 26 组相交均为零。四个实际回环端部在 3 mm 球形邻域内与腹板均有约 56.55 mm³ 正体积交叠（球只限定局部区域，检查对象是实际实体）。1082 个未改 BRep／映射成员和正式 v61 的 2095 个 GUI 成员逐字节保持。[FCStd／STEP 独立读回](readback-verification.json)为 698 对象、696 可见对象、1008 有效闭合 STEP 实体，体积相对误差 3.65×10⁻⁷；变化网格逐顶点／逐面等于最终重开 FCStd。

[原生四视角](native-display/native-board.png)已目视检查，696 件可见，颜色差异在半个 8 位色阶内，打开关闭后 FCStd 哈希不变。屏幕保持 210 × 160 × 2 mm、可视区 200 × 150 mm；曲面罩与不可观察结构仍是假设。整体预览保留四根新增支柱，主 IoU 沿用原支撑区域排除规则。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [拟合参数与观察](path-fit.json) · [构建检查](candidate-check.json) · [逐视角结论](candidate-review.json)
- [十视频叠加／差异](video-comparison/comparison-board.png) · [七静态叠加／差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png) · [共同裁切](loop-closeup.png)
- [区域归因](video-ids/boundary-regions.json) · [区域板](video-ids/boundary-regions-board.png) · [v81 基线 ID 清单](baseline-v81-video-ids/object-id-manifest.json)

复现需设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，使用带 NumPy／SciPy／Pillow 的 FreeCAD Python，在仓库根目录执行。构建及打包输出目录必须为空：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/fit_drone_loop_boundaries.py --output /tmp/v82-fit.json
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_loop_path.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --fit /tmp/v82-fit.json --radius 4.109314070578928 --output /tmp/v82-diagnostic
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/finalize_drone_petal_axial.py --diagnostic /tmp/v82-diagnostic --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/v82-package
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_visible_loop_edges.py --candidate cad/drone-concept/comparison/v82-loop-visible-boundaries --baseline-ids cad/drone-concept/comparison/v69-boundary-diagnostic-2026-11-04 --previous-ids cad/drone-concept/comparison/v82-loop-visible-boundaries/baseline-v81-video-ids
```

彩色渲染、对象 ID 和叠加分别使用 `tools/render_drone_concept.py`、`tools/render_drone_object_ids.py`、`tools/compare_drone_reference.py`，全部使用 v69 的视频／静态 cameras.json。几何验证使用 `tools/measure_drone_saved_loop_path.py`；导出验证使用 `tools/readback_drone_loop_radius_candidate.py --expected-step-solids 1008 --verify-mesh-objects UnderbodyLoop0 UnderbodyLoop1`；原生检查使用 `tools/verify_drone_native_display.FCMacro`。边界观察不会作为中心线误差读取，独立可见边界报告承担图像诊断。

正式 v61 和研究优选 v69 保持。下一步联合核对小喷口、底壳、外挂筒与回环的遮挡，不能继续仅靠扭曲回环追逐被遮挡的观察。90% IoU／完整主要部件 5% 目标未完成。未作制造、打印、装配、承力、电气、光学或实物验收。
