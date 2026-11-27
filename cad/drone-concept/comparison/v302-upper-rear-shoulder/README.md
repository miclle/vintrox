# v302 后肩上段恢复宽度

以 v300 保存模型为基线，将 v292 两侧后肩护甲 Z=137 mm 以上的形体与 v300 的收窄护甲融合。实测 210 × 160 × 2 mm 平面屏、外挂筒、侧控件、格栅和四根支柱均保留。曲面罩和被参考画面遮挡的结构按外观推定。[保存几何与接合](candidate-check.json) · [局部宽度候选](../v301-local-rear-shoulder/README.md)

| 固定相机 | v300 | v302 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.044955% | 86.059626% | +0.014672 |
| 静态七图 | 82.589979% | 82.592259% | +0.002280 |
| 拼图十格 | 89.825407% | 89.838663% | +0.013255 |

静态第 03 图提高 0.07055 个百分点，静态第 01 图下降 0.02345 个百分点。视频第 90 帧提高 0.08251 个百分点，第 0 帧下降 0.02550 个百分点。整圈 90% IoU 和主要部件轮廓偏差 5% 的目标仍待达到。[十方位视频](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

FCStd 和 STEP 独立读回确认 853 个有效闭合 STEP 实体。FreeCAD 原生四视图核对 696 个可见对象和 70 组颜色。九张预览和 12 秒转台来自保存后的 CAD，独立重建网格与渲染输入逐字节一致。[读回报告](../../readback-verification.json) · [颜色记录](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

在 FreeCAD Python 环境运行本目录的 `replay.py`。将 v300 FCStd 和重建网格传给 `--base` 和 `--mesh`，将 v292 FCStd 传给 `--wide`，另指定临时 `--out` 和 `--transition 137`。通过 `PYTHONPATH` 加入仓库的 `tools`，沿用 v300 的固定相机。[v300 相机与网格](../v300-rear-shoulder-nozzle/README.md) · [v292 基线](../v292-brow-shoulder-inset/README.md)
