# v41 叶片圆角凹槽

采用 B。正式模型 SHA-256 `72f70bbc88e8ec059fb033c6388f89bd8a96a877e0f683a1a0d805848d590adc`，基线 v40 `a517708ecfbf61416ae16f371bdfa9d319ce36b552d257707e69dc5bd9376ca6`。12 片叶片及 12 片槽底衬片改变；后壳、凹舱、喷口外罩、口沿、导轨和四支柱保持。

## 选择依据

参考后三视角的叶片槽角较圆，底部金属边较窄。A 试验圆角渐缩槽；B 同时扩大槽口并收窄底边。切槽采用先倒圆的平面渐缩切削体与真实曲面求交，槽底仍为有厚度曲面实体。外框、凹槽及衬片保持独立层次，未调整材质或相机。

| 试件 | 槽口 | 十方位 IoU | 七张独立图均值 | 出口圆 RMS | 三处节距 RMS |
| --- | --- | --- | --- | --- | --- |
| v40 | 较宽底边、直角切槽 | 84.78071% | 81.90992% | 3.29834px | 1.66px |
| A | 圆角渐缩切槽 | 84.78071% | 81.90989% | 3.29834px | 1.66px |
| B | 圆角渐缩切槽，较窄边框 | 84.78071% | 81.90989% | 3.29834px | 1.66px |

[数值](review.json) · [A 十方位](a/comparison/comparison-board.png) · [B 十方位](b/comparison/comparison-board.png) · [B 逐图](b/stills/comparison-board.png) · [B 正后放大](b/closeup-back.png)。B 的选择依据是后三视角的槽口观感；没有通过更换分割或相机提高分数。图 05 的 CAD 前景多一个像素，其他六张轮廓分数保持；全圈目标未达成，材质反光、细小末端构件和完整曲面仍有差异。

[B 正后放大](b/closeup-back.png) · [左后](b/detail-left.png) · [正后](b/detail-back.png) · [右后](b/detail-right.png)。依次为参考、v40、v41、50% 叠加。

## 几何和测量复核

凹槽切削体圆角为 1mm，衬片圆角为 0.8mm；局部截面站位为 99.5～127mm，保留叶片 2mm 主厚度。数值是外观推定，不是测得的原作尺寸。实际切削体会随各片位置和末端倾斜变化，不能把站位解释成全局水平裁切高度。

24 个变化对象高级实体检查通过，12 处衬片与叶片有正体积接合。候选、[生成器](source-equivalence.json)及[正式读回](formal-geometry-check.json)逐件实体差集为零，四支柱差集为零。[归档转移](archive-transfer.json)保留 674 个未改 BRep 与 GUI 状态；672 个可见网格及材质保持。[原生 GUI](native-open-check.json)打开检查通过，未再次保存。

旧槽由全局水平面裁切，在正后相机背向的三片叶片末端局部贯出。新曲面槽补回内缘：[0.2mm 端部薄层诊断](b/cap-preservation-check.json)在 NozzlePetal1/2/3 分别增加约 2.09516、2.52733、2.09516mm³，未移除该薄层材料。该报告的整端部不变检查仍为 `false`，如实保留；不能将外圆保持表述为全部端面不变。12 片根部薄层差集均为零。

[出口外圆读回](b/outline-check.json)仍为半径 43.6mm、中心 `(0,250.20518,65.37186)mm`，12 片实际圆弧共圆。旧检测按面延长线与轴的交点排序，会选到新增槽端面；改为先从真实 CAD 找完整共享的根部和末端圆，再取沿轴最后一个完整圆，不按参考拟合值挑选。[检测回归](outline-selector-regression.json)确认 v40/A/B 相同，单独缩短一片末端 0.63mm 的内存反例被拒绝。出口圆仍只是局部轮廓证据。

## 失败与复现

第一次在已裁切的曲面凹槽上直接倒圆出现自交和不可定向面，未保存为正式模型。改用先倒圆的简单切削体求交后通过高级实体检查。失败脚本、日志和后续检查脚本留在缓存，见 [mesh-cache.json](mesh-cache.json)。

使用 FreeCAD Python 运行 `tools/experiment_drone_petal_recess.py`，传入 v40 模型、同哈希网格、空输出目录及 `--variant a` / `b`。使用既定十方位和七张独立图相机渲染，运行 `measure_drone_nozzle_outline.py` 和 `measure_drone_petal_pitch.py`。正式保存入口为 `tools/refine_drone_petal_recess.py`；`tools/measure_drone_petal_recess.py` 校验源代码、候选、保存实体、衬片接合与四支柱。

原始网格约 510MiB 转入本机缓存；候选 FCStd、渲染、对比和检查保留。完整从头 GUI 重建的 OCCT 稳定性问题仍未解决，当前结果不代表制造、声学或实物验收。
