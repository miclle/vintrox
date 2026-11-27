# v288 前侧脸颊继续收窄

在 v287 的保存模型上，将左右前侧脸颊和桥板横向再收窄 3%。四件修改形体保存读回均为有效闭合单实体。实测平面屏几何和 13 件支撑形体通过复核。[保存几何](candidate-check.json)

| 固定相机 | v287 | v288 |
| --- | ---: | ---: |
| 视频十方位 | 86.033198% | 86.028384% |
| 静态七图 | 82.574760% | 82.574723% |
| 拼图十格 | 89.782809% | 89.784647% |

视频均值下降 0.004814 个百分点，拼图均值提高 0.001838 个百分点，正式交付采用 v287。候选已导出 STEP，独立 STEP 读回和原生窗口颜色复核留待正式版本。[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

从 v287 保存模型重建网格，沿用同一候选生成流程，将 `--scale` 改为 `.97`，将 `--revision` 改为 `v288-front-cheek-x097`，并按原三组固定相机重放。[v287 复建流程](../v287-front-cheek-x0985/README.md)
