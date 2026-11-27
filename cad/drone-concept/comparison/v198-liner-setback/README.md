# v198 front-liner setback screening

在 v193 基础上仅将 `BrowUnderside` 前罩内衬沿深度方向后移 1 mm。实测平面屏、可视区、外挂筒、屏幕侧控件、格栅和四根支柱保持。候选完成保存 CAD、STEP、从保存 FCStd 临时重建网格、固定相机渲染、半透明叠加、边缘和差异输出。

| 固定相机 | v193 | v198 |
| --- | ---: | ---: |
| 视频十方位 | 85.910052% | 85.910044% |
| 静态七图 | 82.533877% | 82.533862% |
| 拼图十格 | 89.664094% | 89.664088% |

三组均未产生可重复的整体轮廓提升，正式外观入口保持 v193。该候选作为未采用研究结果保留，不能据此宣称整圈 90% IoU 或主要部件轮廓偏差 5% 已达成。测量平面屏继续保留，参考曲面屏及不可观察细节仍是限制。

- [视频十方位比较](video-comparison/comparison-board.png)
- [静态七图比较](stills-comparison/comparison-board.png)
- [拼图十格比较](sheet-comparison/comparison-board.png)
- [候选检查](candidate-check.json)
- [筛选记录](screening.json)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从 `candidate.FCStd` 临时生成网格，再使用 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`，不进行图像变形、逐零件对齐或可见部件省略。
