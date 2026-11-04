# v91 前罩与小喷口根部组合候选

日期：2026-11-05

v91 是外观研究候选，基于 v90 `v90-front-cheek-contract097`，叠加 v84 的 108 个 `LowerPod*` 根部修正对象。v90 的前侧护壳收缩、v88 的喷口叶片切向收缩和 v85 的前罩变化均由候选链继承；v91 只新增这组 `LowerPod` 变化，正式入口和研究优选均不因此改变。

## 结果

固定相机、真实 CAD 三角网格、无图像变形/拉伸、无逐件配准、无删减可见零件的比较结果如下：

| 指标 | v90 基线 | v91 | 变化 |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 0.855830343136 | 0.855699623656 | -0.000130719479 |
| 静态七图平均 IoU | 0.823507546356 | 0.823322803658 | -0.000184742697 |

视频仅 1/10 方位改善、9/10 退步；静态图仅 1/7 改善、6/7 退步。因此拒绝直接组合 v84 的 `LowerPod` 根部修正与 v90 前罩收缩，保留 v90 作为当前探索候选。

## CAD 与读回

- FCStd SHA-256：`2f0ea6f5ef04cfc2f3874ce6c64023c2b037919eec8f9b446cbcd9903ad0b34d`
- STEP SHA-256：`a74dc23764000cc86bae84f90fd9ecd5a7e0732e62556128d18216d903032c7c`
- 保存对象 700 个，其中 698 个有效闭合形体；渲染网格 696 个。
- 实测平面屏几何保持；四根支柱保护检查的对称差为 0 mm³。
- `GuiDocument.xml` 存在，2094 个外观成员继承自 v90；v91 未执行新的原生 GUI 截图审计。

独立保存读回、网格绑定和渲染均通过。GUI 外观结论的范围仅覆盖继承的 v90 审计，不能描述为 v91 的原生目视验证。

## 归因与限制

视频对象级外侧边界归因中，主要差异家族包括 `NozzlePetal`、`BrowUnderside`、`LowerPodRib`、`ScreenBezel` 和 `ProjectingBrow`。`LowerPodRib` 仍是高差异来源，根部修正没有跨固定轨道泛化。90% 整机轮廓和主要部件投影偏差不超过 5% 的目标仍未完成。

本包只记录外观假设和屏幕空间诊断，不代表制造、打印、装配、光学、声学、热、电气或实物验收。不得用 v91 替换正式 v61，也不得把失败变化合入 v90。

报告入口：[candidate-review.json](candidate-review.json)、[candidate-check.json](candidate-check.json)、[readback-verification.json](readback-verification.json)、[video comparison](video-comparison/comparison-report.json)、[stills comparison](stills-comparison/comparison-report.json)。
