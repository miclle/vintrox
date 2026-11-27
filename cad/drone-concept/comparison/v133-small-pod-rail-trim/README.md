# v131–v133 小喷口压条与脊条

以保存的 v130 为基线，在小喷口局部 Z=35.5 mm 收短两侧 108 件压条与脊条的根部。v131 只处理根部。v132 尝试将两类饰条一并截至 Z=50.5 mm，36 条中央脊条与叶片的间隙从零增至约 0.56 mm，试件止于接合检查。v133 仅将两侧压条截至 Z=50.5 mm，中央脊条保有末端搭接。壳体、口环、主叶片、实测平面屏和四支柱均从保存基线读回。[四视角近景](pod-closeups.png) · [v132 接合报告](v132/terminal-contact-check.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% |
| v131 | 85.852696% | 82.442843% | 89.589450% |
| v133 | 85.854726% | 82.445432% | 89.590868% |

v133 的十方位外侧差异中，归属侧压条的像素由 2,756 降至 1,992，归属主叶片的像素由 11,086 增至 11,679。小喷口相关零件合计由 25,175 降至 25,039。四组口沿和四组回环边缘采样距离均相同。近景仍可见主叶片末边及亮边形状差异，正式外观继续采用 v130。参考暗色材料与背景的分割存在不确定性，像素归属按固定相机和原分割规则计算。[区域差异](video-ids/boundary-regions.json) · [局部采样](visible-pod-loop-edges.json)

v131 与 v133 均通过 36 个叶片端面、328 项接合、853 个有效闭合 STEP 实体和 108 件变更网格读回。FreeCAD 原生四视图确认 696 个可见对象、70 组颜色和保存可见性。保存的四支柱形体一致。[v133 保存端面与接合](terminal-contact-check.json) · [STEP 与实体读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

复建使用 v130 的保存 FCStd 和解压网格。以 `tools/experiment_drone_pod_detail_roots.py --root-z 35.5` 生成根部试件，加入 `--rail-tip-z 50.5` 生成 v133。先运行 `tools/verify_drone_lower_pod_lip.py`，再将其报告传给 `tools/finalize_drone_petal_axial.py --verification` 恢复原生颜色并导出 STEP。以保存的试件和网格重放 v130 的三组相机。局部采样沿用 v83 的口沿标注和 v82 的回环标注。[v130 输入与重放](../v130-underbody-loop-path/README.md) · [v83 标注](../v83-small-pod-lip/lip-fit.json)
