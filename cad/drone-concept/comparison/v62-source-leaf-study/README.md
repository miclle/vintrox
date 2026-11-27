# 喷口源叶片恢复与出口收形研究（2026-10-26）

正式模型保持 v61；本目录候选不代表正式 v62。四根支柱和其它既有形体保持不变。延续固定十方位视频与七张静态相机，真实 CAD 渲染、50% 叠加及差异图均保留，无图像变形。

## 源叶片恢复

上一轮确认历史 `transformShape` 非均匀缩放意外缩短轴向。本轮直接从 `nozzle_leaf_parts()` 恢复 12 片叶片、槽内衬、压条、侧轨、末端包边及导轨，共 96 个对象，绕过这些缩放。候选 [FCStd](source/candidate.FCStd) 与 [STEP](source/candidate.step) 保存为独立研究文件，正式模型未改。

[三视角局部放大板](nozzle-detail-board.png)依次为参考、v61、恢复源叶片。所有列使用相同裁切，裁切只用于展示，不参与分数。源叶片恢复末端位置和分瓣层次，但不同照片仍有不一致。

| 诊断 | v61 | 源叶片候选 |
| --- | ---: | ---: |
| 视频十方位平均轮廓 IoU | 85.49201687% | 85.15568813% |
| 静态七图平均前景诊断值 | 82.22681557% | 82.04254658% |
| 三视频视角 19 点末端边界 RMS | 26.41758 px | 3.11824 px |
| 五视角末端边界 RMS | 20.48772 px | 11.85071 px |
| still-04 末端边界 RMS | 14.909 px | 16.425 px |
| still-05 末端边界 RMS | 11.696 px | 15.391 px |

末端边界诊断对保存包边边线采样，匹配已有参考观察点；包含被遮挡边段，不能替代可见轮廓。视频局部改善与整体 IoU 下降同时存在，参考黑色叶片/背景分割也有歧义。保留所有视角，不因局部分数或整体分数单独决定采用。静态第 06 张是线框图，前景诊断不等于实物轮廓准确率。

[视频叠加板](source/video-comparison/comparison-board.png) · [静态叠加板](source/stills-comparison/comparison-board.png) · [v61 五视角边界](v61-tip-five-check.json) · [候选五视角边界](v62-source-tip-five-check.json)

## 接合与 STEP

96 个重建件均为有效单一闭合实体，高级 BOP 检查及保存读回通过；13 个支撑相关实体差集为零。叶片连接口环及铰接件，导轨连接凸起压条；口环通过卷边连接外罩。直接叶片/外罩或导轨/叶片间距不代表悬空，完整接合链见 [assembly-step-check.json](source/assembly-step-check.json) 与 [导轨接合](source-guide-contacts.json)。不将阴影空隙补成连续筒壁。

STEP 为 817 个有效闭合实体，696 个可见对象；与保存 CAD 复合体体积相对差约 `6.98e-7`。检查中发现直接累加单件 `Volume` 与复合体 `Volume` 在重叠装配中并非本轮验证器使用的同一口径；按现有独立验证器以复合体比较，未放宽其 `1e-6` 相对阈值。另抽查 `Part.export` 与 `Import.export`：单件导出位置行为不同，本候选 STEP 使用 `Part.export`。

## 下一档出口收形

原始源叶片在视频中接近出口圆，但两张静态图仍偏大；联合五视角稀疏拟合会牺牲视频，不能据此移动整机相机。第二档保持根部半径和轴向站位，仅沿叶片截面逐步把出口半径收小 3 mm，附件截面同步变化，已完成真实形体、接合、STEP 读回与全部固定视角。

以上均为外观研究，未验证制造、打印、承力、装配或声学。未提交、未推送。

## 中间截面：七视角末端均改善，暂作完整评审候选

末端轴向回收 6 mm、出口半径收小 1.5 mm，根部截面保持，所有叶片层次同步重建。原 0.85 mm 末端圆角在第 11 片失败，未保存半成品；显式改为 0.6 mm 后全部 96 件高级检查、单实体与保存读回通过。生成器仅增加可配置圆角并从实际末端截面读取边线选择平面，默认几何参数保持原值。

[完整候选 FCStd](mid/candidate.FCStd) · [STEP](mid/candidate.step) · [五视角放大叠加](mid-five-detail.png) · [十方位板](mid/video-comparison/comparison-board.png) · [七图板](mid/stills-comparison/comparison-board.png) · [实体/STEP](mid/assembly-step-check.json)

| 末端边界 RMS | v61 | 中间截面 |
| --- | ---: | ---: |
| video-02 | 29.601 px | 12.633 px |
| video-03，新增留出 | 14.27 px | 8.71 px |
| video-04 | 22.418 px | 9.539 px |
| video-05，新增留出 | 14.75 px | 12.60 px |
| video-06 | 29.514 px | 12.412 px |
| still-04 | 14.909 px | 10.046 px |
| still-05 | 11.696 px | 7.573 px |
| 七视角合计 | 19.297 px | 10.221 px |

新增视频第 90/150 帧的 12 个手工观察点来自可见叶片包边，名义人工不确定性约 3 px，未参与本候选参数选择；[观察点](tip-holdout-90-150.json)、[v61 读回](v61-tip-seven.json)与[候选读回](mid-tip-seven.json)保留全部距离。黑色金属边、遮挡、边厚仍可能影响判断，留出结果不证明唯一几何。七视角最大距离仍为 24.227 px，局部目标尚未通过。

视频十方位 IoU 为 **85.34736060%**，静态七图为 **82.15506092%**，分别比 v61 低 **0.14465627 / 0.07175465 个百分点**。保留这个取舍，未把局部误差改善解释为整机 90% 目标已达。四支柱及 13 个支撑对象实体差集为零；接合链通过。STEP 817 个有效闭合实体，复合体相对体积误差 `6.9893e-7`、包络最大差 `4.46e-11 mm`。

该档作为本轮优先评审候选，正式入口仍为 v61；进一步检查根部可见长度、叶片间隙及外罩遮挡后再决定写回。复现参数为 `--terminal-inset 1.5 --terminal-axial-shift -6 --corner-radius .6`。完整源叶片与收小 3 mm 的两档继续保留，避免用中间结果覆盖先前失败证据。

### 出口收小 3 mm 的结果

[候选 FCStd](inset3/candidate.FCStd)、[STEP](inset3/candidate.step)、[接合/STEP 检查](inset3/assembly-step-check.json)、[视频板](inset3/video-comparison/comparison-board.png)及[静态板](inset3/stills-comparison/comparison-board.png)已归档。视频平均 IoU **85.20158742%**、静态 **82.08235994%**，均比完整源叶片略好，仍低于正式 v61。三视频末端 RMS **3.51661 px**，五视角 **11.24027 px**；still-04/05 为 **15.017 / 14.958 px**，仍未同时优于 v61。96 个修改件高级检查通过，817 个 STEP 实体与 CAD 复合体相对体积误差约 `6.99e-7`，13 个支撑差集为零。

本阶段不采用两档候选。下一步需要联合处理叶片根部在外罩下的可见长度、出口倾角及静态投影误差，不能继续只追求末端圆或暗部掩模。

复现入口：`tools/experiment_drone_petal_source.py`（`--terminal-inset 0` / `3`）、`tools/measure_drone_saved_petal_tips.py --include-stills`、`tools/verify_drone_source_leaf_candidate.py --candidate-dir <候选目录>`，随后使用现有 `render_drone_concept.py` 与 `compare_drone_reference.py`。传入哈希绑定的基线网格；历史网格恢复先按 `MESH_ARCHIVE.txt` 只恢复所需文件。

中间候选另有五张常规预览：[整机](mid/review-renders/hero.png)、[后部](mid/review-renders/rear.png)、[正面](mid/review-renders/front.png)、[右侧](mid/review-renders/right.png)、[喷口细节](mid/review-renders/nozzle-detail.png)，渲染清单绑定候选 FCStd。
