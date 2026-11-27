# v286 提手支臂倾角筛查

以 v276 的保存模型为基线，绕左右支臂根部转轴分别试验额外内倾和外倾 1.5°。支臂、内嵌面、端箍和标记共 12 件同步转动。两档均通过 14 项接合检查，高级几何检查结果与基线一致，支撑形体和原生显示数据经归档成员逐字节核对。[内倾几何](inward-1.5/candidate-check.json) · [外倾几何](outward-1.5/candidate-check.json)

| 版本 | 视频十方位 | 静态七图 | 拼图十格 |
| --- | ---: | ---: | ---: |
| v276 | 86.019486% | 82.574760% | 89.777430% |
| 内倾 1.5° | 85.993024% | 82.561156% | 89.774871% |
| 外倾 1.5° | 86.008388% | 82.563489% | 89.759527% |

内倾使视频第 00 方位提高 0.02607 个百分点，第 04、09 方位分别下降 0.08092、0.09133 个百分点。两档的三组均值均低于 v276，正式交付采用 v276。两档均生成了 STEP，独立 STEP 读回和原生窗口颜色复核尚未执行。[内倾视频](inward-1.5/video-comparison/comparison-board.png) · [外倾视频](outward-1.5/video-comparison/comparison-board.png) · [内倾静态](inward-1.5/stills-comparison/comparison-board.png) · [外倾静态](outward-1.5/stills-comparison/comparison-board.png)

从保存的 v276 导出网格，运行 `tools/experiment_drone_handle_tilt.py`，分别传入 `--angle 1.5` 和 `--angle -1.5`。用 `tools/finalize_drone_petal_axial.py` 恢复归档原生显示数据并导出 STEP。固定相机沿用 v276 的全部三组配置。[重建网格与渲染](../../../../docs/drone-concept.md#编辑与复现) · [v276 基线](../v276-front-cheek-x099/README.md)
