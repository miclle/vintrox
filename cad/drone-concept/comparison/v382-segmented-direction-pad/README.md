# v382 左侧方向键分区

参考视频第 0、30、60 帧均能看到中央按钮周围的四个方向键。沿用 v381 的盘面外径和四个箭头，在盘面切出四条宽 1.5 mm、深 1.3 mm 的斜槽，并绕中央按钮切出内外半径为 8 和 10.3 mm 的环槽。槽的实际尺寸无法从参考画面直接测得。三列依次为参考、v381、v382。[局部对照](dial.jpg) · [裁切坐标](crop.json)

方向盘切除 216.38 mm³ 后仍为单一闭合实体。中央按钮与盘面接触，四个箭头与盘面的既有间距均为 0.2 mm。首次 STEP 导出包含两个隐藏对象，随后按 FCStd 保存的可见状态重新导出。正式 STEP 独立读回 869 个有效闭合实体。FreeCAD 四视角确认 696 个可见对象、71 种显示颜色。[FCStd](candidate.FCStd) · [间距](joints.json) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

固定相机的视频十方位、静态七图和拼图十格平均整机 IoU 分别为 86.26720%、82.72225%、90.00226%。本次变化集中在盘面内部，整圈轮廓与 v381 接近。四根支柱保留，实测平面屏本体为 210 × 160 × 2 mm，可视区为 200 × 150 mm。曲面罩及被遮挡的结构仍属外观假设。喷口末缘的部件偏差仍待解决。[视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png)

旧 STEP 已清理。可从本目录保存的 FCStd 按可见对象导出 STEP，原导出的哈希与实体检查保存在读回报告中。
