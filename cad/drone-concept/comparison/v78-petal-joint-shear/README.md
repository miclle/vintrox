# v78 叶片末段轴向、半径与中心联合研究（未采用）

在 v69 保存 BRep 上保留局部 Z≤98 mm 根部，把末段轴向扩大 1.50 倍，并按原局部轴向跨度施加径向与中心剪切：每 17 mm 原跨度分别径向外移 2.5 mm、局部 Y 移动 4 mm。各叶片径向取 index×30°+30°，接缝点不移动；这不是整喷口刚体旋转，也不声称接缝切向连续。72 件本体／衬片／边条／压边／脊变化，其余 626 件 BRep 字节保持，包括固定导轨、铰座、四支柱、实测平面屏、外挂筒、侧控件与格栅。平面屏输入仍为 210 × 160 × 2 mm、可视区 200 × 150 mm；曲面罩与隐藏结构仍是假设。

**未采用**。十视频／七静态固定相机平均 IoU 为 **85.480943%／82.220088%**，均低于 v69 的 85.553320%／82.259620%。七视角保存末端采样 RMS 为 9.53 px，较 v77 的 12.66 px 改善，但隐藏边采样不能代表可见轮廓。联合最优解约为轴向 1.5445、径向 2.5523 mm、中心 5 mm，中心参数碰到上界；采用取整且较小参数只是探索，不是唯一几何恢复。所有七视角均已在历史研究中查阅，不是新留出验证。

本轮新增[可见边界比较](visible-petal-edges.png)与[数据](visible-petal-edges.json)：用真实 CAD 遮挡后的对象 ID，按最近色表容差 <6 合并全部叶片家族，再提取家族边界，避免颜色量化／抖动导致内部假孔。七视角中六个观察点到可见边界的 RMS 改善，但 video-05 从 7.04 px 退步到 9.37 px；video-02／video-06／still-05 的最大观察偏差分别为投影屏幕水平跨度的约 11.06%／11.37%／7.97%。该诊断仍含根部及遮挡边缘，只覆盖部分尖端，不证明完整主要部件 ≤5%。接近侧视时屏幕水平投影变窄也会放大比率。

[区域归因](video-ids/boundary-regions.json)显示既有参考填洞轮廓外的多出像素由 194,695 增至 203,067；没有修改原主 IoU、前景阈值或遮挡规则。封闭暗区或外侧归因不自动证明几何错误。[后视共同裁切](petal-rear-closeup.png)显示片长更接近，但出口与周边线束、暗边仍不一致；固定导轨未延长也限制了局部细节。下一步应按可见单片端部与周边遮挡联合重建，而非继续用全圈单一轴向／半径去追逐最近隐藏边。

[构建检查](candidate-check.json)：72 件变化零件无新增高级 BOP 错误、接合距离无退步。[独立根部差集](root-preservation.json)在 Z<97.99 mm 通过 10⁻⁶ mm³ 阈值；[保存读回](readback-verification.json)为 698 对象、696 可见对象、1008 有效闭合 STEP 实体，体积相对误差 3.66×10⁻⁷，变化网格与最终重开 FCStd 逐顶点／逐面一致。[归档检查](archive-preservation.json)确认未改 BRep 和正式 v61 的 2095 个 GUI 成员保持。[原生四视角](native-display/native-board.png)已目视检查，696 件可见，颜色误差在半个 8 位色阶内，打开关闭后文件哈希不变。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [联合预筛](joint-hypothesis.json) · [末端采样](tip-measurement.json) · [逐视角结论](candidate-review.json)
- [十视频叠加及差异](video-comparison/comparison-board.png) · [七静态叠加及差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

复现：在仓库根目录设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，使用 FreeCAD Python：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/fit_drone_saved_petal_extension.py --joint --output /tmp/vintrox-v78-joint-fit.json
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_petal_axial.py --base-model cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-meshes cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --output /tmp/vintrox-v78-diagnostic --factor 1.5 --station 98 --construction tip-splice --tip-radial-shift 2.5 --tip-centre-shift 4
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/finalize_drone_petal_axial.py --diagnostic /tmp/vintrox-v78-diagnostic --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v78-package
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_visible_petal_edges.py --candidate cad/drone-concept/comparison/v78-petal-joint-shear --baseline-video-ids cad/drone-concept/comparison/v69-boundary-diagnostic-2026-11-04 --baseline-still-ids cad/drone-concept/comparison/v78-petal-joint-shear/baseline-still-ids
```

彩色 CPU 渲染使用 `tools/render_drone_concept.py`，对象 ID 用 `tools/render_drone_object_ids.py`；均使用 v69 固定视频／静态 cameras.json，比较使用 `tools/compare_drone_reference.py`。静态 ID 已按每个相机分辨率生成并保留基线，全部渲染清单绑定模型和相机哈希。没有移动相机、非刚性图像变形或遗漏可见部件；仅按既有规则排除新增支撑区域。静态第六图是线框，前景分数不是实体轮廓精度。

正式 v61 和研究优选 v69 保持，90%／完整主要部件 5% 目标未完成。未作制造、打印、装配、承力、光学、声学、电气或实物验收。
