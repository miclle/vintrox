# v134 小喷口内封片

基于保存的 v130，将两片内封片从局部 Z=44 mm 的直圆柱改为从 Z=42 mm 开始的锥台。锥台长 2 mm，根端半径 22.8 mm，出口端半径 19.0 mm。沿用各封片原有坐标系，在根端保留与 18 片主叶片的接合。参考中暗色封片的深度和连接形式仍是外观推定。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% |
| v134 | 85.855070% | 82.442389% | 89.589601% |

视频十方位中，归到内封片的参考轮廓外像素由 4,579 降至 2,761，归到主叶片的像素从 11,086 升至 12,801，小喷口总计从 25,175 降至 25,066。八组既有口沿和回环采样距离相同。大部分像素差异落在相邻零件的遮挡关系上，三组整机分数变化很小，正式模型继续采用 v130。[对象归属](video-ids/boundary-regions.json) · [逐点对照](visible-pod-loop-edges.png)

最终 FCStd 通过 36 个叶片端面和 328 项接合复核。STEP 读回确认 853 个有效闭合实体，四支柱与 v130 一致。原生四视图确认 696 个可见对象及 70 组显示颜色。[端面与接合](terminal-contact-check.json) · [STEP 读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

复建时只替换 v130 中两个 `LowerPodDiaphragm` 对象。用 `Part.makeCone(22.8, 19.0, 2, App.Vector(0, 0, 42))` 构造锥台，以原封片的 `Shape.Placement` 左乘锥台的 `Placement`。保存后独立读回复核端面和接合，再从最终保存模型导出 STEP 并重建变更网格。按 v130 的同组相机重放。[参数与哈希](candidate-check.json) · [v130 重放流程](../v130-underbody-loop-path/README.md)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)
