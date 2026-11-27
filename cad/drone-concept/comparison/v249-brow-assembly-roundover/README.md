# v249 前罩端部弧线试验

从保存的 v242 出发，在前罩本体、金属包边和内衬两侧下端分别切出 7 mm 的圆弧轮廓。三件均经保存读回复核，原有接合仍为零间隙。前罩本体已有的四处高级几何检查报告仍存在。FCStd 仅更换三件的 BRep，颜色和可见性数据与 v242 逐字节一致。[几何报告](candidate-check.json)

| 固定相机 | v242 | v249 |
| --- | ---: | ---: |
| 视频十方位 | 85.9252085% | 85.9267570% |
| 静态七图 | 82.5372638% | 82.5410554% |
| 拼图十格 | 89.6719938% | 89.6701440% |

复用 v248 的标注，前罩总成外边在 `video-01` 和 `video-07` 的最大局部偏差分别从投影屏宽的 **8.67% 和 9.48%** 降到 **5.09% 和 5.02%**。同两帧可见前罩本体在弧线前方留有薄边。正式交付继续采用 v242，v249 的独立 STEP 和原生显示读回尚未开展。[近景](brow-tip-detail.png) · [逐点数据](brow-tip-samples.json) · [v248 标注方法](../v248-brow-tip-roundover/README.md)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

用 FreeCAD Python 运行 `tools/experiment_drone_brow_tip_roundover.py --base <v242.FCStd> --base-mesh <v242网格> --output <新目录> --assembly --radius 7` 生成候选。使用 v242 的三组相机重放固定视角和视频对象 ID。[v242 相机与流程](../v242-belly-y097/README.md)
