# Control rail terminal screening v219–v221

在 v218 分组筛选后，继续拆分控制条端部和压边。v219 只前移端部护块与螺钉 0.25 mm。v220 只前移 `ControlRailLip` 0.25 mm。v221 只前移 `ControlRailLip` 0.1 mm。

| 候选 | 视频十方位 | 静态七图 | 拼图十格 | 结论 |
| --- | ---: | ---: | ---: | --- |
| v219，端部组 −0.25 mm | 85.907851% | — | — | 保留 v193 |
| v220，压边 −0.25 mm | 85.913852% | 82.531314% | 89.668890% | 保留 v193 |
| v221，压边 −0.1 mm | 85.911557% | — | — | 保留 v193 |

压边局部前移是当前控制条分支的视频最佳方向，静态七图仍退步，正式模型保持 v193。下一步停止整体位置试探，转向 still-05 的局部遮挡和端部几何。

- [筛选记录](screening.json)
- [v220 三组比较](v220/video-comparison/comparison-board.png)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时生成网格，不依赖 Git LFS。
