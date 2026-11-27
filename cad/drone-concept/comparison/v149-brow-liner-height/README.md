# v149 前罩内衬高度

从保存的 v140 出发，将 `BrowUnderside` 的高度缩至 88%，固定最高点的 Z 和斜面坐标 `Y + 0.4Z`，两端底边抬高约 6.52 mm。内衬与前罩的接触间隙为 0 mm，基线内衬的 16 条高级曲面检查错误在试件中消失。实测平面屏和四支柱通过几何复核。[构建](candidate-check.json) · [保存读回](readback-verification.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v149 | 85.851451% | 82.468728% | 89.591231% |

十方位中，归到内衬的参考轮廓外像素从 11,775 降至 10,184，归到前罩外壳的像素从 7,631 增至 8,953。外壳在部分视角露出，三组整机均值均略降，正式模型采用 v140。原生四视角确认 696 个可见对象和 70 组显示颜色，独立读回确认 853 个有效闭合 STEP 实体及内衬网格一致。[v140 像素归属](v140-boundary-regions.json) · [v149 像素归属](video-ids/boundary-regions.json) · [原生显示](native-display/native-display-verification.json)

复建时以 v140 的 FCStd 和解压网格运行 `tools/experiment_drone_front_brow_contract.py`，传入 `--scale 1 --liner-height-scale .88 --revision v149-brow-liner-height`，用 v140 的相机重放。归档保存参数、检查报告和对照板。[v140 输入与固定相机](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
