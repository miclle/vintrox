# v124 大喷口叶片末段收径

从正式 v120 出发，在喷口局部 Z=110 mm 处接续叶片末段。两组均按原轴向跨度 17 mm 计，径向向内收 4 mm。第一组将末段轴向拉伸至 1.45 倍，并沿局部 Y 偏移 4 mm。第二组使用 1.65 倍和 7 mm。共变更 46 件，根部、导轨和铰座沿用 v120。接缝处保持共面连接，曲率连续性仍待核对。实测平面屏、外挂筒、侧控件、格栅和四支柱随完整模型一起渲染。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU | 叶片末端最大采样偏差 |
| --- | ---: | ---: | ---: | ---: |
| v120 | 85.842979% | 82.434163% | 89.583531% | 22.74% |
| 1.45 倍 | 85.843620% | 82.429526% | 89.597781% | 21.94% |
| 1.65 倍 | 85.843903% | 82.428362% | 89.605929% | 21.41% |

较短方案的七组既有末端标注 RMS 均下降。较长方案改善六组，`video-05` 从 7.76 px 升至 7.92 px。最大采样偏差仍出现在 `video-06`。这些距离以投影屏宽归一化，最近边缘可能属于遮挡边界，采样仅覆盖可辨认的局部。两组视频和拼图略升，静态七图回落，正式模型继续采用 v120。[1.45 倍局部对照](moderate/visible-petal-edges.png) · [1.65 倍局部对照](extended/visible-petal-edges.png)

两组保存读回均通过 95 项接合检查，确认 696 个可见对象、853 个有效闭合 STEP 实体、46 件重三角化结果一致以及支撑实体保持。FreeCAD 原生四视图确认可见性、70 组显示颜色与网格相符，读回后文件哈希一致。[1.45 倍读回](moderate/readback-verification.json) · [1.65 倍读回](extended/readback-verification.json) · [原生显示](native-display/native-display-verification.json)

- 1.45 倍 [视频](moderate/video-comparison/comparison-board.png) · [静态](moderate/stills-comparison/comparison-board.png) · [拼图](moderate/sheet-comparison/comparison-board.png)
- 1.65 倍 [视频](extended/video-comparison/comparison-board.png) · [静态](extended/stills-comparison/comparison-board.png) · [拼图](extended/sheet-comparison/comparison-board.png)

以 v120 保存 FCStd 和解压网格复建。运行 `tools/experiment_drone_petal_axial.py`，两组都传入 `--construction tip-splice --station 110 --tip-radial-shift -4`，再分别传入 `--factor 1.45 --tip-centre-shift 4` 和 `--factor 1.65 --tip-centre-shift 7`。用 `tools/finalize_drone_petal_axial.py` 从 v120 恢复原生颜色并导出 STEP。从保存候选网格按 v120 的三组相机重放渲染、叠加与差异图。用视频和静态对象 ID 与 v110 的既有标注复算局部距离。仓库保留参数、报告和对照板。[v120 输入](../v120-barrel-rear-cap/README.md) · [渲染和对象 ID 流程](../v116-petal-hinge-plus3/README.md) · [既有末端标注](../v110-nozzle-pose-minus7/tip-measurement.json)
