# v155 底部托壳后缘

基于 v154 的轮廓差异，抬高封闭托壳后段两侧的外缘。对称切面从 Y=127 mm、Z=46 mm 过渡到 Y=136 mm、Z=53.35 mm。中间 104 mm 宽区域保留，底盘、回环和支柱座与托壳的原有正体积搭接量保持一致。[构建与搭接报告](candidate-check.json) · [v154 十方位区域差异](video-boundary-v154/boundary-regions-board.png)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v154 | 85.870940% | 82.484227% | 89.635491% |
| v155 | 85.875864% | 82.484484% | 89.638517% |

第 90、120、150 帧分别增加 0.00723、0.03550、0.00651 个百分点。三组固定相机共 27 个视角均无 IoU 回退。排查时沿用原有参考分割，暗色材料与背景相近时仍有归属不确定性。实测平面屏参与完整渲染，参考曲面罩与遮挡几何属于外观推定。整圈 90% IoU 和主要部件完整轮廓偏差 5% 仍待达成。

保存读回复核托壳网格与四支柱，STEP 含 853 个有效闭合实体。FreeCAD 原生四视图确认 696 个可见对象和 70 组颜色。[保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [当前交付校验](../../delivery-verification-current.json)

复建时从本机恢复包和 LFS 缓存取回 v154 的 FCStd 和压缩网格，再解压网格，用 FreeCAD 的 Python 运行本目录 `build.py`，依次传入 v154 FCStd、解压网格和新试件目录。再运行 `tools/finalize_drone_petal_axial.py`，以 v154 FCStd 作为几何与颜色基准。用最终保存模型和网格按三组相机重放。[构建脚本](build.py) · [v154 输入](../v154-handle-petal-combination/README.md) · [网格校验](mesh-archive.json)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
