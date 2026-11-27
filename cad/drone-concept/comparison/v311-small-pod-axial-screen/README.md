# v311 小喷口叶片轴向筛选

v310 视频十方位的对象归因里，大喷口叶片、小喷口叶片和前罩内衬分别有 18,193、12,144 和 12,032 个像素落在填洞参考轮廓之外。这些像素包含参考中可辨认的暗色表面。以小喷口局部 Z=36 mm 的口环为锚点，两侧叶片带及端部件的轴向跨度分别缩至 97% 和 98.5%。每档 146 件修改形体和 216 项接合距离均通过保存读回复核。[十方位归因](boundary-regions-board.png) · [97% 几何](axial-97/candidate-check.json) · [98.5% 几何](axial-985/candidate-check.json)

| 固定相机 | v310 | 97% | 98.5% |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.184762% | 86.195144% | 86.190302% |
| 静态七图 | 82.639128% | 82.649524% | 82.644263% |
| 拼图十格 | 89.905496% | 89.908445% | 89.907494% |
| 外端圆弧另外两视角 RMS | 7.38 px | 7.83 px | 7.62 px |

两档均提高三组整机平均 IoU。参考端缘标注到保存模型的可见叶片边界距离，在六个视角上的逐视角 RMS 均增大。97% 档第 240 帧从 5.31 px 增至 6.01 px，第 210 帧从 5.29 px 增至 5.90 px。测量覆盖已有端缘样点，可见边界含叶片间隙及遮挡。正式模型继续采用 v310。[基线可见端缘](base-visible.json) · [97% 可见端缘](axial-97/visible.json) · [98.5% 可见端缘](axial-985/visible.json)

重放时复制 [v289 轴向筛选脚本](../v289-small-pod-axial-extension/replay.py)，在 `--axial-scale` 的选项中加入 `.97` 与 `.985`。使用 v310 保存 FCStd、重建网格、空输出目录和 `--anchor-z 36`。沿用 v310 三组相机生成真实 CAD 对照。用 `tools/measure_drone_lower_pod_outline.py` 测量保存叶片端缘，再按视频相机生成对象 ID 图，用 `measure_visible.py` 和 `base-outline.json` 复测可见边界。[视频](axial-97/video-board.png) · [静态图](axial-97/stills-board.png) · [拼图](axial-97/sheet-board.png)
