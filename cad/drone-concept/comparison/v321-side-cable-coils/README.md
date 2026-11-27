# v321 外挂筒下段卷线

v315 的十方位对象归因在视频 00 和 05 识别出单侧外挂筒卷线的外部差异。按原路径重放，将线束圆截面半径改为 1.5 mm，将下段线圈的半径参数收至 85%。最终 FCStd 从 v315 复制显示载荷和全部其他保存成员，仅替换 `SideCableLeft.Shape.brp`。线束两端仍与护套交叠，13 件支撑构件与线束的交叠体积为零。[v315 差异归因](v315-boundary-regions.json) · [候选几何](candidate-check.json)

| 固定相机 | v315 平均 IoU | v321 平均 IoU |
| --- | ---: | ---: |
| 视频十方位 | 86.204590% | 86.215070% |
| 静态七图 | 82.687714% | 82.703228% |
| 拼图十格 | 89.958234% | 89.960599% |

视频第 04 方位和拼图第 05 格分别下降 0.01872 和 0.03154 个百分点。对保存扫掠截面的中心线复测显示，原拟合两帧 RMS 从 4.20 升至 4.48 px，独立第 120 帧从 5.23 升至 5.38 px。整机均值增益很小，且同一线束的可见走向偏差在三帧汇总中增大，正式评审采用 v315。隐藏引线仍是外观推定。[视频](video-comparison/comparison-board.png) · [静态](stills-comparison/comparison-board.png) · [拼图](sheet-comparison/comparison-board.png) · [基线测量](v315-cable-measure.json) · [候选测量](v321-cable-measure.json)

候选通过 FCStd 与 STEP 独立读回，具有 696 个可见对象和 853 个闭合 STEP 实体。FreeCAD 原生四视图核对了 70 组颜色及可见性。实测平面屏、外挂筒、屏幕侧控件、格栅和四根支柱均在保存候选内。[独立读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

## 复现

1. 从 [v315](../v315-antenna-multiview/README.md) 的保存模型和对应清单，用 `tools/export_saved_drone_meshes.py` 生成基线网格。用 FreeCAD Python 运行 `tools/experiment_drone_side_cable_radius.py`，传入 `--radius 1.5 --lower-coil-scale .85`、基线 FCStd 和网格。
2. 运行 [replay.py](replay.py)，以 v315 为 `--base`、上一步输出为 `--candidate`，生成带颜色的 `--output` FCStd。将 v315 清单副本的 FCStd 哈希更新为新文件哈希，从该 FCStd 重建网格。STEP 导出使用保存 GUI 中的可见对象。
3. 用既有渲染和比较脚本重放本页三组固定相机，使用 `tools/measure_drone_side_cable.py` 复测保存线束的中心线。该档 FCStd、STEP 和派生网格可按上述步骤再生成。[正式流程](../../../../docs/drone-concept.md#编辑与复现)
