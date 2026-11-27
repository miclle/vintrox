# v69 底部回环半径 2.2 mm 候选

v69 只修改 `UnderbodyLoop0`、`UnderbodyLoop1` 的圆截面半径：3.5 mm → 2.2 mm；中心线、端点、四根 `SupportShaft`、`SupportSocket`、`SupportFoot`、`CentralSupportSeat` 和其余外观对象保持。测量平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm` 保持，参考曲面屏仍只是外观/透明罩假设。

候选已独立保存读回：698 个保存对象、696 个可见对象、1010 个 STEP solids；保存实体有效且闭合，保护支撑几何与正式 v61 相等。彩色网格为 696 个对象、74 个 RGB 三元组，顶点和面保持不变。哈希和细节见 [candidate-check.json](candidate-check.json)、[readback-verification.json](readback-verification.json)、[color-restoration.json](color-restoration.json) 和 [meshes.json](meshes.json)。

固定校准相机下，视频十方位平均轮廓 IoU 为 **85.553320%**，正式 v61 为 **85.492017%**，delta **+0.061303 个百分点**；静态七图为 **82.259620%**，正式 v61 为 **82.226816%**，delta **+0.032804 个百分点**。v69 在视频和静态均值上优于 v68，但仍未达到 90% 外观目标，改善仍是屏幕空间诊断证据。正式入口保持 v61，v69 作为当前更优研究候选保留。

比较使用真实 CAD 网格、固定相机、叠加和差异图，没有图像拉伸、非刚性变形、逐部件配准或删除可见零件。该候选不代表制造、装配、承力、声学、热、电气、打印或实物验收。

2026-11-04 补充：原候选由 headless FreeCAD 保存，**缺少 GUI 外观数据**；此前 74 色检查只覆盖网格，不能代表原生 FCStd 显示通过。新增 [candidate-display.FCStd](candidate-display.FCStd) 从正式 v61 恢复 2095 个 GUI 外观成员，原 `Document.xml` 和全部 BRep 字节保持不变，见 [修复报告](display-restoration.json)。原候选、STEP 和比较哈希保留；原生窗口目视检查尚未完成。
