# v112 小喷口口环与压条根部

在保存 v107 上，取原口环与 v83 参考拟合之间的 55% 插值，将局部轴向位置由 36 移至 39.908 mm，主半径由 27.5 收至 27.265 mm。重建两侧 150 件小喷口零件，保留两侧根部和 36 片叶片的末端截面。第二组将 108 件压条和脊条的根部修剪至局部 Z=39.108 mm，消除了第一组近景中露在暖褐色外罩上的线条。[拟合输入](lip-fit.json) · [四视角局部对照](pod-closeup.png)

| 固定相机平均轮廓 IoU | 视频十方位 | 静态七图 |
| --- | ---: | ---: |
| v107 | 85.708302% | 82.445144% |
| 口环移动 | 85.705286% | 82.433035% |
| 口环移动并修剪压条根部 | 85.705370% | 82.433013% |

第 0、60、180、240 帧的可见口沿采样 RMS 分别从 8.93、12.56、12.91、15.79 px 降至 3.94、6.19、6.60、8.68 px。两个侧视的最大采样偏差仍分别为投影屏宽的 6.55% 和 5.85%。第 180 帧附近回环的采样 RMS 从 11.85 降至 11.13 px，正后方两组回环采样持平。两组整机均值均略低于 v107，当前外观入口采用 v107。[可见口沿和回环对照](trimmed-detail-roots/visible-pod-loop-edges.png) · [逐点距离与遮挡归属](trimmed-detail-roots/visible-pod-loop-edges.json)

两组保存模型均通过 36 个端面和 328 组接合复核。STEP 独立读回为 852 个有效闭合实体，150 件变更零件与保存模型重新三角化结果一致。FreeCAD 原生四视图通过 696 件可见性及颜色复核。实测平面屏、四支柱、外挂筒、侧控件和格栅均保留。曲面罩和隐藏结构仍为外观推定，整圈 90% 和完整主要部件 5% 目标仍待达成。

- [口环移动 FCStd](lip-shift/candidate.FCStd) · [STEP](lip-shift/candidate.step) · [视频十方位](lip-shift/video-comparison/comparison-board.png) · [静态七图](lip-shift/stills-comparison/comparison-board.png) · [读回](lip-shift/readback-verification.json) · [原生显示](lip-shift/native-display/native-display-verification.json)
- [修剪根部 FCStd](trimmed-detail-roots/candidate.FCStd) · [STEP](trimmed-detail-roots/candidate.step) · [视频十方位](trimmed-detail-roots/video-comparison/comparison-board.png) · [静态七图](trimmed-detail-roots/stills-comparison/comparison-board.png) · [读回](trimmed-detail-roots/readback-verification.json) · [原生显示](trimmed-detail-roots/native-display/native-display-verification.json)

## 复建

沿用 v83/v84 的构建、端面与接合验证及打包命令。第一组使用 v107 的 FCStd、解压网格及本目录的 `lip-fit.json`。第二组以第一组的打包结果为父模型，使用 `experiment_drone_pod_detail_roots.py --root-z 39.10767516529829`。两组均以 v107 为颜色来源，以各自的父模型进行打包前的接合检查。[v83/v84 复建流程](../v83-small-pod-lip/README.md)

使用 v107 的视频与静态相机重放渲染和差异图。为候选生成同组对象 ID 图后，运行 `compare_drone_visible_pod_edges.py`，将 `--baseline` 和 `--baseline-ids` 指向 v107，将 `--lip-observations` 指向 v83 的 `lip-fit.json`。这些人工点曾参与历史拟合，测量涵盖可见口沿和部分回环边缘。[固定相机流程](../v107-handle-arm-inward-tilt/README.md)
