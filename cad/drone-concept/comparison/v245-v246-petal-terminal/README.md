# v245 与 v246 喷口叶片末段试验

两次试验从 v242 的保存 FCStd 出发，保留叶片根部，在指定局部 Z 位置接续末段，并沿喷口局部 Y 方向逐渐偏移。三组对照使用 v242 的固定相机与分割规则。

| 版本 | 接续位置 Z（mm） | 轴向倍数 | 每 17 mm 原跨度的 Y 偏移（mm） | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| v242 | — | — | — | 85.92521% | 82.53726% | 89.67199% |
| v245 | 104.0 | 1.35 | 3.0 | 85.93272% | 82.51860% | 89.73367% |
| v246 | 109.5 | 1.25 | 1.5 | 85.93432% | 82.53171% | 89.70289% |

v245 在 7 个已标注视角中的 6 个降低了叶片末端采样 RMS。`video-02` 和 `video-06` 的最大采样偏差分别从投影屏宽的 20.96% 和 21.94% 降至 16.51% 和 18.25%。`video-05` 的最大偏差从 4.83% 升至 5.44%。保存读回复查发现 `NozzlePetal0`、`NozzlePetal4` 和 `NozzlePetalRidge7` 新增高级几何检查失败。120 项接合检查没有退步，13 件支撑实体差集为零。[几何报告](v245/candidate-check.json) · [叶片对照](v245/visible-petal-edges.png) · [逐点报告](v245/visible-petal-edges.json)

v246 的 56 件改动通过保存读回高级几何检查，104 项接合检查没有退步，13 件支撑实体差集为零。`video-02` 和 `video-06` 的最大采样偏差分别降至 19.61% 和 20.89%。七个视角中有六个仍超过 5%，静态七图平均 IoU 略低于 v242。正式交付采用 v242。v246 的 STEP 独立读回与原生颜色显示待验证。[几何报告](v246/candidate-check.json) · [叶片对照](v246/visible-petal-edges.png) · [逐点报告](v246/visible-petal-edges.json)

| 版本 | 视频 | 静态图 | 拼图 |
| --- | --- | --- | --- |
| v245 | [对照板](v245/video-comparison/comparison-board.png) · [报告](v245/video-comparison/comparison-report.json) | [对照板](v245/stills-comparison/comparison-board.png) · [报告](v245/stills-comparison/comparison-report.json) | [对照板](v245/sheet-comparison/comparison-board.png) · [报告](v245/sheet-comparison/comparison-report.json) |
| v246 | [对照板](v246/video-comparison/comparison-board.png) · [报告](v246/video-comparison/comparison-report.json) | [对照板](v246/stills-comparison/comparison-board.png) · [报告](v246/stills-comparison/comparison-report.json) | [对照板](v246/sheet-comparison/comparison-board.png) · [报告](v246/sheet-comparison/comparison-report.json) |

## 复现

按正式交付文档导出 v242 网格，在 FreeCAD 附带的 Python 中运行 `tools/experiment_drone_petal_axial.py`，传入 `--base-model`、`--base-meshes` 和新建的 `--output` 目录。v245 使用 `--construction tip-splice --station 104 --factor 1.35 --tip-centre-shift 3`，v246 使用 `--construction tip-splice --station 109.5 --factor 1.25 --tip-centre-shift 1.5`。候选 FCStd 和中间网格可用这些参数在临时目录重建。[正式网格导出](../../../../docs/drone-concept.md#编辑与复现)

用 v242 的视频、静态和拼图相机重跑渲染与叠加，再按 v244 的对象 ID 流程重算七视角的局部偏差。最近边缘可能来自遮挡边沿。两侧侧后视角的投影屏幕较窄，应同时查看像素距离和归一化偏差。[v242 相机与基线](../v242-belly-y097/README.md) · [对象 ID 与局部测量](../v244-petal-terminal/README.md#复现)
