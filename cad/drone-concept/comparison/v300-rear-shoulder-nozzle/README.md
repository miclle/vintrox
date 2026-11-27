# v300 后肩与大喷口叶片

以 v292 保存模型为基线，将两侧后肩护甲沿横向缩至 88%，固定内侧 X=±89 mm，每侧外缘内收 3.36 mm。第 7、9 号喷口叶片在局部 Z=105 mm 后沿轴向伸至 1.5 倍，每 17 mm 原跨度径向内移 3.6 mm。两处合计修改 14 件保存形体。平面屏采用实测 210 × 160 × 2 mm，曲面罩和参考中被挡住的结构按外观推定。外挂筒、屏幕侧控件、格栅和四根支柱均保留。[保存几何与哈希](candidate-check.json) · [叶片筛选](../v299-nozzle-radial-inset/README.md)

| 固定相机 | v292 | v300 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.034597% | 86.044955% | +0.010357 |
| 静态七图 | 82.587208% | 82.589979% | +0.002772 |
| 拼图十格 | 89.783549% | 89.825407% | +0.041858 |

后肩单独收窄 6% 和 12% 时，视频均值分别为 86.033196% 和 86.027342%，静态均值为 82.591435% 和 82.596305%。组合后静态第 03 图下降 0.12913 个百分点，后肩附近少覆盖 496 个参考前景像素。视频第 05 方位下降 0.04576 个百分点，第 06 方位上升 0.07021 个百分点。叶片可见端缘复测中，第 02 与第 06 方位的最大偏差分别从 26.52% 和 27.47% 降到 25.13% 和 25.98%，第 05 方位从 8.59% 升至 8.91%。视频整圈 90% 与主要部件轮廓偏差 5% 的目标仍待达到。[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png) · [可见末端边缘](visible-petal-edges.json)

FCStd 和 STEP 已独立读回，853 个 STEP 实体均有效闭合。FreeCAD 原生四视图核对了 696 个可见对象与 70 组颜色。九张预览、12 秒转台和三组固定相机对照均由保存模型生成。独立重建网格与渲染输入逐字节一致。[读回报告](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json) · [网格记录](mesh-archive.json)

## 复建

从 v292 的保存 FCStd 重建网格。将 FCStd 和网格传给本目录 `shoulder-screen/screen.py` 的 `--base` 和 `--mesh`，指定临时 `--output`，并传入 `--scale .88`。另按 v299 的步骤生成内移 3.6 mm 的两片叶片。运行本目录 `combine.py`，将两个候选目录传给 `--shoulders` 和 `--leaves`，把本目录的 `candidate-check.json` 传给 `--checks`，并提供同一 v292 FCStd、网格和新的 `--output`。以输出 FCStd 和网格重放三组固定相机。[v292 基线](../v292-brow-shoulder-inset/README.md) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
