# v371 沿提手臂截面裁切握把端箍

在 v369 上构造 v370 的端箍后，分别取左右提手臂距中面 112 mm 处的截面，向内拉伸 23 mm，以截面包络裁切新增实体，再与原端箍融合。两个端箍通过 FreeCAD 高级形体检查，仍分别与同侧包覆带、提手臂和握把芯搭接。[建模差异](clip-arm-section.diff) · [接合体积](contact.json)

第 180 帧可见 v370 突出的圆角已收回，但侧面接缝仍较参考明显。正后方两端上缘的平均垂直偏差分别为 1.08 和 0.97 px，第 150 帧为 0.84 px，第 180 帧为 1.94 px。v370 相应结果为 0.78、0.70、0.63 和 1.94 px。[三方位近景](cuff-comparison.jpg) · [固定列测量](top-edges.json)

| 平均轮廓 IoU | v369 | v370 | v371 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.24539% | 86.22357% | 86.26680% |
| 静态七图 | 82.71694% | 82.72807% | 82.72207% |
| 拼图十格 | 89.98364% | 89.98908% | 90.00205% |

保留 v371 为整机研究基线。视频十方位距 90% 仍有 3.733 个百分点，主要部件偏差仍需验证和改进。FCStd 与 STEP 各有 869 个有效闭合实体，696 个可见对象在原生四视角中与网格对应，共 70 种显示颜色。[几何检查](independent.json) · [原生显示](native-display/native-display-verification.json) · [视频](video-overlays.jpg) · [静态](stills-overlays.jpg) · [拼图](sheet-overlays.jpg)

## 正式评审交付

正式网格从保存模型与概念清单重建，使用清单中的喷口文字位置、大小和方向。视频十方位、静态七图、拼图十格的平均 IoU 分别为 86.26715%、82.72213%、90.00205%。上表保留筛选阶段使用渲染器默认文字位置的结果。四根支柱和实测平面屏已通过正式几何检查，隐藏部分与曲面屏罩仍属外观推导。[完整读回](readback-verification.json) · [视频](video-comparison/comparison-report.json) · [静态](stills-comparison/comparison-report.json) · [拼图](sheet-comparison/comparison-report.json)

[FCStd](candidate.FCStd) 作为 v375 的复建输入保留。旧 STEP 已清理，独立读回结果见本目录的验证记录。FCStd 的 SHA-256 为 `cd42c6185d80546b6c53465b4071bc7c14afd941644f92734fbfc1c21f327900`。按参数重建时，复制 [v370 脚本](../v370-grip-end-cuffs/build.py)，应用本目录的截面裁切差异，并传入 v369 FCStd 和新的输出路径。
