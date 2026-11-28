# v371 沿提手臂截面裁切握把端箍

在 v369 上构造 v370 的端箍后，分别取左右提手臂距中面 112 mm 处的截面，向内拉伸 23 mm，以截面包络裁切新增实体，再与原端箍融合。两个端箍通过 FreeCAD 高级形体检查，仍分别与同侧包覆带、提手臂和握把芯搭接。[建模差异](clip-arm-section.diff) · [接合体积](contact.json)

第 180 帧可见 v370 突出的圆角已收回，但侧面接缝仍较参考明显。正后方两端上缘的平均垂直偏差分别为 1.08 和 0.97 px，第 150 帧为 0.84 px，第 180 帧为 1.94 px。v370 相应结果为 0.78、0.70、0.63 和 1.94 px。[三方位近景](cuff-comparison.jpg) · [固定列测量](top-edges.json)

| 平均轮廓 IoU | v369 | v370 | v371 |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.24539% | 86.22357% | 86.26680% |
| 静态七图 | 82.71694% | 82.72807% | 82.72207% |
| 拼图十格 | 89.98364% | 89.98908% | 90.00205% |

保留 v371 为整机研究基线。视频十方位距 90% 仍有 3.733 个百分点，主要部件偏差仍需验证和改进。FCStd 与 STEP 各有 869 个有效闭合实体，696 个可见对象在原生四视角中与网格对应，共 70 种显示颜色。[几何检查](independent.json) · [原生显示](native/native-display-verification.json) · [视频](video-overlays.jpg) · [静态](stills-overlays.jpg) · [拼图](sheet-overlays.jpg)

在仓库根目录用普通 Git 恢复此次读回和渲染使用的完整 FCStd。重建结果已逐字节核对。

```sh
research_dir=$(mktemp -d)
cp cad/drone-concept/comparison/v345-small-pod-y-minus1p0-cable/candidate.FCStd "$research_dir/"
gzip -dc cad/drone-concept/comparison/v371-grip-arm-profile/from-v345.patch.gz | (cd "$research_dir" && git apply --binary -)
shasum -a 256 "$research_dir/candidate.FCStd"
```

FCStd 的 SHA-256 为 `cd42c6185d80546b6c53465b4071bc7c14afd941644f92734fbfc1c21f327900`。按参数重建时，复制 [v370 脚本](../v370-grip-end-cuffs/build.py)，应用本目录的截面裁切差异，并传入 v369 FCStd 和新的输出路径。
