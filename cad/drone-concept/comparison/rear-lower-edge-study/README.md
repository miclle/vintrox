# v40 后盖与外框下沿

采用 C，正式 FCStd SHA-256 `a517708ecfbf61416ae16f371bdfa9d319ce36b552d257707e69dc5bd9376ca6`。基线为 v39 `ea492d3652025456d2dcf20d264cc826f46d479edaf1a9fb3742ff9dcf70ebe3`。只改后盖外框与检修盖板；喷口、凹舱、侧后肩、侧框及四支柱保持。

## 固定角度比较

先以[物体 ID 归属](baseline-boundary-attribution.json)判定可见边界：后斜视中偏低的下沿属于后盖和外框，并非喷口周围阴影。抬高两件下沿，保持顶面位置、7.56mm 框边厚度及原圆角，未用平面切除去削薄框边。

| 试件 | 下沿抬高 | 27 点 RMS / 最大偏差 | 十方位 IoU | 七张独立图均值 |
| --- | --- | --- | --- | --- |
| v39 | 0mm | 4.98145 / 11.18034px | 84.78016% | 81.90992% |
| A | 2mm | 4.29470 / 8.54400px | 84.78034% | 81.90992% |
| B | 4mm | 3.83454 / 8px | 84.78043% | 81.90992% |
| C | 6mm | 3.57978 / 8px | 84.78071% | 81.90992% |

C 两侧后斜视 RMS 分别为 3.33809 和 3.07060px；纯侧视为 4.12311 / 3.77964px，有轻微退步。七张独立图逐张轮廓分数保持，不代表内部细节相同。主指标增益很小；本轮主要修正内部可见下沿，不宣称已达到 90% 或整体外观一致。手工抽样包含遮挡边界，不代替完整曲面判断。

[数值汇总](review.json) · [v39 原始报告快照](baseline-v39.json) · [A](a/comparison/comparison-board.png) · [B](b/comparison/comparison-board.png) · [C](c/comparison/comparison-board.png) · [C 七张独立图](c/stills/comparison-board.png)。

[C 左后](c/detail-left.png) · [C 正后](c/detail-back.png) · [C 右后](c/detail-right.png)，依次为参考、v39、v40、50% 叠加；相机、裁切、分割方法固定，未做非刚性变形。

[当前左后下沿放大](../rear-lower-edge-closeup-left.png) · [当前右后下沿放大](../rear-lower-edge-closeup-right.png)。

## 保存与受保护部位

[两件实体和上半部读回](formal-geometry-check.json)及[生成器等价](source-equivalence.json)检查通过。两件 Z≥84mm 的上部差集为零，四支柱差集为零。[归档转移](archive-transfer.json)保留 696 个未改 BRep 和 GUI 状态，694 个可见对象的网格、颜色和材质保持。[原生 GUI](native-open-check.json)打开 700 个顶层对象，其中 696 个可见，未再次保存。

后框与弧面仍接触；后盖和弧面保留约 0.318mm 原分件间隙，后盖与下斜封板、凹舱衬件仍有体积交叠。后框下沿变化使其与凹舱衬件约有 960.07mm³ 搭接；这是外观零件穿插，未设计制造接缝。参见 [C 局部连接](c/candidate-check.json)及[C 空腔和支柱检查](c/cavity-check.json)。

天线上部共面接缝及槽口的保持检查限定于 Z≥134mm，记录整件变化体积；完整两件的变化由源代码、候选与保存实体差集检查覆盖，不用上部局部检查替代全件。实际凹舱、喷口体及口沿层次保持，阴影没有被转成额外筒壁。

## 复现

使用 FreeCAD 自带 Python 运行 `tools/experiment_drone_rear_lower_edge.py`，传入 v39 的保存模型、同哈希网格、空输出目录及 `--rise 2` / `4` / `6`；随后使用既定视频与独立图相机渲染，并执行 `measure_drone_rear_transition.py`。正式转移入口为 `tools/refine_drone_rear_lower_edge.py`，输出 FCStd、STEP、清单和同哈希网格；`tools/measure_drone_rear_lower_edge.py` 核对源代码、候选、保存实体及四支柱。

三份约 768MiB 原始网格转入本机缓存，路径与哈希见 [mesh-cache.json](mesh-cache.json)。候选模型、检查及逐图渲染保留。完整从头 GUI 重建的 OCCT 稳定性问题仍保留，当前仍为外观研究，未做制造或实物验收。
