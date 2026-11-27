# v317 大喷口叶片与总成姿态筛选

从 v315 保存模型出发，将 v316 的第 5、11 号档和第 6、10 号的末段内收组合。第 6、10 号使用局部 Z=109.5 mm 接续面，轴向放大至 1.65 倍，每 17 mm 原跨度径向内移 2 mm、局部 Y 偏移 2 mm。进一步从局部 Z=112 mm 起收窄第 6、10 号的切向外缘。另从同一 v315 基线绕大喷口根部筛选总成姿态，旋转 1° 通过接合复核。旋转 2° 时后套环与后导轨座分离 0.079 mm，止于几何检查。[组合几何](combined/candidate-check.json) · [收窄几何](combined-trim/candidate-check.json) · [1° 几何](pose-one/candidate-check.json) · [2° 接合记录](angular-2-contact-failure.json)

| 固定相机 | v315 | 叶片组合 | 组合后收窄 | 总成旋转 1° |
| --- | ---: | ---: | ---: | ---: |
| 视频十方位 | 86.204590% | 86.215610% | 86.205511% | 86.211470% |
| 静态七图 | 82.687714% | 82.668897% | 82.676043% | 82.684296% |
| 拼图十格 | 89.958234% | 89.983423% | 89.964667% | 89.967360% |

叶片组合把第 60、180 帧的采样 RMS 从 25.13、25.98 px 降到 21.21、23.19 px，最大偏差仍为屏宽的 18.94% 和 20.68%。进一步收窄让静态第 05 图相对 v315 的降幅从 0.07829 缩至 0.05378 个百分点。三档静态七图均值仍低于 v315，正式评审沿用 v315。[侧后视逐点测量](combined/visible-petal-edges.json) · [视频](combined/video-board.png) · [静态图](combined-trim/stills-board.png) · [拼图](combined/sheet-board.png)

复建叶片组合时先按 [v316 复建流程](../v316-nozzle-terminal-inset/README.md)生成第 5、11 号档，再用该档 FCStd 与网格运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 1.65 --tip-radial-shift -2 --tip-centre-shift 2 --leaf-indices 6 10`。末缘收窄沿用 [v308 切削流程](../v308-nozzle-outer-flank/README.md)。总成姿态试验从 v315 运行 `tools/experiment_drone_nozzle_pose.py --angle 1`，再用 `tools/finalize_drone_petal_axial.py` 生成保留显示数据的 FCStd、STEP 和网格。渲染与轮廓复测沿用 v315 固定相机。[v315 输入](../v315-antenna-multiview/README.md)
