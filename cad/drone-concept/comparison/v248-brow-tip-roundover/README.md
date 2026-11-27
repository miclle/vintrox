# v248 前罩内衬端部圆角

参考视频的三个近景显示，前罩下端由斜边圆滑转入底边。v248 从保存的 v242 出发，在 `BrowUnderside` 两侧前下缘施加 5 mm 圆角。FCStd 仅替换该内衬的 BRep，零件颜色、可见性及其余几何沿用基线。保存读回确认一个有效闭合实体，高级几何检查通过，与前罩和屏框的接合仍为零间隙。[几何报告](candidate-check.json)

| 固定相机 | v242 | v248 |
| --- | ---: | ---: |
| 视频十方位 | 85.925208% | 85.925200% |
| 静态七图 | 82.537264% | 82.537564% |
| 拼图十格 | 89.671994% | 89.671994% |

手工标注取自参考视频三处可辨认的内衬转角和前罩外边。以固定相机下的对象 ID 边界测距，`video-01` 内衬峰值从投影屏宽的 7.97% 降到 6.92%。前罩总成外边在 `video-01` 和 `video-07` 仍分别偏差 8.67% 和 9.48%。近景显示，金属包边和外罩在部分画面遮住内衬圆角。三组对照与局部采样支持以 v242 为正式版本。v248 的独立 STEP 和 FreeCAD 原生视图检查尚未开展。[局部近景](brow-tip-detail.png) · [逐点数据](brow-tip-samples.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

## 复现

先从 v242 保存模型导出网格，再用 FreeCAD Python 运行 `tools/experiment_drone_brow_tip_roundover.py --base <v242.FCStd> --base-mesh <网格> --output <新目录> --radius 5`。用 v242 三组相机渲染候选，并用同一视频相机为两版分别渲染对象 ID。逐点报告给出源帧坐标、裁剪范围和投影屏宽。测距取裁剪区域内手工标注到可见 ID 掩膜边界的最近像素距离，内衬使用 `BrowUnderside`，前罩外边使用 `BrowUnderside`、`ProjectingBrow` 和 `HoodEdge` 的并集。并集边界包含遮挡边缘，测量范围限于所示端部。[v242 相机与流程](../v242-belly-y097/README.md)
