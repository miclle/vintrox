# v139 后肩与喷口叶片组合

从保存的 v130 出发，复制 v135 的两件后护甲和 v138 的 46 件大喷口叶片及末段细节。两组变更的 92 对实体包围盒互不相交。使用 v130 的固定相机对完整保存模型渲染、叠加和评分。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% |
| v139 | 85.851826% | 82.473007% | 89.592972% |

组合后的静态和拼图均值提高，视频均值下降约 0.00094 个百分点。正式模型采用 v130。两组原试件的接合统计随组合参数存档，组合独立读回覆盖形体、支撑、网格与导出。48 件变更网格逐顶点、逐面一致，853 个 STEP 实体有效闭合。FreeCAD 原生四视角复核了 696 个可见对象和 70 组显示颜色。[组合参数](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

先按 v135 和 v138 的报告复建两组试件，再用 FreeCAD Python 运行本目录的 `combine.py`。位置参数依次为 v130 FCStd、v130 解压网格、新输出目录、v135 和 v138 的最终试件目录。接着用 `tools/finalize_drone_petal_axial.py` 恢复 v130 的原生颜色、从保存模型重建变更网格和导出 STEP。归档保留参数、对照板及检查报告，旧试件的大型文件可复建。[v135 复建](../v135-v136-rear-shoulder-section/README.md) · [v138 复建](../v138-petal-terminal-offset/README.md) · [v130 渲染流程](../v130-underbody-loop-path/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
