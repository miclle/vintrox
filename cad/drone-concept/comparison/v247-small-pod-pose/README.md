# v247 小喷口镜像姿态试验

v242 的固定相机近景显示，前罩内衬被像素统计归为轮廓外的区域大多落在参考图仍可辨认的暗色内衬上。小喷口的归因区域也包含开口后侧暗面和叶片表面。包围这些区域的亮边可用来辨认实际轮廓。本轮沿用原参考分割，对小喷口做姿态试验。[六处近景](v242-contour-detail.png) · [原对象归因](../v242-belly-y097/video-comparison/boundary-regions.json)

将两侧各 76 件小喷口实体绕各自壳体根部做镜像刚体调整。右侧位移为 `(0.91849, −1.5, −0.32625) mm`，旋转向量为 `(1.5, 1.5, 0.71169)°`，左侧镜像。参数来自外罩口环与叶片端缘既有标注的有界拟合。保存读回中，152 件改动均保持有效闭合实体，未新增高级几何错误或支撑搭接，壳体和夹座仍与主壳、底盘与底壳搭接。首轮保存使未改动零件的部分 BRep 被重新序列化，最终候选复测前已恢复 798 个原始几何成员以及 2,095 个颜色和显示成员。[几何读回](candidate-check.json) · [显示数据](display-restore.json)

| 测量 | v242 | v247 |
| --- | ---: | ---: |
| 外罩口环的拟合标注 RMS | 11.19 px | 9.17 px |
| 叶片末端四个拟合视角 RMS | 4.53 px | 5.03 px |
| 叶片末端两个未参与拟合视角 RMS | 7.38 px | 5.42 px |
| 视频十方位平均 IoU | 85.92521% | 85.91483% |
| 静态七图平均 IoU | 82.53726% | 82.50952% |
| 拼图十格平均 IoU | 89.67199% | 89.66247% |

两个未参与拟合视角的叶片末端最大偏差由 12.62 px 降至 10.26 px。口环测量使用标注到投影圆心线的最近距离，叶片末端测量使用保存外端圆弧，两个测量均只覆盖已标注区域。整机三组 IoU 均下降，正式交付采用 v242。v247 的 STEP 独立读回与 FreeCAD 原生视图验证未开展。[口环采样](shell-lip-measurement.json) · [叶片末端复查](lower-pod-outline-check.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

## 复现

用 FreeCAD Python 执行 `tools/experiment_drone_small_pod_pose.py --base cad/drone-concept/vintrox-drone-concept.FCStd --output <新目录> --offset .91849 -1.5 -.32625 --rotation-vector 1.5 1.5 .71169`。以 v242 为显示来源运行 `tools/restore_candidate_display.py`，用 `tools/export_candidate_drone_meshes.py` 从恢复显示的候选重建网格。沿用 v242 视频、静态图和拼图三组 `cameras.json` 作全模型渲染、叠加和差异比较。以 `tools/measure_drone_lower_pod_outline.py --model <候选.FCStd> --output <报告路径>` 复测叶片端缘。外罩口环用 `tools/fit_drone_lower_pod_rim.py` 的标注，测量至保存环体主圆在固定相机下的投影。[v242 输入与相机](../v242-belly-y097/README.md)
