# v77 固定根部的叶片末段延长（未采用）

从 v69 的保存 BRep 出发，保留局部 Z≤98 mm 的根部，切开真实平面接缝，只把末段轴向扩大 1.35 倍后融合。72 件叶片本体、衬片、边条、末端压边与脊变化；包括 24 根导轨和 12 件铰座在内，其余 626 件 BRep 字节保持。接缝不宣称切向连续，造型仍是图像推导。实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm、四支柱、外挂筒、侧控件与格栅保留，曲面透明罩仍为外观假设。

**不采用**：十视频／七静态固定相机 IoU 为 **85.521540%／82.237159%**，仍低于 v69 的 85.553320%／82.259620%。它修复了 [v76](../v76-petal-axial120/README.md) 的新增高级几何和根部接合问题，但单独延长末段仍不能改善整圈，不替换正式 v61 或研究优选 v69。[完整逐视角结论](candidate-review.json)保留退步。

[构建检查](candidate-check.json)记录 72 件变化形体高级检查均无新增错误、接合距离无退步、13 件保护支撑保持。[独立根部差集](root-preservation.json)在局部 Z<97.99 mm 逐件比较对称体积差，均小于 10⁻⁶ mm³；接缝前 0.01 mm 避开共面布尔不确定性。这不是根部制造或受力验收。

[独立读回](readback-verification.json)：698 对象、696 可见对象、1008 有效闭合 STEP 实体，体积相对误差 3.66×10⁻⁷；变化网格与最终重开 FCStd 逐顶点／逐面一致，支撑保持。[归档检查](archive-preservation.json)确认未改 BRep、导轨／铰座与屏幕保持字节，2095 个 GUI 外观成员与正式 v61 一致。[原生四视角](native-display/native-board.png)已目视检查，696 件可见、颜色在半个 8 位色阶内匹配，文件打开关闭后哈希不变。

[末端采样](tip-measurement.json)七视角 RMS 为 12.66 px，最大 29.42 px；包含隐藏边和实体厚度，不是可见轮廓评分。五视频与两静态观察均已在历史研究中查阅，不是本轮新留出验证；不能据此宣称全部主要部件完整轮廓 ≤5%。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建参数／接合记录](candidate-check.json)
- [十方位叠加及差异](video-comparison/comparison-board.png) · [七图叠加及差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

在仓库根目录设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，用 FreeCAD 自带 Python 复现：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_petal_axial.py --base-model cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-meshes cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --output /tmp/vintrox-v77-diagnostic --factor 1.35 --station 98 --construction tip-splice
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/finalize_drone_petal_axial.py --diagnostic /tmp/vintrox-v77-diagnostic --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v77-package
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_drone_petal_roots.py --candidate cad/drone-concept/comparison/v77-petal-tip-splice/candidate.FCStd --baseline cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --check cad/drone-concept/comparison/v77-petal-tip-splice/candidate-check.json --output /tmp/vintrox-v77-root-check.json
```

CPU 渲染使用 `tools/render_drone_concept.py` 和 v69 两套固定 cameras.json，比较使用 `tools/compare_drone_reference.py`；仅依既有规则排除新增支撑区域，没有移动相机、变形图像或遗漏可见零件。静态第六图为线框参考，前景分数不能解释为实体轮廓精度。

下一步应联合核对叶片出口半径、倾角与外罩遮挡，避免继续只沿轴向追逐隐藏边采样距离。90%／全部主要部件完整轮廓 5% 目标未完成，不代表制造、打印、装配、光学、电气、声学或实物验收。
