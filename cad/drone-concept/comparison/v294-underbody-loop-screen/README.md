# v294 底部回环路径与截面筛选

从 v292 保存模型重建两条镜像回环。以 v277 路径为起点，沿 v278 解移动控制点，测试 30% 和 60% 的位移。两档分别采用 3.5 mm 和 4.5 mm 的中段半径。另用 60% 位移和原 2.2 mm 等径截面，检查仅改变路径的影响。四个路径端点和 2.2 mm 端部半径沿用 v292。[30% 参数](low/build-fit.json) · [60% 参数](mid/build-fit.json) · [等径参数](path/build-fit.json)

| 候选 | 视频十方位平均 IoU | 静态七图 | 拼图十格 |
| --- | ---: | ---: | ---: |
| v292 | 86.034597% | 82.587208% | 89.783549% |
| 30% 位移和 3.5 mm | 85.953898% | — | — |
| 60% 位移和 4.5 mm | 85.883403% | — | — |
| 60% 位移和 2.2 mm | 85.981846% | 82.555167% | 89.773231% |

等径档在三组固定相机对照中均有退步。第 120 帧左侧回环的最大采样偏差从投影屏宽的 9.15% 降至 4.84%，第 180 帧右侧则从 6.28% 升至 22.95%。第 180 帧有两个靠近小喷口的采样点与可见回环相距超过 38 px，两个点的 CAD 归因分别为小喷口外罩和底盘。后续拟合需要同时约束第 180 帧的可见边缘。正式评审采用 v292。[可见边缘近景](visible-loop-edges.png) · [逐点距离与遮挡](visible-loop-edges.json) · [视频](path/video-board.png) · [静态](path/stills-board.png) · [拼图](path/sheet-board.png)

三档均保存并重新打开两件闭合回环实体，端部仍与底壳搭接，和新增四支柱总成的体积交叠为零。保存包仅替换两个回环的 BRep。等径档从保存包重开后，两个回环的三角网格逐项复现，696 个可见对象与 70 组颜色匹配。候选停在外观筛选阶段，正式 STEP 和 FreeCAD 四视图校验见 v292。[30% 几何](low/candidate-check.json) · [60% 几何](mid/candidate-check.json) · [等径几何](path/candidate-check.json) · [正式交付](../../delivery-verification-current.json)

## 复现

将 v292 FCStd 和网格传给 `tools/experiment_drone_loop_path.py`，以该档的 `build-fit.json` 传给 `--fit`，并按表中半径设置 `--radius`，两端用 `--end-radius 2.2`。在 FreeCAD Python 运行该脚本后，用普通 Python 执行本目录的 `restore_display.py --base <v292 FCStd> --screen <候选目录>`。用生成的 `display.FCStd` 和更新的网格运行 Blender 渲染和对象 ID。三个相机文件沿用 v292。复测等径档局部边缘时，将 `display.FCStd` 复制为候选目录中的 `candidate.FCStd`，放入本目录的 `path-fit.json`，用该目录作为 `tools/compare_drone_visible_loop_edges.py` 的 `--candidate`，并指定 v292 模型和对象 ID 作为基线。[固定相机与网格](../v292-brow-shoulder-inset/README.md) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
