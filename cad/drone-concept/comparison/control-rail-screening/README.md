# Control rail screening v212–v215

从 still-05 对象归因出发，刚性平移 `ControlRail`、`ControlRailLip`、`ControlInset`、`ControlKeyBed`、两侧端部护块和端部螺钉。Y 方向正值表示后移，负值表示前移。

| 候选 | Y 位移 | 视频十方位 | 静态七图 | 拼图十格 | 结论 |
| --- | ---: | ---: | ---: | ---: | --- |
| v212 | +0.5 mm | 85.902778% | — | — | 保留 v193 |
| v213 | −0.5 mm | 85.914434% | 82.521219% | 89.668730% | 保留 v193 |
| v214 | −0.1 mm | 85.911097% | — | — | 保留 v193 |
| v215 | −0.25 mm | 85.911839% | 82.526836% | 89.666594% | 保留 v193 |

控制条前移改善视频和拼图，静态七图退步，正式模型保持 v193。下一步拆分控制条主体、压边和端部护块，避免整体平移继续牺牲静态视角。

- [筛选记录](screening.json)
- [v213 三组比较](v213/video-comparison/comparison-board.png)
- [v215 三组比较](v215/video-comparison/comparison-board.png)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时生成网格，不依赖 Git LFS。
