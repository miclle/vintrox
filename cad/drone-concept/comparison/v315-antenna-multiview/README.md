# v315 天线多视角中心线

v314 将天线半径增至 1.65 mm 后，五个视频方位的上段宽度差缩小，静态图仍有偏差。静态近景显示多处源天线与 CAD 投影之间有横向偏移，部分视角还存在遮挡和裁切差异。v315 保留 1.65 mm 半径，用五个视频方位和六张静态图的上段标注共同拟合中心线，模型控制点延至 Z=395 mm。真实尖端高度仍未知。各视角使用 v310 相机。[静态差异近景](static-antenna-crops.png) · [拟合记录](joint-fit.json) · [保存几何](candidate-check.json)

| 固定相机 | v310 | v314 | v315 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.184762% | 86.234544% | 86.204590% |
| 静态七图 | 82.639128% | 82.601394% | 82.687714% |
| 拼图十格 | 89.905496% | 89.964125% | 89.958234% |

v315 三组平均 IoU 均高于 v310。静态第 04 图提高 0.15986 个百分点，视频第 210 帧下降 0.14749 个百分点。按标注估计，静态第 04 图上段中心线 RMS 从 9.43 px 降到 5.58 px，第 03 图仍有 11.53 px。中心线拟合覆盖人工标注行，完整天线轮廓仍待复测。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

保存 FCStd 与 STEP 独立读回确认 696 个可见对象和 853 个闭合 STEP 实体。实测平面屏、四根支柱、外挂筒、侧控件和格栅均保留。重建网格与渲染输入逐字节一致，FreeCAD 原生四视图核对可见性和 70 组颜色。视频整圈 90% 与主要部件轮廓偏差 5% 仍待达成。[独立读回](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json)

运行 `fit_joint.py --output <临时参数文件>` 可复算参数。用 [v314 重放脚本](../v314-antenna-radius/replay.py) 读取 v310 保存模型、重建网格和 `--fit joint-fit.json --radius 1.65`。用 `tools/finalize_drone_petal_axial.py` 导出保留显示属性的 FCStd、STEP 和网格。沿本目录三组 `cameras.json` 重放固定相机渲染与对照。[v310 输入](../v310-right-wing-fold/README.md)
