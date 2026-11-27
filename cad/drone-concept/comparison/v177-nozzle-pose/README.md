# v177 大喷口总成姿态候选

用 v173 的叶片末端折边与七个参考视角的 53 个历史样点预筛总成姿态。单独转动绕喷口根部的 X 轴，拟合角度约为 −3.68°，11 组后壳接合均保有正体积。拟合若同时允许 Y、Z 平移，会提出 +7.00°、Y −9.98 mm 和 Z −17.44 mm 的组合，该组合使 6 处后壳接合断开，最大间隙 15.21 mm。预筛的投影包含可能被遮挡的折边。[后壳接合预筛](pose-contact-screening.json) · [历史样点](../v176-petal-tip-extension/visible-petal-edges.json)

| 固定相机 | v173 | v177 |
| --- | ---: | ---: |
| 视频十方位 | 85.90093% | 85.89219% |
| 静态七图 | 82.52506% | 82.50555% |
| 拼图十格 | 89.65442% | 89.57825% |

v177 转动 143 件喷口、标识和内部占位形体。高级几何检查与后壳接合无新增失败。三组均值下降，保留 v173。样点用于判断末端位置，主要部件完整轮廓偏差仍待测。[形体与接合](candidate-check.json) · [逐视角结果](candidate-results.json) · [视频对照](video-comparison.png) · [静态图对照](stills-comparison.png) · [拼图对照](sheet-comparison.png)

从 v173 的保存 FCStd 导出网格后，运行 `tools/experiment_drone_nozzle_pose.py --angle -3.68` 构建试件。用 `tools/finalize_drone_petal_axial.py` 恢复保存颜色、导出 STEP 并重建变更网格，再按 v173 的三组固定相机评审。
