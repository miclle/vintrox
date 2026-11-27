# v250 前罩端部轮廓

在 v242 保存模型上，对前罩本体、金属包边和内衬两侧下端施加 8 mm 圆弧轮廓。切削范围覆盖原有翻边前方，去除了 v249 在弧线前方留下的薄边。FCStd 仅替换三件实体的 BRep，原有颜色和可见性逐字节一致。三件的既有接合均保持零间隙。前罩本体仍有基线已有的四处高级几何检查记录。[几何报告](candidate-check.json) · [v249 对照](../v249-brow-assembly-roundover/README.md)

| 固定相机 | v242 | v250 |
| --- | ---: | ---: |
| 视频十方位 | 85.9252085% | 85.9272020% |
| 静态七图 | 82.5372638% | 82.5506861% |
| 拼图十格 | 89.6719938% | 89.6719037% |

前罩端部在三个已标注视频近景的最大偏差均低于投影屏宽的 5%。其中两处侧视由 8.67% 和 9.48% 降至 4.69% 和 4.26%。这组数据仅覆盖端部。采样参考和固定相机与 v248、v249 相同。采用 v250 是基于局部端部轮廓改善及视频、静态图整体进步，拼图均值下降 0.00009 个百分点。整圈 90% 与所有主要部件 5% 的目标仍待达成。[近景](brow-tip-detail.png) · [逐点数据](brow-tip-samples.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png) · [原生显示](native-display/native-display-verification.json)

用 FreeCAD Python 运行 `tools/experiment_drone_brow_tip_roundover.py --base <v242.FCStd> --base-mesh <v242网格> --output <新目录> --assembly --cover-front --radius 8` 生成候选。以原三组相机重放固定视角，使用视频相机重放对象 ID。标注范围与测距方法见 v248 的记录。[v242 相机与流程](../v242-belly-y097/README.md) · [标注方法](../v248-brow-tip-roundover/README.md)
