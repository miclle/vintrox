# v381 平面屏表情颜色

参考视频中两眼与嘴部呈深绿色。将五个已保存的表情对象的漫反射 RGB 从 (11, 16, 17) 调至 (13, 70, 8)。FCStd 中的变化限于五个 ShapeAppearance 材质载荷。屏幕本体为 210 × 160 × 2 mm，可视区为 200 × 150 mm，曲面透明罩的光学参数仍属外观假设。[v375 几何基线](../v375-screen-eye-profiles/candidate.FCStd) · [共用 STEP](../v375-screen-eye-profiles/candidate.step)

在第 0、240、270 帧沿用 v72 的两眼和嘴部裁切框。逐幅取绿色通道低于 140、内缩 3 px 后的最大连通区域，比较该区域 RGB 中位数与参考的欧氏距离。九处色差均下降，平均值由 45.67 降至 25.02（8 位 RGB 单位）。正面两眼仍受高光影响。该测量使用渲染像素，不能替代实物屏幕测色。[三方位近景](ink.jpg) · [逐处中位数，依次为参考、v375、v381](ink-rgb.json)

保存文件在 FreeCAD 原生四视角读回 696 个可见对象、71 种颜色。两版的几何成员逐字节相同，沿用 v375 的几何 STEP，并对照 v381 FCStd 重新读回 869 个有效闭合实体。四支柱、外挂筒、屏幕侧控件及格栅均保留。[原生显示](native-display/native-display-verification.json) · [读回](readback-verification.json)

视频十方位、静态七图、拼图十格的整机平均 IoU 分别为 86.26715%、82.72213%、90.00205%。第 180 帧喷口末缘历史采样最大偏差仍为投影屏宽的 21.94%。本版更新屏幕配色，轮廓目标仍待完成。[视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png) · [同一几何的部件测量](../v375-screen-eye-profiles/visible-components.json)

归档时已核对 v381 STEP 与 v375 完全相同。v381 FCStd 可从 v375 按 concept-manifest.json 的 screen_ink_v381 记录复建，按原 ZIP 成员顺序和元数据复制归档，仅把对应五个 ShapeAppearance 材质载荷从偏移 8 起的四字节设为十六进制 FF 08 46 0D。复建文件的 SHA-256 与原读回报告完整匹配。当前正式模型和原生视图见[现行交付](../v384-fluted-side-knob/README.md)。
