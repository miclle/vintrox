# v204 screen bezel expansion screening

v204 在 v193 基础上将 `ScreenBezel` 与 `BezelLip` 每侧外扩 0.2 mm。实测平面屏、可视区、外挂筒、屏幕侧控件、格栅和四根支柱保持。

| 固定相机 | v193 | v204 |
| --- | ---: | ---: |
| 视频十方位 | 85.910052% | 85.911793% |
| 静态七图 | 82.533876% | 82.530801% |
| 拼图十格 | 89.664088% | 89.667149% |

视频和拼图提高，静态七图下降，因此正式模型继续保持 v193。候选保存 FCStd、STEP、三组固定相机渲染、半透明叠加、边缘和差异图，未使用图像变形、逐零件对齐或可见部件省略。

- [筛选记录](screening.json)
- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)

网格不随仓库保存。复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时生成网格，不依赖 Git LFS。
