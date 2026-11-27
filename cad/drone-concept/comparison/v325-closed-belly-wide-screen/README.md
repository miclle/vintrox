# v325 ClosedBellyPan 宽范围 Y 向筛选

根据保存 FCStd 的 still-05 对象归因，筛选 ClosedBellyPan 的 Y 向缩放 0.97、0.98、1.02 和 1.03。四档均保持 Y 最小端固定在 25 mm，保存实体有效，696 个可见对象保持。[筛选汇总](screening.json)

| 候选 | 静态七图平均 IoU | 相对 v315 |
| --- | ---: | ---: |
| v315 | 82.687714% | — |
| 0.97 | 82.687663% | -0.000051 个百分点 |
| 0.98 | 82.687627% | -0.000087 个百分点 |
| 1.02 | 82.687377% | -0.000337 个百分点 |
| 1.03 | 82.687305% | -0.000409 个百分点 |

四档变化均只出现在 still-05，没有形成超过渲染和三角化噪声的收益。正式模型保持 v315。每档保留真实 CAD、STEP、颜色恢复和静态固定相机对照的可复现记录，网格按保存模型临时重建。[0.97](scale-.97/comparison-board.png) · [0.98](scale-.98/comparison-board.png) · [1.02](scale-1.02/comparison-board.png) · [1.03](scale-1.03/comparison-board.png)

复现时运行 tools/experiment_drone_closed_belly_y.py --scale 0.97、0.98、1.02 或 1.03，用 tools/restore_candidate_display.py 恢复 v315 的显示载荷，再用 tools/export_candidate_drone_meshes.py 和 tools/compare_drone_reference.py 重放 v315-antenna-multiview/stills-comparison/cameras.json。不使用图像变形、逐件配准或删除可见部件。
