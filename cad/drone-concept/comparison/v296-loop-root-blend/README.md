# v296 底部回环根部与遮挡核对

沿视频第 180 帧的 18 个标注点发射固定相机射线，读取保存 CAD 的真实三角网格。v295 的像素 (311, 657) 先击中小喷口外罩，回环在其后 52.00 mm。像素 (322, 657) 先击中底盘，射线未经过回环。两处都能影响可见边缘，但分别涉及遮挡和投影位置。[v292 射线](v292-rays.json) · [v295 射线](v295-rays.json) · [射线脚本](trace_loop.py)

v296 用 v292 的前段控制点，将后段按各控制点权重向 v295 路径混合。中段和端部半径分别取 3.5 和 2.2 mm。保存读回确认两根回环闭合、端部与底壳搭接、与四支柱总成的体积交叠为零。[控制点和权重](path-fit.json) · [几何复核](candidate-check.json)

第 180 帧的最大采样偏差回到投影屏宽的 6.28%，与 v292 相同，第 120 帧左侧为 4.77%。未用于拟合的第 150 帧右侧由 v292 的 5.94% 升至 7.18%。十方位平均 IoU 为 85.943261%，低于正式 v292 的 86.034597%。正式交付采用 v292。[视频十方位对照](video-board.png) · [可见边缘](visible-loop-edges.png) · [第 150 帧数据](holdout-edges.json) · [v296 射线](v296-rays.json)

按 v294 的保存、显示恢复和渲染流程，将本目录 `path-fit.json` 与 `--radius 3.5 --end-radius 2.2` 传给候选建模脚本。用 Blender 后台运行本目录 `trace_loop.py`，分别传入 `--model`、`--mesh`、v292 的视频 `--cameras`、v295 的 `--samples path-fit.json` 和 `--output`。射线报告区分视线先击中的对象和被挡住的回环。[候选复建](../v294-underbody-loop-screen/README.md) · [射线输入标注](../v295-loop-multiview-fit/path-fit.json)
