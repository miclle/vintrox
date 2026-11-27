# v152 提手支臂中间角度

从保存的 v140 出发，将左右支臂及随动细节各向内转 0.75°，累计内倾 3.25°。与累计内倾 4° 的 v151 使用相同相机、分割和整机几何对照。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v151 | 85.865014% | 82.483732% | 89.610957% |
| v152 | 85.869249% | 82.481709% | 89.608641% |

正后方五行已有样点的 RMS 从 v151 的 2.37 px 降至 1.14 px，最大偏差从 4 px 降至 2 px。第 180、60 帧侧视样点 RMS 分别为 3.33 和 1.96 px，介于 v140 与 v151 之间。v152 的视频均值最高，静态和拼图均值稍低于 v151。本轮以 v151 为正式版本，保留 v152 的三组对照与局部证据。样点覆盖提手支臂的可见边缘。[正后方扫描线](rear-scanline-check.json) · [两组侧视](handle-profile.json) · [v151 对照](../v151-handle-arm-tilt/README.md)

十四项接合通过复核。独立读回确认 12 件变更网格与保存几何一致、四支柱几何一致、853 个有效闭合 STEP 实体。FreeCAD 原生四视角确认 696 个可见对象及 70 组显示颜色。[形体与接合](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从恢复的 v140 FCStd 和解压网格运行 `tools/experiment_drone_handle_tilt.py`，传入 `--angle .75`。用 `tools/finalize_drone_petal_axial.py` 从最终模型恢复原生显示、生成网格并导出 STEP。用 v151 目录的三组固定相机重放。[v140 恢复流程](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
