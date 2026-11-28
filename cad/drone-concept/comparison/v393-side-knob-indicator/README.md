# v393 右侧旋钮端面与指示线

原始视频第 150、180、210、240 帧中，深色沟纹旋钮的端面有一道由中心向边缘延伸的浅色短线。沿冻结相机，从第 180、210 帧的端面中心和短线两端共六个像点拟合三维位置。保存的旋钮端面中心位于 (134.77, 10.59, 164.01) mm，冲切槽内另放一件宽 0.90 mm 的圆端嵌件。深色圆底盘伸至侧壳。长短与颜色按参考外观估计，功能与涂层工艺待验证。[四方位近景](knob.jpg) · [逐帧像素坐标](measured.json)

未参与拟合的第 150、240 帧，端面中心投影偏差分别从 3.69 和 15.56 px 降至 0.81 和 1.17 px。对象 ID 渲染在四个方位均能识别嵌件。参考旋钮的亮边、表面高光及材质仍与模型有差异。[装配间隙](contacts.json) · [FCStd](candidate.FCStd) · [STEP](candidate.step)

| 固定相机平均轮廓 IoU | v392 | v393 |
| --- | ---: | ---: |
| 视频十方位 | 86.16465% | 86.17745% |
| 静态七图 | 82.67231% | 82.66787% |
| 拼图十格 | 90.01812% | 90.02961% |

本版采用四方位都可见的端面标记，静态七图降低约 0.00444 个百分点。四支柱、实测 210 × 160 × 2 mm 平面屏、外挂筒、十道侧格栅及左右控件均保留。参考曲面罩的光学特性与遮挡后的细节仍有未知项。喷口第 60 帧与右翼第 210 帧的采样偏差仍为投影屏宽的 8.42% 和 7.65%。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png) · [逐部件复测](visible-components.json)

FCStd 原生四视角读回确认 697 个可见对象、72 种颜色。STEP 独立读回得到 870 个有效闭合实体，体积相对误差约为 5.16 × 10⁻⁷。可在 FreeCAD GUI 中运行 replay.FCMacro，以 VINTROX_KNOB_BASE 指定 v392 FCStd，以 VINTROX_KNOB_OUTPUT 指定临时输出目录。恢复显示时沿用保存的模型颜色，网格由保存 FCStd 独立导出。[原生显示](native-display/native-display-verification.json) · [实体读回](readback-verification.json)
