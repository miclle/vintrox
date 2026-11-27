# v307 大喷口第 6、10 号叶片末段

用 v306 保存几何筛选第 6、10 号镜像叶片。两档都保留根部、导向件和铰链，并复核保存模型的实体有效性、接合和 13 件支撑几何。改动形体分别为 12 件和 10 件。高级几何检查和接合均无新增失败。[105 mm 接续档](pair-6-10-inward/candidate-check.json) · [109.5 mm 接续档](pair-6-10-seam/candidate-check.json)

| 固定相机 | v306 | 105 mm 接续档 | 109.5 mm 接续档 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.181044% | 86.194075% | 86.195839% |
| 静态七图 | 82.638371% | 82.624285% | 82.623406% |
| 拼图十格 | 89.902265% | 89.922633% | 89.925364% |

109.5 mm 档在第 60、180 帧把叶片可见边界的采样 RMS 从 25.13、25.98 px 降到 23.06、24.02 px。两帧最大偏差仍为投影屏宽的 20.96% 和 21.94%。静态第 04 至 06 图均有回退，其中第 05 图下降 0.0512 个百分点，正式采用 v306。STEP 和 FreeCAD 原生颜色验证适用于已发布的 v306，本轮筛选止于保存几何和渲染。[局部边缘](pair-6-10-seam/visible-petal-edges.png) · [视频十方位](pair-6-10-seam/video-board.png) · [静态七图](pair-6-10-seam/stills-board.png) · [拼图十格](pair-6-10-seam/sheet-board.png)

在 FreeCAD Python 环境运行 `tools/experiment_drone_petal_axial.py`，向 `--base-model` 和 `--base-meshes` 传入 [v306 保存模型](../v306-wing-pose/README.md)及其重建网格，并指定空的 `--output`。两档共用 `--construction tip-splice --leaf-indices 6 10`。105 mm 档用 `--station 105 --factor 1.5 --tip-radial-shift -3.6`，109.5 mm 档用 `--station 109.5 --factor 1.65 --tip-radial-shift -2 --tip-centre-shift 2`。用保存模型和生成的网格运行 `tools/render_drone_concept.py` 与 `tools/compare_drone_reference.py`，沿用 v306 三组相机。局部误差用 `tools/render_drone_object_ids.py` 和 `tools/compare_drone_visible_petal_edges.py` 按同一组参考标注复测。[参考点](video-observations.json)
