# v310 右翼折面边缘

以 v306 保存 CAD 为基线，右翼折面外缘在第 210 帧有一处 7.62 px 偏差。绕轮毂的 v306 姿态继续用于重建。将局部 Y 方向第 14、15、16 站分别外移 2.8、3.8、1.0 mm，重建右翼包边、内彩色面、折面、抬高面和外彩色面。九项邻件距离检查通过。[保存几何](candidate-check.json) · [站位参数](crease-fit.json)

| 固定相机 | v306 | v310 |
| --- | ---: | ---: |
| 视频十方位 | 86.181044% | 86.184762% |
| 静态七图 | 82.638371% | 82.639128% |
| 拼图十格 | 89.902265% | 89.905496% |

第 210 帧折面外缘样点 `(643, 419)` 的偏差由 7.62 px 降到 2.00 px，右翼采样 RMS 从 4.13 px 降到 3.80 px。最大偏差仍为 7.65%，位于折面更高处。第 180 帧翼根复测保持 5.29%。静态第 05 图下降 0.00170 个百分点，第 03 图提高 0.00678 个百分点。参考曲面罩、实测平面屏及遮挡继续影响轮廓判读。[局部复测](visible-wing-edges.json) · [视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

全量站位方案的第 210 帧 RMS 降到 2.58 px，三组整机均值下降。联合调整折面与上段翼缘的方案将第 210 帧最大偏差降至 6.35%，静态七图平均 IoU 降至 82.6320%。带翼根下段调整的折面方案在第 180 帧把翼根最大偏差增至 6.08%。正式采用仅调整折面边缘的方案。[全量拟合](alternatives/full/visible-wing-edges.json) · [联合调整](alternatives/blend/visible-wing-edges.json) · [调整翼根的候选](alternatives/fold-with-root/visible-wing-edges.json)

实测屏幕、四根支柱、外挂筒、屏幕侧控件和格栅保留。FCStd 与 STEP 独立读回确认 696 个可见对象、853 个闭合 STEP 实体。独立导出的网格与渲染输入逐字节一致。FreeCAD 原生四视图验证了可见性和 70 组颜色。整圈 90% 和主要部件轮廓偏差 5% 仍待达到。[读回](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

用 FreeCAD Python 运行本目录的 `replay.py`，从 v306 传入 `--base`、`--mesh` 和 `--pose`，姿态文件为 v306 的 `half-angle.json`。使用 `--fit crease-fit.json --scale 1` 和新的 `--output`。用 `tools/finalize_drone_petal_axial.py` 生成含保存颜色的 FCStd、STEP 和网格，`--base` 与 `--appearance-source` 均指向 v306 的 FCStd。三组渲染沿用各自的 `cameras.json`，局部复测用 `tools/compare_drone_visible_wing_edges.py` 和本目录的 `observations.json`。全量拟合档使用 `fit.json` 与 `--scale 1`，半量拟合档用 `--scale .5`。[v306 重建网格](../v306-wing-pose/README.md)
