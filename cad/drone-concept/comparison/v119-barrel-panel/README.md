# v119 红翼侧外挂筒控制面板

在 v115 的穿孔筒身上分开上方红按钮、黑色拨钮和下方弧形金框。金框内保留暗色内衬和中央滑块。调整四个对象，沿用 v115 的筒身、端盖、卷线、四支柱、实测平面屏、侧控件和格栅。参考中的端盖细节、文字和被遮挡的结构仍有差距。[四视角近景](barrel-panel-review.png)

四个已查阅的视频视角中，红按钮中心的采样 RMS 从 52.50 px 降至 6.73 px，黑拨钮从 18.33 px 降至 6.08 px。取点复核时修正了参考像素，以图中可见端面中心对照保存实体质心，所得距离用于评估控件位置。[点位及逐视角误差](panel-centers.json)

| 固定相机平均轮廓 IoU | v115 | v119 |
| --- | ---: | ---: |
| 视频十方位 | 85.8446100% | 85.8396528% |
| 静态七图 | 82.4302146% | 82.4299484% |
| 参考拼图十格 | 89.5914211% | 89.5826752% |

采用 v119 是基于四视角均可见的控件布局改善。三组整机均值略降，视频正后视回落约 0.048 个百分点。各组采用既有相机与分割，参考比较仅排除新增四支柱及其附件。整圈 90% 和主要部件轮廓偏差 5% 目标仍待达成。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [参考拼图](sheet-comparison/comparison-board.png)

五项设计搭接有正体积，四件变更网格与保存模型复算一致。独立检查确认 696 个可见对象、853 个闭合 STEP 实体，四支柱与实测屏幕通过复核。FreeCAD 原生四视图核对显示颜色和可见性。[几何与搭接](candidate-check.json) · [独立读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

本目录保存 v119 的三组相机、对照板和测试数据。重放这轮几何需另行准备与记录哈希匹配的 FCStd 和网格。`tools/drone_concept.py` 的 `barrel_panel_shapes` 生成面板实体，四件保存实体与生成函数的对称差集体积小于 10⁻⁶ mm³。[当前交付](../v120-barrel-rear-cap/README.md)
