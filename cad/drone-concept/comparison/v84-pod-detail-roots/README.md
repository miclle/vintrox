# v84 小喷口压条根部修正（未采用）

从 v83 保存实体出发，仅截除 108 件压条／脊条在局部 Z<42.304864mm 的根部，不重建其余部分。变化实体相对 v83 的新增体积均小于 1e-6mm³，消除罩面穿出条纹，端部和接合检查保持；主体叶片仍是圆截面放样假设，未恢复参考中的全部单片折边。

**未采用为正式或研究优选模型。** 固定十视频／七静态平均 IoU 为 **85.541304%／82.233657%**，低于 v69 的 85.553320%／82.259620%。仅 3/10 视频与 1/7 静态视角改善。参考填洞轮廓外多出像素为 195,873，v69 为 194,695。全部不利视角保留；相机、主 IoU、分割阈值及四支柱排除规则未改变。

口环拟合观察来自视频第 0／60／180／240 帧，人工像素有暗边和阴影歧义，全部已在历史查阅，不是新留出数据。保存口环中心线 RMS 为 3.518193px；真实遮挡后的口环 ID 可见边界 RMS 为 3.24／2.42／2.45／3.13px，v69 为 8.93／12.56／12.91／15.79px。四组可见边界最大观察偏差为投影屏幕水平跨度的 1.27%／3.18%／2.64%／1.49%，只是人工口沿点的单向距离，不能证明完整小喷口或全部主要部件轮廓通过 5%。

周围回环保持 v69 几何。第 120 帧两组回环边界 RMS 仍为 27.04／22.98px；第 180／60 帧为 10.81／13.61px。没有删除落于小喷口、主壳或外挂筒内衬的观察。移动口环不能单独解决整体遮挡和比例问题。

[最终保存接合检查](saved-pod-verification.json)覆盖 36 片实际端面、完整边界采样及 328 组接合，无退步。端面面积对称差为零，边界最大距离小于 1e-6mm。此前 0.001mm 厚切片约 2.208057e-6mm³ 的差异包含放样斜率改变；该旧失败结果保留在 v83，不能把有限邻域误称为端面。检查改为实际端面，同时保留薄切片诊断，不要求改形叶片的全部邻域不变。

[FCStd／STEP 独立读回](readback-verification.json)为 698 个几何对象、696 件可见对象、1008 个有效闭合 STEP 实体，体积相对误差约 3.66e-7；150 件相关零件网格逐顶点／逐面与最终重开 FCStd 相等。未修改的 BRep／映射逐字节保持，正式 v61 的 2095 个 GUI 成员保持。[原生四视角](native-display/native-board.png)已目视检查；颜色差异小于半个 8 位色阶，打开关闭后模型哈希不变。四支柱、外挂筒、侧控件和格栅均保留；实测平面屏保持 210 × 160 × 2mm、可视区 200 × 150mm，参考曲面罩与不可观察结构仍是假设。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [拟合](lip-fit.json) · [构建检查](candidate-check.json) · [逐视角结论](candidate-review.json)
- [十视频叠加／差异](video-comparison/comparison-board.png) · [七静态叠加／差异](stills-comparison/comparison-board.png)
- [小喷口共同裁切](pod-closeup.png) · [真实可见边界与观察归属](visible-pod-loop-edges.json) · [边界板](visible-pod-loop-edges.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png) · [区域诊断](video-ids/boundary-regions.json)

复现使用带 NumPy／SciPy／Pillow 的 FreeCAD Python，设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`。v83 的拟合与生成使用 `tools/fit_drone_lower_pod_rim.py`、`tools/experiment_drone_lower_pod_lip.py`；v84 使用 `tools/experiment_drone_pod_detail_roots.py --root-z 42.30486393690599`，以 v83 为父模型和网格。先运行 `tools/verify_drone_lower_pod_lip.py`，再将报告传给 `tools/finalize_drone_petal_axial.py --verification <报告>`。最终保存模型再次执行该验证器；使用 `tools/measure_drone_saved_pod_lip.py` 核对口环和归档成员。

渲染使用 `tools/render_drone_concept.py`、`tools/render_drone_object_ids.py` 与 v69 的 video/stills cameras.json；叠加用 `tools/compare_drone_reference.py`，原生显示用 `tools/verify_drone_native_display.FCMacro`。导出读回使用 `tools/readback_drone_loop_radius_candidate.py --expected-step-solids 1008 --verify-mesh-objects <v83 的全部 150 件 changed_objects>`。边界诊断使用 `tools/compare_drone_visible_pod_edges.py`，不更改主评分。构建与打包目录必须为空。

正式 v61 与研究优选 v69 保持。下一步联合核对单片叶片、外罩比例及小喷口／底壳／外挂筒的遮挡，90% IoU／完整主要部件 5% 目标未完成。未作制造、打印、装配、电气或实物验收。
