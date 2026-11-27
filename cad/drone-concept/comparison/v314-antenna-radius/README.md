# v314 天线截面半径

固定相机对象 ID 复测显示，v310 天线在五个视频方位的上段平均投影宽度比参考标注窄 5.89–7.00 px。沿用已保存的中心线，截面半径从 1.10 mm 增至 1.65 mm。候选为有效闭合实体，天线与底座保持零间隙，搭接体积从 3.80 增至 8.56 mm³。[基线测量](baseline-antenna.json) · [候选测量](antenna.json) · [几何报告](candidate-check.json)

| 固定相机 | v310 | v314 |
| --- | ---: | ---: |
| 视频十方位 | 86.184762% | 86.234544% |
| 静态七图 | 82.639128% | 82.601394% |
| 拼图十格 | 89.905496% | 89.964125% |

加粗后，五个视频方位上段平均宽度差降至 3.89–4.44 px。十个视频方位和十格拼图的 IoU 均提高，七张静态图均下降，其中第 05 图降幅为 0.08203 个百分点。参考上段标注可能包含高光，视频中天线尖端被裁切。正式版采用 v310。候选已导出 STEP，独立 STEP 读回及原生显示核验待执行。[视频](video-board.png) · [静态图](stills-board.png) · [拼图](sheet-board.png)

用 FreeCAD Python 运行本目录 `replay.py`，传入 v310 已保存的 FCStd、重建网格、`--fit fit.json --radius 1.65` 和空的输出目录。再将输出目录传给 `tools/finalize_drone_petal_axial.py --diagnostic`，以 v310 同时作为 `--base` 和 `--appearance-source`。三组渲染沿用 v310 固定相机。天线测量用对应的对象 ID 和 `tools/measure_drone_antenna_edges.py`。[v310 复现记录](../v310-right-wing-fold/README.md)
