# Bottom belly boundary screening v210–v211

从 still-05 对象归因出发，只改变 `ClosedBellyPan` 外侧下缘。v210 将外侧平台抬至 Z=52 mm，v211 抬至 Z=53 mm。屏幕、外挂筒、侧控件、格栅和四支柱保持。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 结论 |
| --- | ---: | ---: | ---: | --- |
| v210，外侧平台 Z=52 mm | 85.909696% | — | — | 保留 v193 |
| v211，外侧平台 Z=53 mm | 85.910099% | 82.533838% | 89.664612% | 保留 v193 |

v211 视频和拼图略升，静态七图略降，未形成三组一致提升。正式模型保持 v193。下一步检查 `ControlRail` 与托壳在 still-05 的联合遮挡。

- [筛选记录](screening.json)
- [v210 视频比较](v210/video-comparison/comparison-board.png)
- [v211 三组比较](v211/video-comparison/comparison-board.png)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时生成网格，不依赖 Git LFS。
