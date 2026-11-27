# v176 大喷口叶片末段延伸

从 v173 保存的实体沿喷口轴向延伸叶片末段。接续站为局部 Z = 110 mm，站位之外的轴向长度乘以 1.05。共修改 46 件叶片及随形细节。独立重开候选后核对了未改形体和支柱，95 项接合检查无新增退步。[实体检查](candidate-check.json)

| 固定相机 | v173 | v176 |
| --- | ---: | ---: |
| 视频十方位 | 85.90093% | 85.90219% |
| 静态七图 | 82.52506% | 82.52375% |
| 拼图十格 | 89.65442% | 89.66030% |

采用 v173，静态图 05 在延长后回落 0.00923 个百分点。逐视角结果保留，主要部件完整轮廓偏差仍待测。[逐视角结果](candidate-results.json) · [视频对照](video-comparison.png) · [静态图对照](stills-comparison.png) · [拼图对照](sheet-comparison.png)

七个参考视角的 53 个历史叶片末端样点中，最大偏差出现在视频第 06 视角，约为投影屏宽的 21.94% → 21.67%。视频第 05 视角的 RMS 从 8.50 px 增至 8.68 px。测量使用可见叶片边界，覆盖所选末端样点。[逐点测量](visible-petal-edges.json) · [边缘叠加](visible-petal-edges.png)

复现时从 v173 保存的 FCStd 导出网格。用 `tools/experiment_drone_petal_axial.py` 构建，参数为 `--construction tip-splice --factor 1.05 --station 110`，再用 `tools/finalize_drone_petal_axial.py` 从最终保存模型重新导出 STEP 和变化网格。评审沿用 v173 的三组固定相机和遮罩。
