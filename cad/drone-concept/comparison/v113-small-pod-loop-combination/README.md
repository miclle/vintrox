# v113 小喷口与底部回环联合对照

以 v112 修剪压条根部后的保存模型为父模型，加入 v111 的 30% 回环路径，截面半径为 2.2 mm。实测平面屏、四支柱、外挂筒、侧控件和格栅均保留。[回环路径输入](path-fit.json) · [构建记录](candidate-check.json)

| 固定相机平均轮廓 IoU | 视频十方位 | 静态七图 |
| --- | ---: | ---: |
| v107 | 85.708302% | 82.445144% |
| v111 单独修改回环 | 85.708668% | 82.473895% |
| v112 单独修改小喷口 | 85.705370% | 82.433013% |
| v113 合并两处修改 | 85.704510% | 82.461442% |

视频第 180 帧中，合并后的回环最大采样偏差为投影屏宽的 21.79%，相比只改回环的 22.95% 有所缩小。v107 在同一处为 19.25%。两组正后方回环偏差较 v107 下降。四组口沿采样保持 v112 的结果。四份保存模型的回环和小喷口之间均无正体积交叠，v113 的回环与小喷口外罩最近距离约为 23.65 mm。当前外观入口采用 v107。整圈 90% IoU 和主要部件完整轮廓偏差 5% 的目标仍待达成。[边缘对照](visible-pod-loop-edges.png) · [逐点数据](visible-pod-loop-edges.json) · [保存实体间隙](loop-pod-clearance.json)

独立读回确认 696 个可见对象及 852 个有效闭合 STEP 实体，152 件变更件与最终模型重新三角化结果一致。FreeCAD 原生四视图通过颜色与可见性检查。平面屏使用实测输入，曲面罩和不可见部分仍按参考推定。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png)

复建父模型使用 v112 修剪压条根部的流程，并保留最终 `meshes.json`。按 v111 的复建命令，将建模、打包与颜色来源参数指向该 FCStd 和网格，拟合输入换成本目录的 `path-fit.json`，使用半径 2.2 mm。渲染、对象 ID 和差异图使用 v107 的固定相机。可见边界仍采用 v83 的口沿标注及 v82 的回环标注。[v112 父模型](../v112-small-pod-lip/README.md) · [v111 复建流程](../v111-underbody-loop-path/README.md)
