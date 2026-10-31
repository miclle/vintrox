# v65 侧音箱外沿径向候选

本轮在正式 v61 保存模型基础上，尝试让左右侧音箱外沿沿径向收缩约 **2 mm**，观察参考图中的侧向音箱比例。直接对现有实体执行仿射变换的 `v65-speaker-radial096` 候选产生 `GeomAbs_C0` 的 BOP 错误，因此未进入比较；本目录采用解析重建方式，仅重建下列 12 个对象：

- `SpeakerOuterLipLeft` / `SpeakerOuterLipRight`
- `SpeakerLipTrimLeft` / `SpeakerLipTrimRight`
- `SpeakerSurroundLeft` / `SpeakerSurroundRight`
- `SpeakerCentreLeft` / `SpeakerCentreRight`
- `SpeakerHubNeckLeft` / `SpeakerHubNeckRight`
- `SpeakerVisualConeLeft` / `SpeakerVisualConeRight`

候选证据包括 [FCStd](candidate.FCStd)、[STEP](candidate.step)、[网格绑定](meshes.json)、[保存读回与实体检查](candidate-check.json)、[视频渲染](video-renders/)、[视频叠加与差异](video-comparison/)、[七图渲染](still-renders/) 和 [七图叠加与差异](stills-comparison/)。保存读回包含 **698 个几何对象**；STEP 读回包含 **1010 个实体**，12 个变化对象均为有效单实体。候选 FCStd SHA-256 为 `e86ca06d5234fa4b81c0bc8bbc5ce26bff974454f03c9bf68400a54d63e89645`，STEP SHA-256 为 `80bebc26d00a933c237e6c289bf3975c5e5f7f6dafc960aac97b32b1161253a7`。

在同一组固定校准相机下，视频十方位平均轮廓 IoU 为 **85.441017%**，正式 v61 为 **85.492017%**，delta **−0.051000 个百分点**；静态七图平均轮廓 IoU 为 **82.240457%**，正式 v61 为 **82.226816%**，delta **+0.013641 个百分点**。视频整圈退步，候选保留为研究失败证据，正式模型继续采用 v61。完整决定见 [candidate-review.json](candidate-review.json)。

渲染使用真实 CAD 网格、固定相机、半透明叠加和差异图；没有图像拉伸、非刚性变形、逐部件对齐或删除可见部件。四根支柱及其座脚、实测平面屏 **210 × 160 × 2 mm**、可视区 **200 × 150 mm**、左侧外挂筒、屏幕侧控件和格栅均保留。网格颜色按正式对象名映射恢复，共 74 个 RGB 变体；颜色只影响渲染属性，不改变 FCStd 几何或比较掩码。

该候选仍是外观研究证据，不代表打印、装配、承力、声学、热、电气、光学或实物验收。屏幕曲面继续仅以透明外罩示意，不能据此宣称真实曲面屏或光学一致。
