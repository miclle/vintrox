# v264 前罩组件筛选

从 v259 保存模型出发，使用真实 CAD 前罩脚本筛选两档局部改动。`depth096` 将前罩总成深度缩放到 0.96 倍，`liner095` 将 `BrowUnderside` 内衬高度缩放到 0.95 倍。实测平面屏、外挂筒、侧控件、格栅和四根支柱保持。

| 候选 | 视频十方位 | 相对 v259 | 决策 |
| --- | ---: | ---: | --- |
| v259 基线 | 86.008085% | — | 正式入口 |
| 前罩深度 0.96 | 85.946547% | −0.06154 个百分点 | 不采用 |
| 内衬高度 0.95 | 86.007215% | −0.00087 个百分点 | 不采用 |

两组候选均完成保存 FCStd、STEP 导出和 696 个网格对象绑定。视频比较使用 v259 的十方位固定相机、真实 CAD 三角网格和相同支柱排除范围。静态图和拼图未对这两档继续运行，因为视频均值已经退步。候选没有替换正式 v259。

[前罩深度 0.96](depth096/video-comparison/comparison-board.png) · [内衬高度 0.95](liner095/video-comparison/comparison-board.png) · [候选检查](depth096/candidate-check.json)

复现使用 `tools/experiment_drone_front_brow_contract.py`，分别传入 `--depth-scale .96` 或 `--liner-height-scale .95`，再使用 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`。没有使用图像变形、逐件配准或删除可见零件。
