# v304 前侧护壳厚度

从 v302 保存模型出发，以左右前侧护壳各自的内侧 X 面为基准，将横向厚度缩至 75%。这两件护壳的桥板搭接各约 3,909 mm³，左右共 12 项邻件距离检查保住了原有接触。实测 210 × 160 × 2 mm 平面屏、外挂筒、屏幕侧控件、格栅和四根支柱均保留。曲面罩与遮挡结构仍按参考推定。[保存几何](candidate-check.json)

| 固定相机 | v302 | v304 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.059626% | 86.064428% | +0.004802 |
| 静态七图 | 82.592259% | 82.592259% | 0 |
| 拼图十格 | 89.838663% | 89.839082% | +0.000419 |

视频正面提高 0.04802 个百分点，其余九个方位得分相同。拼图第 04 格下降 0.00691 个百分点，第 05 格提高 0.01110 个百分点。厚度减半的候选在正面视频退步。沿护壳和桥板后缘再削 1.5 mm 时，十个视频方位得分与 75% 厚度档相同。侧后近景的有色归因包含参考暗面和零件间隙，可用于定位待复核边缘。整圈 90% 和主要部件轮廓偏差 5% 仍待达到。[侧后与正面近景](local-cheek-review.png) · [厚度减半](alternatives/scale50/video-comparison.json) · [桥板斜切](alternatives/taper15/video-comparison.json)

FCStd 和 STEP 独立读回确认 853 个有效闭合 STEP 实体。FreeCAD 原生四视图核对 696 个可见对象和 70 组颜色。九张预览和 12 秒转台来自保存 CAD，独立重建网格与渲染输入逐字节一致。[读回报告](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

在 FreeCAD Python 环境运行 `replay.py`，将 v302 FCStd 和重建网格传给 `--base` 和 `--mesh`，指定新 `--output`，并传入 `--scale .75`。通过 `PYTHONPATH` 加入仓库的 `tools`。半厚档用 `--scale .5`。桥板试验以 75% 档为输入，运行 `bridge.py` 并传入 `--inset 1.5`。渲染使用 v302 的三个固定相机配置。[v302 网格与相机](../v302-upper-rear-shoulder/README.md) · [视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)
