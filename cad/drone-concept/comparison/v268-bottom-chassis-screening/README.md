# v268 BottomChassis Y 向微调筛选

从 v259 保存模型出发，仅将 `BottomChassis` 以保存前端 `Y=11.25 mm` 为基准收缩到 0.99 倍。实测平面屏、外挂筒、侧控件、格栅和四根支柱保持。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 决策 |
| --- | ---: | ---: | ---: | --- |
| v259 基线 | 86.008085% | 82.574342% | 89.772706% | 正式入口 |
| scale099 | 86.010229% | 82.575387% | 89.772998% | 不采用 |

三组均值仅提高噪声量级，正式入口继续采用 v259。候选由保存 FCStd 重建网格，包含三组固定相机叠加证据。没有使用图像变形、逐件配准或删除可见零件。

[视频](scale099/video-comparison/comparison-board.png) · [静态图](scale099/still-comparison/comparison-board.png) · [拼图](scale099/sheet-comparison/comparison-board.png)

复现使用 `tools/experiment_drone_bottom_chassis_y.py --scale .99`，再运行 `tools/restore_candidate_display.py`、`tools/export_saved_drone_meshes.py`、`tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。

渲染网格不随仓库重复保存，可由候选 FCStd 和候选清单用 `tools/export_saved_drone_meshes.py` 临时重建。
