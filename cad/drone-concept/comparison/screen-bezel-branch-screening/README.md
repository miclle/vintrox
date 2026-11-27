# Screen bezel branch screening v207–v209

从 v193 的屏框差异归因出发，拆分 `ScreenBezel` 与 `BezelLip` 的小幅外扩候选。v207 只保留屏框本体外扩 0.2 mm。v208 只保留金属压边外扩 0.2 mm。v209 只保留金属压边外扩 0.1 mm。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 结论 |
| --- | ---: | ---: | ---: | --- |
| v207，ScreenBezel +0.2 mm | 85.909696% | — | — | 保留 v193 |
| v208，BezelLip +0.2 mm | 85.911437% | 82.530738% | 89.666909% | 保留 v193 |
| v209，BezelLip +0.1 mm | 85.909696% | 82.533813% | 89.664088% | 保留 v193 |

屏框分支没有在三组相机上形成一致提升。still-01 的对象级归因仍主要指向 `ScreenBezel`，still-05 的主要差异转向 `ClosedBellyPan` 与 `ControlRail`。正式模型保持 v193。

- [筛选记录](screening.json)
- [v207 视频比较](v207/video-comparison/comparison-board.png)
- [v208 三组比较](v208/video-comparison/comparison-board.png)
- [v209 三组比较](v209/video-comparison/comparison-board.png)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时生成网格，不依赖 Git LFS。
