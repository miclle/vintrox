# v135／v136 后肩截面

从保存的 v130 复建左右后护甲。v135 将截面指数从 1.5 降到 1.25，v136 提到 1.75。沿用 R24 下折圆角、截面两端和状态口切口。每个相机均渲染完整的保存模型，沿用 v130 相机和分割。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU | 归到后护甲的参考轮廓外像素 |
| --- | ---: | ---: | ---: | ---: |
| v130 | 85.852768% | 82.442841% | 89.589450% | 5,230 |
| v135 | 85.850369% | 82.476595% | 89.575564% | 3,816 |
| v136 | 85.819768% | 82.414652% | 89.587467% | 7,367 |

v135 减少了后护甲的轮廓外像素，静态均值提高，视频和拼图均值小幅下降。v136 的后护甲外侧差异扩大，三组均值均下降。正式模型采用 v130。对象归属受遮挡影响，局部像素计数只覆盖整机轮廓外侧。[后侧三方位近景](rear-closeups.png) · [v135 对象归属](v135/video-ids/boundary-regions.json) · [v136 对象归属](v136/video-ids/boundary-regions.json)

两组均通过两件后护甲的高级形体检查和四处接触间隙检查。独立读回确认 696 个可见对象、853 个有效闭合 STEP 实体和四支柱几何。原生四视角检查确认 70 组显示颜色及保存可见性。[v135 读回](v135/readback-verification.json) · [v135 原生显示](v135/native-display/native-display-verification.json) · [v136 读回](v136/readback-verification.json) · [v136 原生显示](v136/native-display/native-display-verification.json)

复建时用 `tools/experiment_drone_rear_shoulder_section.py`，以 v130 的 FCStd 和解压网格作为 `--base-model` 和 `--base-meshes`，分别传入 `--exponent 1.25` 或 `--exponent 1.75`，并指定空的 `--output` 目录。再用 `tools/finalize_drone_petal_axial.py` 恢复保存的显示属性，从读回的 FCStd 重建变更网格并导出 STEP。三组固定相机和渲染命令见 v130。归档保留对照板和读回报告，旧试件的大型文件可复建。[v135 参数与哈希](v135/candidate-check.json) · [v136 参数与哈希](v136/candidate-check.json) · [v130 重放流程](../v130-underbody-loop-path/README.md)

- v135 [视频十方位](v135/video-comparison/comparison-board.png) · [静态七图](v135/stills-comparison/comparison-board.png) · [拼图十格](v135/sheet-comparison/comparison-board.png)
- v136 [视频十方位](v136/video-comparison/comparison-board.png) · [静态七图](v136/stills-comparison/comparison-board.png) · [拼图十格](v136/sheet-comparison/comparison-board.png)
