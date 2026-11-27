# v274 前罩主体横向收形

从 v259 的保存模型出发，将 `ProjectingBrow` 和 `BrowUnderside` 以整机中心平面为基准横向缩至 0.985 倍。两件形体通过保存读回，有效且闭合。候选导出 STEP 和 696 件渲染网格，保留实测屏幕、四根支柱和保存显示数据。[几何记录](candidate-check.json)

固定十方位视频平均轮廓 IoU 从 86.008085% 降到 85.979599%，减少 0.028486 个百分点。第 09 方位下降最多，为 0.097727 个百分点。正式模型继续采用 v259。候选停在视频筛选阶段，静态图、拼图、STEP 独立读回和原生显示未复查。[对照板](video-comparison/comparison-board.png) · [逐方位报告](video-comparison/comparison-report.json) · [渲染清单](video-renders/render-manifest.json)

复现时从正式 v259 导出临时网格，调用 `tools/experiment_drone_front_brow_contract.py`，提供正式 FCStd 作 `--base` 和 `--appearance-source`，并传入 `--scale .985 --revision v274-brow-x0985`。用候选保存模型与网格重放[固定视频相机](../cameras.json)。[正式模型与工具入口](../../../../docs/drone-concept.md#编辑与复现)
