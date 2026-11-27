# v261 大喷口整体切向收窄筛选

从 v259 保存模型出发，对 12 组大喷口叶片及其相关实体沿各自局部切向整体收窄，根部 8 mm 保持不动。筛选了 0.90 和 0.88 两档，保存 FCStd、STEP 和三组固定相机结果均独立留档。

| 档位 | 视频十方位 | 静态七图 | 拼图十格 | 决策 |
| --- | ---: | ---: | ---: | --- |
| v259 基线 | 86.008085% | 82.574342% | 89.772706% | 正式入口 |
| 0.90 | 86.003807% | 82.586683% | 89.713070% | 不采用 |
| 0.88 | 85.999324% | 82.590346% | 89.701051% | 不采用 |

两档视频和拼图均下降。静态图略升不足以支持整体收窄，正式模型继续采用 v259。两档候选各有 696 个保存对象，STEP 独立读回均为 1033 个闭合有效实体。四根支柱、实测平面屏、外挂筒、屏幕侧控件和格栅保持。

三组比较使用 v259 的固定相机、真实 CAD 三角网格和相同分割规则，只排除四根新增支柱及其附属件。没有使用图像变形、逐件配准或删除可见零件。参考曲面屏、黑色材料与背景及遮挡区域仍有识别限制，整圈 90% 与主要部件 5% 目标未达成。

- [0.90 档视频](090/video-comparison/comparison-board.png) · [静态图](090/still-comparison/comparison-board.png) · [拼图](090/sheet-comparison/comparison-board.png)
- [0.88 档视频](088/video-comparison/comparison-board.png) · [静态图](088/still-comparison/comparison-board.png) · [拼图](088/sheet-comparison/comparison-board.png)

候选生成使用 `tools/experiment_drone_petal_contract.py`，参数为 `--factor 0.90` 或 `--factor 0.88`，基线为 v259 保存 FCStd 与其导出网格。渲染使用 `tools/render_drone_concept.py`，比较使用 `tools/compare_drone_reference.py`。STEP 导出和独立读回记录见各档 `step-readback.json`。
