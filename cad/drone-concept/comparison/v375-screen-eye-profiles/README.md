# v375 平面屏眼睛轮廓

v371 的眼睛在正面参考帧中偏高、偏窄。v375 保留左右中心 X = ±33 mm，以第 270 帧描点反投影所得的对称阶梯轮廓重建四个眼睛图形对象。主体宽 15 mm，顶、底窄段宽 5.3 mm，总高 26.3 mm，墨色表面仍在 Y = −9.6 mm。实测面板尺寸 210 × 160 × 2 mm，可视区 200 × 150 mm。

复核沿用 v72 保存的三视角裁切框和绿色通道阈值 140、160、180。两眼在三个视角、三档阈值下的 18 项局部 IoU 均高于 v371。在阈值 140 下，正面左眼由 0.690 升至 0.775，右眼由 0.696 升至 0.922。两个斜视角仍有横向位置偏差，参考曲面罩的光学参数未知。[三方位近景](eyes.jpg) · [全部阈值与边缘误差](eye-edges.json)

视频十方位、静态七图、拼图十格整机平均 IoU 分别为 86.26715%、82.72213%、90.00205%，与 v371 一致。保存读回为 696 个可见对象，FCStd 与 STEP 各有 869 个有效闭合实体，体积相对误差 5.16 × 10⁻⁷。[几何核验](independent.json) · [原生四视角](native-display/native-display-verification.json)

在 FreeCAD Python 环境向本目录的 build.py 依次传入 v371 FCStd 和新输出路径。眼部局部测量调用 tools/compare_drone_expression.py 的 mask、metrics，逐项使用 v72 对应视角的 roi_px。

本版采用为正式评审模型。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [完整读回](readback-verification.json)
