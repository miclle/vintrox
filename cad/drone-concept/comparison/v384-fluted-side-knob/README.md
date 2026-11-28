# v384 右侧旋钮轴向沟纹

参考视频第 150、180、210 和 240 帧中，右侧旋钮的侧面可辨认连续轴向沟纹。以 v382 锥形旋钮为基准，在 12 mm 长的锥面上，从轴向 0.4 mm 至 11.5 mm 切出 36 道最大深度为 0.55 mm 的 V 形凹槽。槽数、深度与截面按图估计。端面的亮色指示线以及金属质感仍与参考有差异。三列依次为原视频、v382 和 v384，采用相同裁切区域。[四方位近景](knob.jpg) · [裁切位置](crop.json)

切除体积为 86.54 mm³。保存读回确认旋钮为单一有效闭合实体，旋钮底面与方向盘接触。FreeCAD 原生四视角核对了 696 个可见对象、71 种颜色，STEP 独立读回 869 个有效闭合实体。左右控件、外挂筒、格栅、四根支柱及实测平面屏均保留。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [几何记录](geometry.json) · [读回验证](readback-verification.json) · [原生视图](native-display/native-display-verification.json)

视频十方位、静态七图和拼图十格的平均 IoU 为 86.26723%、82.72225% 和 90.00226%。这次改动集中在旋钮表面。喷口末缘等主要部件仍超过 5% 偏差，视频整圈仍未达 90%。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)
