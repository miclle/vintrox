# v251–v253 大喷口叶片末段筛查

用 v250 保存几何和固定相机追踪七个视角的 53 个参考点。两处侧后视 `video-02` 和 `video-06` 的 10 条射线均落在空处。静态图中的部分采样则先碰到低音占位或后框。射线结果用于判断哪些区域适合试验末端几何。点位沿用既有标注，画面遮挡使单个像素无法确定唯一的三维对应。[射线记录](v250-petal-occlusion.json)

| 版本 | 轴向接续 Z | 末段轴向倍数 | 每 17 mm 径向偏移 | 每 17 mm 局部 Y 偏移 | 保存实体与接合 |
| --- | ---: | ---: | ---: | ---: | --- |
| v251 | 109.5 mm | 1.28 | 2.5 mm | 1.5 mm | 56 件改动通过 |
| v252 | 111 mm | 1.40 | 4 mm | 1 mm | 41 件改动通过 |
| v253 | 107.5 mm | 1.28 | 1.5 mm | 2 mm | 第 9 号脊条由一个实体分成两个，构建终止 |

v251 和 v252 未新增高级几何错误或接合退步，支撑总成的 13 件实体差集为零。两版的 STEP 独立读回和 FreeCAD 原生视图仍待验证。[v251 几何记录](v251/candidate-check.json) · [v252 几何记录](v252/candidate-check.json) · [v253 构建记录](v253-build-failure.json)

| 对照项目 | v250 | v251 | v252 |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 85.92720% | 85.94017% | 85.94800% |
| 静态七图平均 IoU | 82.55069% | 82.54067% | 82.53781% |
| 拼图十格平均 IoU | 89.67190% | 89.70921% | 89.71680% |
| `video-02` 叶片末端最大偏差／投影屏宽 | 20.96% | 19.36% | 19.38% |
| `video-06` 叶片末端最大偏差／投影屏宽 | 21.94% | 20.89% | 21.14% |

两版在七个已标注视角中仍各有六个超过 5%。v251 的两侧叶片偏差略低，v252 在视频和拼图中的整机得分较高。两版静态七图均值均下降，正式模型继续采用 v250。[v251 叶片局部对照](v251/visible-petal-edges.png) · [v252 叶片局部对照](v252/visible-petal-edges.png)

| 版本 | 视频十方位 | 静态七图 | 拼图十格 |
| --- | --- | --- | --- |
| v251 | [对照板](v251/video-comparison/comparison-board.png) | [对照板](v251/stills-comparison/comparison-board.png) | [对照板](v251/sheet-comparison/comparison-board.png) |
| v252 | [对照板](v252/video-comparison/comparison-board.png) | [对照板](v252/stills-comparison/comparison-board.png) | [对照板](v252/sheet-comparison/comparison-board.png) |

使用 FreeCAD Python 运行 `tools/experiment_drone_petal_axial.py`，以保存的 v250 FCStd 和重建网格传入 `--base-model` 和 `--base-meshes`，指定新的 `--output` 目录及 `--construction tip-splice`。表中各列对应 `--station`、`--factor`、`--tip-radial-shift` 和 `--tip-centre-shift`。使用 v250 的三组固定相机重放彩图，视频和静态相机重放对象 ID。用 `tools/compare_drone_visible_petal_edges.py` 按既有标注比较局部边界，用 `tools/diagnose_drone_petal_occlusion.py` 从 v250 保存网格重放采样射线。[v250 基线与相机](../v250-brow-tip-profile/README.md) · [局部测量流程](../v244-petal-terminal/README.md#复现)
