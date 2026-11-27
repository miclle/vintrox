# v53 侧后壳与喷口暗部试验

2026-10-25，本轮沿用 v53 的十个视频相机、相同渲染分辨率与参考分割，专门检查侧后方后壳、喷口容纳空间和暗部边界。四根支柱、喷口外罩、叶片和屏幕均保持；候选都是从精确 v53 FCStd 保存出的真实 FCStd/STEP，并做独立读回。

## 基线

[v53 十方位叠加板](v53-baseline-comparison-board.png) · [比较报告](v53-baseline-comparison-report.json)

视频十方位平均轮廓 IoU 为 **85.030261%**。这是固定相机下的外轮廓诊断，不是细节相似度或制造验收。

## 候选 A：后壳面板与凹舱背板横向内收 2 mm

[候选叠加板](candidate-rear-shadow-inset2/comparison-board.png) · [后视角 03](candidate-rear-shadow-inset2/video-03-comparison.png) · [后视角 04](candidate-rear-shadow-inset2/video-04-comparison.png) · [后视角 05](candidate-rear-shadow-inset2/video-05-comparison.png) · [后视角 06](candidate-rear-shadow-inset2/video-06-comparison.png) · [候选检查](candidate-rear-shadow-inset2/candidate-check.json)

候选只改变 `RearServicePanel` 与 `RearRecessLiner` 的 X 半宽，喷口和四支柱不动。平均 IoU 为 **85.031174%**，仅增加 **0.000913 个百分点**；video-06 略有改善，其它视角基本不变。这个变化不足以说明后壳外轮廓或暗部形体更接近，因此不采用。

凹舱仍以独立的平面/斜面容纳空间表示，不能把其中的暗边当作喷口圆筒壁。

## 候选 B：喷口内盆径向收小 3 mm

[候选叠加板](candidate-nozzle-cone-shrink3/comparison-board.png) · [后视角 03](candidate-nozzle-cone-shrink3/video-03-comparison.png) · [后视角 04](candidate-nozzle-cone-shrink3/video-04-comparison.png) · [后视角 05](candidate-nozzle-cone-shrink3/video-05-comparison.png) · [后视角 06](candidate-nozzle-cone-shrink3/video-06-comparison.png) · [候选检查](candidate-nozzle-cone-shrink3/candidate-check.json)

候选只重建 `BassVisualCone` 的真实凹盆截面，保留喷口外罩、叶片、连续喉部和四支柱。十方位轮廓 IoU 与基线的差异只有 0.000913 个百分点，且没有稳定的逐视角收益，说明该区域大多被外罩和叶片遮挡；没有足够证据继续收小或把阴影解释成筒壁，因此不采用。

## 本轮结论

正式模型保持 v53，SHA-256 为 `aa3de1dc9dcea5a511dd01cfba77d394fdd4a178254d170eb1f1bc369c0389b4`。本轮没有覆盖正式 FCStd，也没有改变四根支柱。下一轮若继续，应针对 `RearArmourCheek`/`MainEnclosureShell` 的可见折面做局部曲面拟合，并把材质阴影与几何轮廓分开评审。
