# v38 喷口中段曲面收浅

正式采用 C，FCStd SHA-256 `81ca290b2a2ab1c9cb6d9a4a1f123b66d580cb04aec0d2fba88c4c931e4435b2`，基线为 v37 `7f4ec530e66b181094d4efa1876d35252e6784d4de209718d70129c27d4c9709`。

## 形体与对比

原外罩在第 60/180 帧的侧视中段向外鼓出约 3～7px。本轮只收浅两中间截面，根部截面 `(0,49,49,0)`、出口截面 `(94.81,53.82,53.82,-1.15)`、轴向位置、卷边和叶片保持。选择的中间截面为 `(28,70,63,-1)` 与 `(60,68,63,1)`，依次为轴向位置、横向半径、纵向半径、纵向偏移，单位 mm；是外观推定而非原作测绘尺寸。

六条白纹和四片警示标记重新与曲面相交生成，显示文字平面移到对应贴片外侧。凹舱、后肩、侧框和四支柱不动，不把凹舱阴影识别成新的筒壁。

| 试件 | 中段收浅 | 全圈 IoU | 侧缘 14 点 RMS / 最大 | 上缘 35 点 RMS / 最大 |
| --- | --- | --- | --- | --- |
| v37 | 0 | 84.76776% | 4.72077 / 8px | 5.77927 / 18px |
| A | 2mm | 84.77641% | 3.39116 / 8px | 5.93296 / 18px |
| B | 4mm | 84.77603% | 3.35942 / 8px | 6.05687 / 17px |
| C | 3mm | 84.77781% | 3.15096 / 8px | 5.93777 / 17.46425px |

C 的中段 12 点 RMS 为 0.95743px，左右误差更均衡；完整 14 点指标仍保留末端卷边的两个 8px 误差，没有删点或换阈值提高分数。上缘点位含遮挡与渐变阴影，RMS 略退步，不能当作完整实体轮廓的精确边界。全圈增幅只有 0.01004 个百分点，主要改善是中段曲率，远未达到 90% 目标。

[汇总](review.json) · [A 比较](a/comparison/comparison-board.png) · [B 比较](b/comparison/comparison-board.png) · [C 比较](c/comparison/comparison-board.png) · [正式左后](../nozzle-depth-detail-left.png) · [正后](../nozzle-depth-detail-back.png) · [右后](../nozzle-depth-detail-right.png)。正式局部图列为参考、v37、v38、50% 叠加。

## 后肩退步归因与未采用试验

[对象 ID 归因](still-03-regression-attribution.json)确认 v37 在独立图片 03 丢失的 2014 个参考前景像素主要属于右后肩（1767）和侧护框（240），不是此前推测的侧前护板。归因使用相同 960×823 等比例 LANCZOS 缩放、轮廓阈值与原比较相机，只用于定位。

[后肩加饱满试验](../rear-bow-study/README.md)虽改善图片 03，却使其余六张独立图与视频均值下降，两档均未采用。后肩形体继续保留 v37，后续需进一步核对分高度截面和遮挡。

## 交付检查与复现

11 个改变零件通过高级 BRep 检查；[正式模型与 C 候选](formal-geometry-check.json)、[生成器局部操作与 C](source-equivalence.json)逐件实体差集为零，四支柱实体差集为零。六组外罩/贴片/卷边/后箍接合检查通过，低音占位与外罩无体积相交。原生 GUI 打开检查见 [native-open-check.json](native-open-check.json)。

[保存入口](../../../../tools/refine_drone_nozzle_depth.py)保留 687 个未改 BRep 文件及原 GUI 数据，转移 11 个候选 BRep，配套保留候选文档与拓扑映射；见 [archive-transfer.json](archive-transfer.json)。685 个可见对象网格与材质记录不变，注释位置参数随喷口贴片修订。完整从头 GUI 重建的 OCCT 稳定性问题仍未解决；当前不作制造、声学或实物验收。

候选生成入口 `tools/experiment_drone_nozzle_depth.py` 使用 FreeCAD 自带 Python，指定 v37 的 `--base-model`、对应 `--base-meshes`、空的 `--output`，再传入 `--depth-reduction 2` / `4` / `3`。全部使用固定 `comparison/cameras.json` 渲染，并检查 `measure_drone_nozzle_side.py`、`measure_drone_nozzle_fairing.py` 与 `measure_drone_nozzle_surfaces.py`。

候选模型、检查和叠加保留在目录中，原始网格与当时脚本版本保存于本机缓存，路径和哈希见 [mesh-cache.json](mesh-cache.json)。正式保存入口在输出目录生成 `render-meshes.json`；复现时保持对应模型哈希。

正式七张独立图诊断均值 81.90136%→81.90796%，图 05 增加 0.04618 个百分点，其余六张轮廓分数保持；不据此宣称贴片、曲面与材质完全相同。正式读回为 696 个可见对象、805 个 STEP 实体、700 个中文顶层对象，STEP 体积相对差约 4.90×10⁻⁸。
