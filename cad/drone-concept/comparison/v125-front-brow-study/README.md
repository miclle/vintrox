# v125 与 v126 前罩尺寸对照

从保存的 v120 出发，v125 将前罩总成的 21 件零件横向缩至原宽的 98.5%，并绕前罩后平面将深度缩至 97%。v126 只收窄前罩本体和内衬，使用相同的横向比例。两组均沿用实测平面屏、四根支柱及三组固定相机。参考曲面屏的反光和前罩阴影仍受表面材质与照明影响。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 参考拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v120 | 85.842979% | 82.434163% | 89.583531% |
| v125 | 85.808721% | 82.489289% | 89.510419% |
| v126 | 85.831130% | 82.472514% | 89.549147% |

两组静态七图均值提升，视频与拼图均值回落。仅收窄两件的 v126 保留了约七成的静态收益，视频及拼图回落幅度较小。两组均归档为候选，正式模型采用 v120。

v125 在视频十方位中归到 `BrowUnderside` 的参考轮廓外像素由 11,775 增至 12,531，归到 `ProjectingBrow` 的像素由 7,631 降至 5,080。第 0 帧与第 240 帧的近景显示，部分差异位于参考图中仍可见的暗色屏框与内衬。逐件归属供目视核对，整机分数继续使用原参考分割。[v120 斜前方近景](v120-front-outline-inspection.png) · [v125 逐视角归属](v125/boundary-diagnostic/boundary-regions.json)

两组均读回 696 个可见对象和 853 个有效闭合 STEP 实体，变更网格与保存后的几何一致，支撑实体与 v120 一致。FreeCAD 原生四视图复核了 70 组零件颜色及可见性。v125 另检查了 21 件的高级几何和与前罩本体的 20 组距离，已有零间隙搭接保持。内衬此前报告的 16 条曲面错误已消失，前罩本体仍报告 4 条。[v125 读回](v125/readback-verification.json) · [v126 读回](v126/readback-verification.json) · [v125 高级几何及接合](v125/geometry-audit.json) · [v125 原生显示](v125/native-display/native-display-verification.json) · [v126 原生显示](v126/native-display/native-display-verification.json)

- v125 [视频](v125/video-comparison/comparison-board.png) · [静态](v125/stills-comparison/comparison-board.png) · [拼图](v125/sheet-comparison/comparison-board.png)
- v126 [视频](v126/video-comparison/comparison-board.png) · [静态](v126/stills-comparison/comparison-board.png) · [拼图](v126/sheet-comparison/comparison-board.png)

复建使用 v120 的 FCStd 和解压网格运行 `tools/experiment_drone_front_brow_contract.py`。两组都传入 `--scale .985`，v125 再传入 `--depth-scale .97`。用同一组相机重放彩色网格、叠加和差异图。像素归属使用 `tools/render_drone_object_ids.py` 和 `tools/analyze_drone_boundary_regions.py`。本目录归档对照板与检查报告。[v120 输入与重放入口](../v120-barrel-rear-cap/README.md)
