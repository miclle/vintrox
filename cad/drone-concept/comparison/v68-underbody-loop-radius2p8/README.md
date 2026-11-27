# v68 底部回环半径 2.8 mm 候选

v68 只修改 `UnderbodyLoop0`、`UnderbodyLoop1` 的圆截面半径：3.5 mm → 2.8 mm；中心线、端点、四根 `SupportShaft`、`SupportSocket`、`SupportFoot`、`CentralSupportSeat` 和其余外观对象保持。测量平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm` 保持，参考曲面屏仍只是外观/透明罩假设。

候选已独立保存读回：698 个保存对象、696 个可见对象、1010 个 STEP solids；保存实体有效且闭合，保护支撑几何与正式 v61 相等。彩色网格为 696 个对象、74 个 RGB 三元组，顶点和面保持不变。哈希和细节见 [candidate-check.json](candidate-check.json)、[readback-verification.json](readback-verification.json)、[color-restoration.json](color-restoration.json) 和 [meshes.json](meshes.json)。

固定校准相机下，视频十方位平均轮廓 IoU 为 **85.524160%**，正式 v61 为 **85.492017%**，delta **+0.032144 个百分点**；静态七图为 **82.243173%**，正式 v61 为 **82.226816%**，delta **+0.016358 个百分点**。这只是屏幕空间外观诊断，不能证明制造、装配、承力、声学、热、电气、打印或实物验收。正式入口仍保持 v61，v68 作为研究候选保留。

比较使用真实 CAD 网格、固定相机、叠加和差异图，没有图像拉伸、非刚性变形、逐部件配准或删除可见零件。
