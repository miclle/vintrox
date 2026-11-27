# v147 大喷口叶片末段

从保存的 v130 叶片构造独立试件，在局部 Z=110 mm 接续，末段轴向跨度增至 1.95 倍，按每 17 mm 原轴向跨度径向外移 4 mm、沿局部 Y 偏移 9 mm。将通过实体检查的 46 件形体转入 v140，再从最终保存模型导出 STEP 并渲染。v146 的 Z=98 mm 试件中五件叶片脊条出现曲面曲线错误。[候选源读回](leaf-source-check.json) · [v146 失败记录](v146-failed-check.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v147 | 85.856082% | 82.469462% | 89.614822% |

在第 180 帧，末端采样 RMS 从 31.22 降至 28.34 px，最大偏差从投影屏宽的 21.94% 降至 20.68%。第 60 帧最大偏差从 21.34% 降至 19.91%。第 150 帧 RMS 增至 8.39 px，静态七图均值略降，正式模型采用 v140。[逐点数据](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

通过 95 项接合检查。独立读回确认 46 件变更网格与保存几何一致、四支柱几何一致、853 个有效闭合 STEP 实体。与保存的 v140 比较，46 件变更形体在接续面以下的对称差均小于 10⁻⁶ mm³。FreeCAD 原生四视角确认 696 个可见对象和 70 组显示颜色。[构建与接合](candidate-check.json) · [根部差集](root-verification.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从 v130 FCStd 和解压网格运行 `tools/experiment_drone_petal_axial.py`，传入 `--construction tip-splice --station 110 --factor 1.95 --tip-radial-shift 4 --tip-centre-shift 9`，再以 `tools/finalize_drone_petal_axial.py` 导出该试件。运行本目录的 `rebase-petals.py`，依次传入包含解压网格的 v140 目录、前述试件最终目录和新输出目录。用相同导出脚本恢复 v140 显示属性，按 v140 固定相机重放。[v130 恢复](../v130-underbody-loop-path/README.md) · [v140 相机与渲染](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
