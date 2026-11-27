# v153 提手支臂与喷口叶片组合

从保存的 v140 出发，组合 v152 的 12 件提手支臂及随动细节与 v144 的 31 件喷口叶片末段。两组变更部件的 372 对包围盒互不相交。沿用 v151 的三组固定相机渲染整机。[组合参数](candidate-check.json) · [v152 提手试件](../v152-handle-arm-tilt/README.md) · [v144 叶片试件](../v144-petal-extension-offset/README.md)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v151 | 85.865014% | 82.483732% | 89.610957% |
| v153 | 85.875172% | 82.482203% | 89.633173% |

相对 v151，第 180 帧整机 IoU 增加 0.04497 个百分点，静态图 03 增加 0.06574 个百分点，静态图 06 下降 0.04445 个百分点。正式版本采用 v151。整圈 90% 与主要部件完整轮廓偏差 5% 仍待达成。

独立读回确认 43 件变更网格与保存实体逐顶点及逐面一致，四支柱几何一致，853 个 STEP 实体有效闭合。FreeCAD 原生四视角确认 696 个可见对象及 70 组显示颜色。[保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

复建时先从恢复的 v140 模型生成 v152 和 v144 最终试件，再运行组合脚本，依次传入 v140 FCStd、v140 解压网格、独立输出目录、v152 和 v144 的最终试件目录。使用 `tools/finalize_drone_petal_axial.py` 恢复显示并从最终模型导出 STEP，按 v151 的三组相机重放。[v140 恢复流程](../v140-shoulder-petal-pod/README.md) · [组合脚本](../v139-shoulder-petal-combination/combine.py) · [固定相机](../v151-handle-arm-tilt/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
