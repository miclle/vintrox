# v283 大喷口外侧可见叶片

在 v276 的 `video-02` 和 `video-06` 对象 ID 中，沿参考口沿至叶片末端检查遮挡关系。靠外的几条采样列分别经过可见的第 6、7、9、10 号叶片。将这两对镜像叶片的末段在局部 Z 105 mm 处接续，轴向跨度放大至 1.5 倍。每 17 mm 原跨度径向外移 1.5 mm、局部 Y 偏移 2 mm。保存读回检查覆盖 24 件改动、80 项接合及 13 件支撑几何，通过有效性和接合检查，支撑差集为零。[保存几何](candidate-check.json)

| 固定相机 | v276 | v283 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.019486% | 86.058289% | +0.038802 |
| 静态七图 | 82.574760% | 82.542151% | −0.032610 |
| 拼图十格 | 89.777430% | 89.841057% | +0.063627 |

两个侧后视频视角的末端 RMS 分别由 26.52 px 降至 22.95 px、由 27.47 px 降至 23.76 px，最大采样偏差仍分别为投影屏宽的 20.96% 和 21.94%。`still-05` 下降 0.14670 个百分点。近景显示第 9、10 号叶片在该视角向背景伸出，`still-06` 的线框参考也显示局部外伸。正式模型采用 v276。候选 STEP 与原生显示尚未复核。[局部采样](visible-petal-edges.png) · [静态近景](still-delta-crops.png)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

沿用 v281 的保存模型、重建网格和渲染流程，运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 105 --factor 1.5 --tip-radial-shift 1.5 --tip-centre-shift 2 --leaf-indices 6 7 9 10`。以 v276 的三组相机重放，局部采样沿用 v257 标注。[复建流程](../v281-mirrored-petal-long-tip/README.md)
