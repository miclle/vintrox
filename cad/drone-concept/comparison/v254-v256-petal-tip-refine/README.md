# v254–v256 大喷口叶片末段偏移筛查

v251 在 `still-05` 新增 624 个前景像素，其中 523 个落在填洞后的参考外轮廓之外。对象 ID 将多数外溢像素归到第 8 至 11 号叶片。相比之下，`video-02` 和 `video-06` 分别新增 356 和 366 个落在参考前景内的像素。该差异来自同一组固定相机和分割规则。[三视角差异图](v251-pixel-differences.png) · [v251 报告](../v251-v253-petal-tip-screen/README.md)

| 版本 | 接续 Z | 轴向倍数 | 径向偏移／17 mm | 局部 Y 偏移／17 mm | 保存几何 |
| --- | ---: | ---: | ---: | ---: | --- |
| v254 | 109.5 mm | 1.28 | −2.5 mm | 1.5 mm | 第 8 号叶片在保存前未通过有效性和闭合检查 |
| v255 | 111 mm | 1.40 | 0 mm | 4 mm | 六个叶片新增高级几何错误 |
| v256 | 111 mm | 1.28 | 0.75 mm | 1 mm | 41 件改动通过保存读回，无新增高级几何错误和接合退步 |

v256 的 13 件支撑实体差集为零。三组整机对照均使用 v250 相机。v256 的静态七图退步集中在 `still-05`，该视角下降 0.03483 个百分点。[v254 构建记录](v254-build-failure.json) · [v255 几何](v255/candidate-check.json) · [v256 几何](v256/candidate-check.json)

| 对照项目 | v250 | v256 |
| --- | ---: | ---: |
| 视频十方位平均 IoU | 85.92720% | 85.93788% |
| 静态七图平均 IoU | 82.55069% | 82.54571% |
| 拼图十格平均 IoU | 89.67190% | 89.70262% |
| `video-02` 叶片端部最大偏差／投影屏宽 | 20.96% | 20.04% |
| `video-06` 叶片端部最大偏差／投影屏宽 | 21.94% | 21.42% |

v256 缩小了两处侧后视的最大偏差，静态七图均值仍低于 v250。v250 仍为正式交付版本，v256 保留作独立对照。候选的 STEP 独立读回和 FreeCAD 原生视图待验证。[局部对照](v256/visible-petal-edges.png) · [视频十方位](v256/video-comparison/comparison-board.png) · [静态七图](v256/stills-comparison/comparison-board.png) · [拼图十格](v256/sheet-comparison/comparison-board.png)

用 v250 保存模型及网格运行 `tools/experiment_drone_petal_axial.py --construction tip-splice`，将表中的参数分别传给 `--station`、`--factor`、`--tip-radial-shift` 和 `--tip-centre-shift`。固定相机渲染和端部检测沿用 v251 的流程。[复现流程](../v251-v253-petal-tip-screen/README.md)
