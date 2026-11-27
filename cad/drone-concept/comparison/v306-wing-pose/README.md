# v306 翼板姿态

从 v304 保存模型出发，绕各侧轮毂中心转动翼板及其细节，共 18 件。采用半角度档，绕全局 X 轴旋转 −0.14011°，随后绕 Y 轴镜像旋转 ±0.47047°。四处翼根和轮毂接合距离通过复核，实测 210 × 160 × 2 mm 平面屏、外挂筒、侧控件、格栅和四根支柱保留。曲面罩和基于遮挡推定的形体仍有待核对。[保存几何与接合](candidate-check.json) · [半角度参数](half-angle.json)

| 固定相机 | v304 | v306 全角度档 | v306 半角度档 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.064428% | 86.137990% | 86.181044% |
| 静态七图 | 82.592259% | 82.637737% | 82.638371% |
| 拼图十格 | 89.839082% | 89.838149% | 89.902265% |

采用半角度档。视频第 120 帧提高 0.63318 个百分点，第 60 帧下降 0.07779 个百分点。静态第 01 图下降 0.26592 个百分点，第 02、03 图和近景各提高超过 0.23 个百分点。相机、参考区域和新增支撑总成排除规则沿用 v304。渲染来自保存的 CAD 网格，保留半透明叠加、轮廓差异和逐视角报告。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

左翼标注的最大偏差从投影屏宽的 4.69% 降至 4.10%，右翼从 8.10% 降至 7.65%。两处未参与拟合的翼根观测保持 5.29% 和 3.55%。观察只覆盖标注的可见边缘，包含部分遮挡边。视频全圈 90% 和主要部件轮廓偏差 5% 仍待达成。[可见翼缘](visible-wing-edges.png) · [逐点测量](visible-wing-edges.json) · [全角度档](full-angle/visible-wing-edges.json)

FCStd 和 STEP 独立读回确认 696 个可见对象和 853 个闭合 STEP 实体。重新打开保存模型生成的网格与渲染输入逐字节一致。FreeCAD 四个原生视图核对了可见性和 70 组颜色。九张预览和 12 秒转台来自同一保存模型。[读回](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

## 重放

在 FreeCAD Python 环境中从 [v304 保存模型](../v304-front-cheek-thickness/README.md) 重建网格。用 `tools/experiment_drone_wing_pose.py` 传入 `--base-model`、`--base-meshes`、`--fit half-angle.json` 和新目录 `--output`。将诊断目录传给 `tools/finalize_drone_petal_axial.py --diagnostic`，用 v304 FCStd 同时作为 `--base` 和 `--appearance-source`，并指定新的 `--output`，生成保留颜色的 FCStd、STEP 和网格。全角度档用 `full-angle.json` 重放。三组对照沿用各自目录中的 `cameras.json`。
