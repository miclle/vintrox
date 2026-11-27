# v154 提手支臂与喷口叶片

在 v140 的保存几何上组合 v151 的提手支臂和 v144 的大喷口叶片末段。两侧提手支臂累计内倾 4°。叶片末段在喷口局部 Z=113 mm 接续，轴向跨度增至 1.95 倍，按每 17 mm 原跨度沿局部 Y 偏移 9 mm。两组变更零件的 372 对包围盒互不相交。[构建记录](candidate-check.json) · [提手几何](../v151-handle-arm-tilt/README.md) · [叶片几何](../v144-petal-extension-offset/README.md)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v151 | 85.865014% | 82.483732% | 89.610957% |
| v153 | 85.875172% | 82.482203% | 89.633173% |
| v154 | 85.870940% | 82.484227% | 89.635491% |

采用 v154 作为正式评审版本。相对 v151，视频与拼图均值分别提高约 0.00593 和 0.02453 个百分点，静态均值变化低于 0.001 个百分点。三组相机覆盖十个环绕方位、七张静态图和十个拼图格。实测平面屏参与完整渲染，参考曲面罩与遮挡处几何属于外观推定。整圈 IoU 90% 和主要部件完整轮廓偏差 5% 仍待达成。

保存读回确认 43 件变更网格逐顶点、逐面一致，四支柱几何一致，853 个 STEP 实体有效闭合。FreeCAD 原生四视图核对了 696 个可见对象和 70 组显示颜色。[独立读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](delivery-verification.json)

从恢复的 v140 复建 v151 与 v144，运行组合脚本，依次传入 v140 FCStd、解压网格、新输出目录、v151 与 v144 的最终试件目录。再用 `tools/finalize_drone_petal_axial.py` 恢复原生显示，从最终保存文件导出 STEP。重放使用本目录三组固定相机、解压网格和保存模型。[组合脚本](../v139-shoulder-petal-combination/combine.py) · [v140 恢复流程](../v140-shoulder-petal-pod/README.md) · [网格清单](mesh-archive.json)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)

v155 接替 v154 后，FCStd、STEP 和压缩网格已移出本地 `main` 历史。可从本机恢复包和 LFS 缓存取回原件。[清理与恢复记录](../../../../docs/storage-cleanup.md) · [v155 当前模型](../v155-rear-belly-relief/README.md)
