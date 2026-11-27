# v291 小喷口外罩微量延长

从 v287 保存模型出发，分别将两个小喷口外罩和口环沿局部轴向延长 0.25 mm、1 mm、2 mm。0.25 mm 档保存形体有效闭合，外罩、口环、主壳、夹座和叶片的 82 项间距检查没有分离原有接触。[保存几何](candidate-check.json)

| 外罩与口环延长 | 视频十方位 | 静态七图 | 拼图十格 |
| ---: | ---: | ---: | ---: |
| v287 | 86.033198% | 82.574760% | 89.782809% |
| 0.25 mm | 86.033177% | 82.574491% | 89.782487% |

0.25 mm 档三组均略低于 v287，正式模型继续采用 v287。1 mm 和 2 mm 档各有 8 个原有口环—叶片接触被拉开，停止在几何接合检查。[0.25 mm 视频](video-comparison/comparison-board.png) · [静态图](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png) · [失败档记录](failed-candidates.json)

候选采用真实保存 CAD 和固定相机渲染。使用 v287 保存模型和网格运行 `replay.py --extension .25`，大档可用 `--extension 1`、`--extension 2` 复现。[固定相机流程](../../../../docs/drone-concept.md#编辑与复现)
