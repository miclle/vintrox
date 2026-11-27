# v144 大喷口叶片末段延长与偏移

从保存的 v140 出发，在喷口局部 Z=113 mm 接续。31 件叶片及末段细节的轴向跨度增至 1.95 倍，按每 17 mm 原轴向跨度沿局部 Y 偏移 9 mm。使用同一组固定相机渲染保存模型。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v144 | 85.860025% | 82.473049% | 89.617654% |

第 180 帧采样 RMS 从 31.22 降到 28.55 px，最大采样偏差仍为投影屏宽的 21.94%。第 150 帧 RMS 从 7.68 升至 8.50 px，第 30 帧整机 IoU 下降 0.01243 个百分点。正式外观采用 v140，本试件保留作轴向跨度与中心偏移联合调整的证据。[逐点数据](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

直接投影保存的叶片折边，53 个参考点的最近边缘距离 RMS 从 20.01 降至 18.36 px。该计算包含被遮挡的折边。随后固定相机并拟合接续面之后的折边，Z=98、104、110、113 mm 的七组 RMS 分别为 9.14、9.52、15.91、18.25 px。Z=98 的拟合参数用于构造实体时，`NozzlePetal0` 未通过有效闭合检查。Z=101、104、107 和 110 的四组备选参数在实体预检中均报告 `NozzlePetal0` 与 `NozzlePetal4` 异常。拟合数据用于定位形体调整方向，真实候选需要通过保存体与可见边缘复核。[v140 折边投影](v140-saved-hem-projection.json) · [v144 折边投影](v144-saved-hem-projection.json) · [Z=98](splice-fit-98.json) · [Z=104](splice-fit-104.json) · [Z=110](splice-fit-110.json) · [Z=113](splice-fit-113.json)

试件通过 84 项接合检查。独立读回确认 31 件变更网格与保存实体一致，四支柱几何一致，853 个 STEP 实体有效闭合。FreeCAD 原生四视角确认 696 个可见对象和 70 组显示颜色。[构建](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从 v140 的 FCStd 和解压网格运行 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --station 113 --factor 1.95 --tip-centre-shift 9`。用 `tools/finalize_drone_petal_axial.py` 恢复保存的显示属性并导出 STEP。归档保留参数、报告和对照板，试件大文件可复建。[v140 输入与固定相机](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
