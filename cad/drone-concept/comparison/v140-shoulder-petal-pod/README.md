# v140 后肩、喷口叶片与小喷口内封片

v140 组合了 v135 的两件后护甲、v138 的 46 件大喷口叶片及末段细节，以及 v134 的两片小喷口内封片。以 v130 的同一组相机渲染保存模型，整机对照排除新增四支柱及其安装件。实测平面屏、参考曲面罩、外挂筒、屏幕侧控件和格栅均纳入渲染。当前外观入口为 v151。[v151 提手支臂](../v151-handle-arm-tilt/README.md)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% |
| v140 | 85.854104% | 82.472554% | 89.593124% |

三组整机均值均小幅增加。90% 视频整圈目标与主要部件完整轮廓偏差 5% 仍待达成。平面屏按实测尺寸保留，曲面罩和参考中被遮挡的结构属于外观推定。

保存读回确认 696 个可见对象、853 个有效闭合 STEP 实体、50 件变更网格与保存几何一致，以及四支柱几何一致。STEP 按实体分别积分后汇总，体积相对误差为 5.35×10⁻⁷。小喷口的 36 个端面和 328 项接合通过复核。FreeCAD 原生四视角确认 70 组显示颜色和原生可见性。[参数](candidate-check.json) · [读回](readback-verification.json) · [小喷口校验](terminal-contact-check.json) · [原生显示](native-display/native-display-verification.json)

v140 的 FCStd、STEP 和压缩网格已移出本地 `main` 历史。用恢复包和本机 LFS 缓存取回最终模型及网格后，使用本目录的三组 `cameras.json` 重放。复建几何时，从 v130 复建 v139 与 v134，以二者的最终试件目录作为本目录 `combine.py` 的两个来源，执行小喷口复核后用 `tools/finalize_drone_petal_axial.py` 恢复原生颜色及导出 STEP。[清理与恢复记录](../../../../docs/storage-cleanup.md) · [网格清单](mesh-archive.json) · [v130 重放流程](../v130-underbody-loop-path/README.md) · [v139 组合](../v139-shoulder-petal-combination/README.md) · [v134 内封片](../v134-small-pod-diaphragm/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
