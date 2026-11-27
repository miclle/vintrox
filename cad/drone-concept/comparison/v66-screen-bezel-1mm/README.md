# v66 屏框外沿 1 mm 候选

本轮从正式 v61 复制保存模型，仅将 `ScreenBezel` 与 `BezelLip` 的外部视觉包络各收缩约 1 mm；实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根新增支柱、外挂筒、屏幕侧控件和格栅均保留。候选用于判断 v63 的 2 mm 屏框收缩是否过度，未修改正式 v61。

候选完成 FCStd 保存读回、STEP 独立读回和真实 CAD 网格绑定；对象级调色板按稳定对象名恢复为 74 个 RGB 三元组，候选顶点和面保持不变。证据位于 [candidate.FCStd](candidate.FCStd)、[candidate.step](candidate.step)、[candidate-check.json](candidate-check.json)、[视频渲染](video-renders/)、[视频比较](video-comparison/)、[七图渲染](still-renders/)、[七图比较](stills-comparison/) 和 [candidate-review.json](candidate-review.json)、[readback-verification.json](readback-verification.json) 和 [color-restoration.json](color-restoration.json)。

固定校准相机下，视频十方位平均轮廓 IoU 为 **85.481944%**，正式 v61 为 **85.492017%**，delta **−0.010072 个百分点**；静态七图平均轮廓 IoU 为 **82.243009%**，正式 v61 为 **82.226816%**，delta **+0.016189 个百分点**。视频整圈仍退步，候选保留为研究证据，正式模型继续采用 v61。

比较只使用真实 CAD 网格、固定相机、半透明叠加和差异图，没有图像拉伸、非刚性变形、逐部件对齐或删除可见部件。该候选是外观研究，不代表打印、装配、承力、声学、热、电气、光学或实物验收；参考曲面屏仍以透明外罩示意。
