# v137 后肩下折圆角

基于保存的 v130，将两件后护甲下折圆角从 R24 改为 R12 mm。截面指数仍为 1.5，沿用状态口切口。由真实 BRep 导出网格，用 v130 的十方位视频、七张静态图和十格拼图相机渲染整机。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU | 归到后护甲的参考轮廓外像素 |
| --- | ---: | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% | 5,230 |
| v137 | 85.850859% | 82.441840% | 89.588528% | 5,327 |

R12 试件的后护甲外侧差异增加 97 px，三组均值小幅下降，正式模型采用 v130。表中 IoU 使用 CPU 渲染。Metal 复跑的视频和拼图均值相同，静态均值相差约 0.000053 个百分点。对象归属来自 Metal 视频渲染，只衡量参考轮廓外侧差异。[对象归属](video-ids/boundary-regions.json) · [逐视角差异板](video-ids/boundary-regions-board.png)

左右后护甲通过高级形体检查，四处接触间隙均为 0 mm。独立读回确认两件变更网格与 FCStd 逐顶点、逐面一致，全部 853 个 STEP 实体有效闭合，四支柱几何一致。FreeCAD 原生四视角确认 696 个可见对象和 70 组显示颜色。[参数与哈希](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [原生后视](native-display/v137-rear.png)

从保存的 v130 模型和解压后的网格运行后肩试验，传入 `--exponent 1.5 --fold-radius 12`。按后肩截面试验的步骤恢复原生显示、读回并导出 STEP，再用 v130 的三组相机重放。归档保留对照板、参数和检查报告，旧试件的大型文件可复建。[复建步骤](../v135-v136-rear-shoulder-section/README.md) · [v130 重放流程](../v130-underbody-loop-path/README.md)

- [视频十方位](video-cpu-comparison/comparison-board.png)
- [静态七图](stills-cpu-comparison/comparison-board.png)
- [拼图十格](sheet-cpu-comparison/comparison-board.png)
