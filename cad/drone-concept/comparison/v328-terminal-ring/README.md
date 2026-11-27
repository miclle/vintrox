# v328 按参考出口环调整十二片大喷口叶片

v315 的第 60、120、180 帧对应三组人工标注，19 个点到拟合出口圆的 RMS 为 3.30 px。对每片叶片取保存折边的体积加权中心，并在三维空间找到圆上的最近点。沿喷口局部 Z=99 mm 截开叶片，以该截面为固定端向末端施加渐增位移。半量档取拟合位移的 50%，全量档取 100%。源图暗边、相机拟合和部分遮挡使这个圆的位置存在不确定性。[拟合输入](../nozzle-mouth-fit.json) · [出口环读回](terminal-readback.json)

| 固定相机测量 | v315 | 半量 | 全量 |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 86.2046% | 86.1031% | 85.8670% |
| 静态七图平均 IoU | 82.6877% | 82.6254% | 82.4987% |
| 拼图十格平均 IoU | 89.9582% | 89.9153% | 89.7127% |
| 第 60 帧可见末缘最大偏差 / 投影屏宽 | 20.96% | 11.91% | 4.53% |
| 第 180 帧可见末缘最大偏差 / 投影屏宽 | 21.94% | 11.35% | 6.39% |
| 静态 04 可见末缘 RMS | 8.95 px | 4.89 px | 8.79 px |
| 静态 05 可见末缘 RMS | 10.88 px | 8.39 px | 10.90 px |

半量档在两张未参与端环拟合的静态图上改善了末缘。第 150 帧的 RMS 从 8.91 升至 9.54 px。全量档第 120 帧增加了 3,323 个前景像素，其中 2,663 个在参考遮罩以外，2,608 个对应参考图中 RGB 最大通道为 1 到 18 的暗区。原亮度阈值和全部相机保持一致。几个视角仍能看到宽度、折边和导轨的差异。[半量视频边界](half/video-edges.png) · [半量静态边界](half/still-edges.png) · [全量视频边界](full/video-edges.png) · [新增前景](added-pixels.json)

两档均改动 72 件形体，120 项接合距离无退步，13 件支撑形体的对称差为零。半量档保存后无新增高级几何问题。全量档的第 8 号加强筋出现曲线上点与曲面不一致的高级检查错误，保留为诊断试验。三组整机均值均下降，正式模型采用 v315。[半量几何](half/geometry.json) · [全量问题](full/geometry.json) · [半量视频](half/video.json) · [半量静态](half/stills.json) · [半量拼图](half/sheet.json)

用 FreeCAD Python 执行 `tools/experiment_drone_petal_axial.py`，传入 v315 保存模型、重建网格和新输出目录，以及 `--construction tip-splice --station 99 --terminal-ring-fit cad/drone-concept/comparison/nozzle-mouth-fit.json --ring-fraction 0.5`。全量档用 1 替代 0.5。半量档用 `tools/finalize_drone_petal_axial.py` 打包。全量档用 `tools/restore_candidate_display.py` 恢复保存的 GUI 载荷后，从该 FCStd 导出诊断网格。[显示恢复](full/display.json)

使用 v315 三组固定相机和相同的支撑排除区域渲染。可见末端边界用 `tools/render_drone_object_ids.py` 和 `tools/compare_drone_visible_petal_edges.py` 重测。视频沿用 [v307 点集](../v307-nozzle-pair-6-10/video-observations.json)，静态使用 [五视角点集](../exit-profile-study/multiview-exit-fit.json) 的 still-04、still-05 两组参考像素。局部误差只覆盖已标注边缘。
