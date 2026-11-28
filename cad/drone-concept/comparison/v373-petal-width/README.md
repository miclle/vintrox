# v373 喷口叶片与附件宽度

旧切向缩放脚本把叶片编号和附件后缀一起解析成整数。例如第 1 号叶片的压条 `NozzlePetalEdgeRail1_24` 被读成 124。v348、v355 的逐件记录各列出 65 个处理对象。修正后，以 v372 为底按原脚本的局部切向系数 0.96 生成 v373，十二个编号各覆盖九个实际对象，共 108 个。[对象清单](candidate-check.json)

| 同相机测量 | v372 | v373 |
| --- | ---: | ---: |
| 第 60 帧可追踪端角偏差 | 5 px | 2 px |
| 第 90 帧可追踪端角偏差 | 1 px | 2 px |
| 第 180 帧可追踪端角偏差 | 1 px | 4.12 px |
| 视频十方位平均 IoU | 86.09527% | 86.12406% |
| 静态七图平均 IoU | 82.64240% | 82.67156% |
| 拼图十格平均 IoU | 89.93830% | 89.94133% |

三组整机均值比 v372 略高，仍低于正式 v371。第 60 帧端角得到改善，第 180 帧有回退。[同位置近景](tracked-corners.jpg) · [视频](video-overlays.jpg) · [静态](stills-overlays.jpg) · [拼图](sheet-overlays.jpg)

根部切割和切向变换后，FCStd 和 STEP 均读回 1026 个有效闭合实体，较 v372 多 157 个。部分对象在布尔运算后分成更多实体，本候选只作宽度研究。原生显示四方位中可见对象均为 696 个，70 种颜色与渲染网格对应。[逐件实体数变化](solid-changes.json) · [独立读回](independent.json) · [原生显示](native/native-display-verification.json)

复建使用修正后的 `tools/experiment_drone_petal_contract.py`，向 `--base-model` 和 `--base-meshes` 传入 v372 保存模型及其网格，指定新的输出目录和 `--factor .96`。通过 `tools/restore_candidate_display.py` 恢复同源颜色后，从彩色 FCStd 导出验证网格与 STEP。
