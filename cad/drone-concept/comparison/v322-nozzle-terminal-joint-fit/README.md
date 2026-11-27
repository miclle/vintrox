# v322 大喷口叶片末段联合拟合

以 v315 的保存末缘作为输入，沿用七个已标注的固定相机视角。对局部 Z=109.5 mm 接续面之后的叶片末段，联合拟合轴向延展、径向和局部 Y 位移。拟合的轴向因子触及 2.0 上限，径向和局部 Y 分别每 17 mm 移动 9.69 mm 和 4.60 mm。随后在第 5 至 11 号叶片的 38 件形体上重放这组参数。保存实体和接合检查通过，13 件支撑构件通过保护检查。[拟合参数](hem-fit.json) · [候选几何](candidate-check.json)

由保存模型三角化并渲染，十方位视频平均 IoU 从 86.204590% 降至 85.976458%。原标注点到实际可见叶片边缘的 RMS 在第 120 帧由 22.93 px 降至 9.85 px，在第 150 帧由 8.91 px 升至 12.38 px。标注覆盖部分可见边缘，并包含遮挡边。此档止于视频筛选，正式评审沿用 v315。[十方位对照](video-comparison/comparison-board.png) · [末缘近景](visible-petal-edges.png) · [逐点距离](visible-petal-edges.json)

复现时以 [v315](../v315-antenna-multiview/README.md) 为基线。使用 FreeCAD Python 运行 `tools/fit_drone_saved_petal_extension.py --joint --station 109.5`，再用 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 109.5 --factor 2 --tip-radial-shift 9.6878565 --tip-centre-shift 4.6030411 --leaf-indices 5 6 7 8 9 10 11` 生成真实 CAD。用 `tools/restore_candidate_display.py` 恢复 v315 的显示载荷，随后从保存候选重新导出网格。沿用本页相机和 [v307 标注](../v307-nozzle-pair-6-10/video-observations.json) 重放视频和可见末缘比较。候选和网格可再生成。[显示载荷核验](display-repair.json)
