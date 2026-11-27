# v276 前侧脸颊和桥板横向收形

在 v259 的保存模型上，将左右前侧脸颊及桥板以机身中心平面为基准横向缩至 99%。第 05、06 方位的对象 ID 诊断显示，右桥板在两个相邻方位都超出参考遮罩外缘。固定相机评分沿用三组原始参考和支柱排除规则。[v259 外缘诊断](v259-boundary-diagnostic/boundary-regions-board.png) · [对象归因](v259-boundary-diagnostic/boundary-regions.json)

| 固定相机 | v259 | v276 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.008085% | 86.019486% | +0.011401 |
| 静态七图 | 82.574342% | 82.574760% | +0.000418 |
| 拼图十格 | 89.772706% | 89.777430% | +0.004724 |

27 个视角的 IoU 均持平或提高。视频第 09 方位提高最多，为 0.078613 个百分点，其次是第 03 方位的 0.022622 个百分点。整圈 90% 和主要部件轮廓偏差 5% 的目标仍待达成。[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

保存读回及 STEP 独立读取通过。四件修改的形体均通过高级几何检查，桥板与侧脊间隙均为 0 mm，STEP 包含 853 个有效闭合实体。保留实测 210 × 160 × 2 mm 平面屏、外挂筒、屏幕侧控件、格栅和四根支柱。FreeCAD 原生四视图核对了 696 个可见对象与 70 组颜色。曲面罩和遮挡结构是外观推定，实物与制造验证待开展。[保存读回](../../readback-verification.json) · [候选几何与 STEP](independent-readback.json) · [原生显示](native-display/native-display-verification.json)

复建时使用 [v259 保存模型](../v259-rear-beacon-length/candidate.FCStd) 作为 `--base` 和 `--appearance-source`。用 `tools/export_saved_drone_meshes.py` 导出 v259 网格，传入 `--model` 和从提交 `06b6ed09` 提取的 v259 `concept-manifest.json`。然后运行 `tools/experiment_drone_front_cheek_contract.py`，以 v259 网格作为 `--base-mesh`，使用 `--scale .99 --revision v276-front-cheek-x099`。从 v276 保存模型独立重建的网格与比较渲染网格逐字节一致。[网格记录](mesh-archive.json) · [生成与比较命令](../../../../docs/drone-concept.md#编辑与复现)
