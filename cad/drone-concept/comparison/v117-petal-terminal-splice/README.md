# v117 大喷口叶片末段试验

从保存的 v115 出发，在喷口局部坐标的三个 Z 站位分别切开叶片末段，沿轴延长并沿局部 Y 方向剪切。剪切量按原轴向跨度 17 mm 计。三组沿用固定相机、参考分割和四支柱排除规则，保留实测平面屏、外挂筒、侧控件与格栅。接缝使用共面融合，连续曲率待验证。参考曲面屏和隐藏构造仍按图推定。

| 接缝站位及参数 | 视频十方位 IoU | 静态七图 IoU | 参考拼图 IoU | 末端最大采样偏差 |
| --- | ---: | ---: | ---: | ---: |
| v115 基线 | 85.8446100% | 82.4302146% | 89.5914211% | 22.74% |
| 98 mm，1.25 倍，3 mm | 85.8291296% | 82.4155846% | 89.6231345% | 18.55% |
| 104 mm，1.32 倍，4 mm | 85.8347427% | 82.4187378% | 89.6208017% | 19.67% |
| 110 mm，1.55 倍，7 mm | 85.8455572% | 82.4255466% | 89.6122840% | 21.67% |

末端偏差按各视角投影屏宽归一化，只覆盖可辨认的喷口末端。98 mm 和 104 mm 候选分别有三件和一件加强条新增高级曲面校验错误。110 mm 候选改动 46 件，95 项接合距离无退步，无新增高级检查错误。保存读回确认 696 个可见对象、852 个有效闭合 STEP 实体和四支柱几何保持，46 件变更网格与保存 CAD 一致。FreeCAD 原生四视图通过颜色和可见性检查。考虑整体增益和静态退步，正式模型仍采用 v115。整圈 90% 和主要部件 5% 目标仍待达成。[末端叠加](station110-final/visible-petal-edges.png) · [读回](station110-final/readback-verification.json) · [原生颜色](station110-final/native-display/native-display-verification.json)

[视频十方位](station110-final/video-comparison/comparison-board.png) · [静态七图](station110-final/stills-comparison/comparison-board.png) · [参考拼图十格](station110-final/sheet-comparison/comparison-board.png)

复建以 v115 保存模型和解压网格为输入，使用 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 110 --factor 1.55 --tip-centre-shift 7`，按脚本帮助传入 `--base-model`、`--base-meshes`、`--output`。通过 `tools/finalize_drone_petal_axial.py` 用 v115 恢复原生外观并导出 STEP，再使用本包的三组相机重放对照。[v115 输入](../v115-antenna-curve/README.md) · [固定相机渲染流程](../v116-petal-hinge-plus3/README.md)
