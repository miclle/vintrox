# v267 BassVisualCone 内部凹碗筛选

从 v259 保存模型出发，仅收缩 `BassVisualCone` 的真实 CAD 内部凹碗轮廓。`shrink05` 和 `shrink15` 分别收缩 0.5 mm 与 1.5 mm，外部喷口、叶片、外罩、屏幕、侧控件、格栅和四根支柱保持。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 决策 |
| --- | ---: | ---: | ---: | --- |
| v259 基线 | 86.008085% | 82.574342% | 89.772706% | 正式入口 |
| shrink05 | 86.015193% | 82.563156% | 89.766143% | 不采用 |
| shrink15 | 86.014841% | 未完成 | 未完成 | 不采用 |

两档视频均有噪声量级提升。`shrink05` 的静态和拼图均值下降，因此不进入正式模型。两档均通过保存读回和 STEP 导出，候选证据绑定最终 FCStd。

[0.5 mm 视频](shrink05/video-comparison/comparison-board.png) · [静态图](shrink05/still-comparison/comparison-board.png) · [拼图](shrink05/sheet-comparison/comparison-board.png) · [评分](candidate-review.json)

[1.5 mm 视频](shrink15/video-comparison/comparison-board.png)

复现使用 `tools/experiment_drone_nozzle_cone_scale_v53.py --shrink 0.5` 或 `--shrink 1.5`，再使用 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。没有使用图像变形、逐件配准或删件。凹碗属于外观假设，暗部和遮挡关系仍需谨慎解释。
