# v58.1 后肩回接候选复核

## 目的

在固定视频/静态相机下，为 `outer_x=100.8 mm` 的后肩收窄候选补充 `RearShoulderReturn` 回接板，检查后肩与 `SideGuard` 的 3.81 mm 脱离是否可以修复，同时保持四根支柱不变。

## 结果

- 候选 FCStd：`iteration-119-rear-shoulder-return-candidate/candidate.FCStd`
- 后肩与侧护板的回接实体已生成；四根支柱对正式 v58 的实体差集均为 `0 mm³`。
- 视频十视角平均 silhouette IoU：`0.8524297568`。
- 静态七视角平均 silhouette IoU：`0.8215324677`。
- 对照的 v58 后肩收窄候选分别为 `0.8544878353` 与 `0.8222507724`。
- `video-00/03/04/05/08` 和静态 `still-01/02/04/05/06` 出现轮廓回退；回接板增加了可见外轮廓面积。

## 决策

该候选拒绝写回正式模型。正式 `vintrox-drone-concept.FCStd` 保持 v58 折角半径 24 mm，四根支柱保持不变。凹舱暗边仍按后退内衬、侧壁和灯座的遮挡阴影处理，不将其补成连续喷口筒壁。

## 证据

- `iteration-119-rear-shoulder-return-candidate/candidate-check.json`
- `iteration-119-rear-shoulder-return-candidate/video-comparison/comparison-report.json`
- `iteration-119-rear-shoulder-return-candidate/stills-comparison/comparison-report.json`
- 同目录的 `video-comparison-board.png` 与 `stills-comparison-board.png`

这些指标只用于相同相机下的外观轮廓筛选，不代表制造、装配、承力、声学或热验证。
