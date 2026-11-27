# v272–v273 前罩肩部局部内移

从同一份 v259 保存模型重建两组各内移 2 mm 的候选。v272 移动左右弧面内罩及八片白纹，v273 移动左右甲片、滑槽内衬及螺钉。保存读回的变更形体均有效、闭合并具有正体积。高级检查错误集合与对应原件一致。[v272 读回与接合](crown/candidate-check.json) · [v273 读回与接合](plate/candidate-check.json)

| 版本 | 视频十方位 | 静态七图 | 拼图十格 |
| --- | ---: | ---: | ---: |
| v259 | 86.008085% | 82.574342% | 89.772706% |
| v272 弧面内罩和白纹 | 86.009839% | 82.586852% | 89.773446% |
| v273 甲片、滑槽内衬和螺钉 | 85.999641% | 82.579264% | 89.756716% |

v272 的静态第 05 图提高 0.034646 个百分点，视频第 04 方位下降 0.002980 个百分点。该静态图的参考外侧像素从 56,550 降至 56,360，其中左内罩归因从 2,616 降至 1,407，前罩主体从 1,527 升至 2,673。内罩内移后，剩余外溢集中在与其相邻的前罩主体。v273 的视频和拼图均值下降。正式入口继续采用 v259。[基线归因](../v269-rear-shoulder-screening/still-05-boundary.json) · [v272 归因](crown/still-05-boundary.json) · [差异图](crown/still-05-boundary-diagnostic.png)

- v272 [视频](crown/video-comparison/comparison-board.png) · [静态](crown/still-comparison/comparison-board.png) · [拼图](crown/sheet-comparison/comparison-board.png)
- v273 [视频](plate/video-comparison/comparison-board.png) · [静态](plate/still-comparison/comparison-board.png) · [拼图](plate/sheet-comparison/comparison-board.png)

沿用 [v270–v271 的复现步骤](../v270-v271-front-shoulder/README.md)，以 `--inward-mm 2 --group crown` 或 `--inward-mm 2 --group plate` 生成候选，再运行保存网格导出及三组固定相机比较。候选阶段完成了 FCStd 保存读回和固定相机筛选，完整的 STEP 独立读回和 FreeCAD 原生显示核验见正式 v259 包。
