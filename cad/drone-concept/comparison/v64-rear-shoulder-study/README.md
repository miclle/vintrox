# v64 后护甲截面候选

本轮在正式 v61（当前保存模型）基础上，仅改变 `RearArmourCheekLeft` 与 `RearArmourCheekRight` 的后护甲截面指数为 **1.25**；四根新增支柱、平面实测屏幕、外挂筒、屏幕侧控件和格栅均保留。候选由 `tools/experiment_drone_rear_shoulder_section.py` 从正式 FCStd 和当前保存网格重建，未修改正式模型。

候选证据：

- [候选 FCStd](candidate.FCStd)、[候选 STEP](candidate.step)、[候选网格绑定](meshes.json)
- [保存/STEP 读回检查](candidate-check.json)：698 个 FCStd 几何对象、1010 个实体，FCStd 与 STEP 均为有效闭合实体
- [视频十方位渲染](video-renders/)、[视频叠加与差异](video-comparison/)
- [七张静态渲染](still-renders/)、[静态叠加与差异](stills-comparison/)
- [彩色视频渲染与叠加](video-renders-color/)、[彩色七图渲染与叠加](still-renders-color/)

固定校准相机只做投影比较，没有图像拉伸、非刚性变形、逐部件对齐或删除可见部件。视频十方位平均轮廓 IoU 为 **85.489951%**，正式 v61 为 **85.492017%**；静态七图为 **82.259796%**，正式 v61 为 **82.226816%**。由于视频整圈略退步，候选保留为研究证据，正式模型继续采用 v61。

候选网格按稳定对象名恢复了正式外观研究的对象级颜色映射，共 74 个 RGB 颜色；颜色修复只改变渲染属性，不改变候选 FCStd 几何、顶点或比较掩码。

屏幕仍是实测 **210 × 160 × 2 mm** 平面输入；参考中的曲面屏只以透明外罩示意，不能从图片推断隐藏曲面或宣称光学一致。该候选只表示外观研究，不代表打印、装配、承力、声学、电气、热或实物验收。
