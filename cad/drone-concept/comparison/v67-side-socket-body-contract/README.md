# v67 侧上方圆口座体收形候选

本候选仅修改 `SideSocketBaseLeft` 与 `SideSocketBaseRight`：外部径向包络收缩到四个固定视角推定轮廓的 92%，保留口沿、孔口和凹座。正式 v61、测量平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、中心座、外挂筒、侧控件和格栅均保持。

候选已完成 FCStd 保存读回和 STEP 独立读回：698 个可见对象、1008 个 STEP solids，保存实体有效，保护支柱/中心座与正式 v61 相等。彩色网格按稳定对象名恢复正式对象级调色板，共 74 个 RGB 三元组；恢复过程保持候选顶点和面不变。证据见 [candidate.FCStd](candidate.FCStd)、[candidate.step](candidate.step)、[candidate-check.json](candidate-check.json)、[readback-verification.json](readback-verification.json)、[color-restoration.json](color-restoration.json) 和 [meshes.json](meshes.json)。

同一固定校准相机下，视频十方位平均轮廓 IoU 为 **85.492505%**，正式 v61 为 **85.492017%**，delta **+0.000488 个百分点**；静态七图为 **82.226864%**，正式 v61 为 **82.226816%**，delta **+0.000049 个百分点**。增益处于三角化和渲染噪声量级，不能视为可重复的整圈改善，正式模型继续采用 v61。

比较使用真实 CAD 网格、固定相机、半透明叠加和差异图，没有图像拉伸、非刚性变形、逐部件对齐或删除可见部件。该候选是外观研究，不代表打印、装配、承力、声学、热、电气、光学或实物验收；参考曲面屏仍以透明外罩示意。
