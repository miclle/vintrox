# v265 ClosedBellyPan Y 向微调筛选

从 v259 保存模型出发，只对 `ClosedBellyPan` 以保存的前端 `Y=25 mm` 为基准做整体 Y 向微调。`scale099` 收缩到 0.99 倍，`scale101` 放大到 1.01 倍。实测平面屏、外挂筒、侧控件、格栅和四根支柱保持。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 决策 |
| --- | ---: | ---: | ---: | --- |
| v259 基线 | 86.008085% | 82.574342% | 89.772706% | 正式入口 |
| scale099 | 86.010581% | 82.574452% | 89.773019% | 不采用 |
| scale101 | 86.007036% | 未完成 | 未完成 | 不采用 |

scale099 三组相机均有极小提升，视频 +0.000025、静态 +0.000001、拼图 +0.000003 个百分点，属于渲染与三角化噪声量级。scale101 视频下降 0.000010 个百分点。两档均不替换正式 v259。

scale099 的 STEP 独立读回确认 696 个可见对象对应 853 个闭合有效实体。两档候选均从最终保存 FCStd 重建网格，并恢复 v259 的颜色与可见性载荷。比较未使用图像变形、逐件配准或删件。

[scale099 视频](scale099/video-comparison/comparison-board.png) · [静态图](scale099/still-comparison/comparison-board.png) · [拼图](scale099/sheet-comparison/comparison-board.png) · [STEP 读回](scale099/step-readback.json)

[scale101 视频](scale101/video-comparison/comparison-board.png) · [STEP 读回](scale101/step-readback.json)

复现使用 `tools/experiment_drone_closed_belly_y.py --scale .99` 或 `--scale 1.01`，再用 `tools/restore_candidate_display.py`、`tools/export_saved_drone_meshes.py`、`tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。
