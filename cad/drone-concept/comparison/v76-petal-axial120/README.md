# v76 保存叶片轴向延长（未采用）

从 v69 已保存喷口出发，局部 Z=83 mm 处锚定，轴向扩大 1.20 倍；108 件叶片与附件变化，其余 590 件 BRep 保持字节一致。此法不重建已知与保存喷口不同的源生成器。实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm、四支柱、外挂筒、侧控件与格栅保留。

**不采用**：十视频／七静态固定相机 IoU 为 **85.507740%／82.231550%**，均低于 v69 的 85.553320%／82.259620%。36 件导轨／铰座出现新的 `BOPAlgo GeomAbs_C0` 错误，19 项接合距离退步；不能因基础有效闭合或 STEP 读回通过而忽略这些失败。

[预筛假设](extension-hypothesis.json)将末端边采样点沿轴延长，三拟合视角 RMS 26.42→15.73 px，另四个已查阅视角 13.80→9.44 px；[真实保存候选测量](tip-measurement.json)七视角合计 RMS 12.08 px。采样含隐藏边和厚度，历史留出视角已被后续研究使用，本轮不是新留出验证。这些局部距离不等于可见轮廓误差，不证明主要部件完整轮廓 ≤5%。

[独立读回](readback-verification.json)：698 对象、696 可见对象、1008 有效闭合 STEP 实体，体积相对误差 4.43×10⁻⁷；108 件变化网格与最终重开 FCStd 一致，保护支撑保持。[归档检查](archive-preservation.json)保留其余 BRep 与正式 v61 的 2095 个 GUI 成员。[原生四视角](native-display/native-board.png)已目视检查，696 件可见、颜色在半个 8 位色阶内匹配，打开关闭后哈希不变；基础显示检查不豁免高级几何失败。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [参数／失败接合记录](candidate-check.json) · [逐视角结论](candidate-review.json)
- [十方位比较板](video-comparison/comparison-board.png) · [七图比较板](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

复现时在仓库根目录设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，使用 FreeCAD 自带 Python：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/fit_drone_saved_petal_extension.py --output /tmp/vintrox-v76-hypothesis.json
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_petal_axial.py --base-model cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-meshes cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --output /tmp/vintrox-v76-diagnostic --factor 1.2 --station 83
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/finalize_drone_petal_axial.py --diagnostic /tmp/vintrox-v76-diagnostic --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v76-package
```

渲染沿用 `tools/render_drone_concept.py`、CPU、v69 两套 cameras.json；比较使用 `tools/compare_drone_reference.py`，不移动相机、不形变图像、不遗漏可见零件，仅按既有规则排除新增支撑区域。静态第六图是线框参考，其前景分数不是实体轮廓精度。

正式 v61 与研究优选 v69 保持。下一步检查固定根部、只延长末端的真实 CAD 接缝方案。90%／完整主要部件 5% 目标未完成；曲面罩及不可见结构仍为假设，未作制造、装配、光学、电气或实物验收。
