# v44 侧后保护边框切口

采用候选 A 的左右保护边框修订。正式模型 SHA-256 为 `08e667f1a219b9b0758b2bdf9b13d6d6e34ae45c277bbcd859bf31a45c3703a8`，基线 v43 为 `d03080846462cd5b8318f6dea254456fe77ece6cda06349ba698ea010086d591`。这是局部外观修订，整体还原目标仍未完成。

## 问题与修改

侧后方状态板下缘原有多次避让裁切，留下尖角和约两级台阶；参考边缘连续斜收。对象 ID 核对将主要尖角定位到 `SideGuardRight`，相邻后壳边缘仍涉及 `SideClosureRight`。先前的 [后壳折转半径研究](../rear-fold-study/README.md)没有解决这一切口问题，未采用。

本轮仅修整左右两件保护边框，沿既有 X=108mm 平面，把固定视频第 180 帧的四个参考点反投影为真实 CAD 切口。左右对称、切口深度及隐藏接合属于外观假设；没有改变相机或变形图片。每侧移除约 336.009mm³ 的尖角材料，没有添加遮挡状态板的材料。

## 同角度证据与限制

[当前边界放大图](v44-guard-notch-check.png)列为参考、v43、v44；[候选四联图](a/notch-side.png)列为参考、v43、A、50% 叠加。测量读取保护边框、侧壳和后肩的**可见联合边界**，避免把被邻件挡住的私有切边当成显示效果。

四个观察点的 RMS 从 **8.888px 降至 6.225px**，最大偏差从 12.728 降至 12px。这些点参与构造，人工不确定度约 ±2px，不是独立验收。上方邻壳交界仍有约 12px 差异，后续需要联合修订相邻侧壳及凹口，而不是不断裁去保护边框。

十方位轮廓 IoU 保持 **84.84932%**，七图诊断均值保持 **81.94409%**，每一个视角均保持其原轮廓分数。此次修订改变的是内部可见边界，不以整机 IoU 声称局部细节已完全还原。全部视频和图片相机、材质设置、分割阈值、支柱排除范围保持；七图包含线框图。

[正式十方位](../iteration-78/comparison-board.png) · [正式七图](../stills-49/comparison-board.png) · [候选十方位](a/video/comparison-board.png) · [候选七图](a/stills/comparison-board.png) · [汇总与哈希](review.json)。

## 几何与保存

[局部源代码等价](source-equivalence.json)和[正式读回](formal-geometry-check.json)确认两件源代码、候选及保存实体的双向差集为零，均为单一闭合实体且通过高级 BOP 检查。六组与侧壳、后肩、灯带的接合间隙为零，四根支柱差集为零。状态板五个视角的 75 条观察线与外壳交集长度均为零，原有凹槽和背板探针仍通过。

[归档转移](archive-transfer.json)保留另外 696 个 BRep 文件及 GUI 状态，694 个可见网格、颜色和材质记录保持。[原生打开检查](native-open-check.json)通过，未再次保存；模型仍有 700 个顶层中文对象、696 个可见外观对象和 805 个 STEP 实体。

构建函数为 `tools/drone_guard_notch.py`，在 `tools/drone_concept.py` 侧板重建后使用；保存入口为 `tools/refine_drone_guard_notch.py`，源代码和保存实体核对为 `tools/measure_drone_guard_notch_geometry.py`。图像测量为 `tools/measure_drone_guard_notch.py`。候选构建源码与网格按哈希保留在本机任务缓存，路径见汇总。

既有其余 11 个翼板对象的高级 BOP 问题及完整 GUI 从头重建稳定性限制仍在。本轮不是制造、打印或实物验收，未提交或推送。

正式模型后续已推进至 [v45 内退斜边](../status-rim-study/README.md)；本研究的数值和归档图保持 v44。
