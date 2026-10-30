# v37 后壳安装平面与侧视轮廓研究

正式采用 C；模型版本 `v37-reprojected-rear-side-profile`，哈希 `7f4ec530e66b181094d4efa1876d35252e6784d4de209718d70129c27d4c9709`。基线为 v36，哈希 `646ed03b39c7454cac7166f4d80a03b07ac0b80422caac1442e5a90fbbeab66f`。这是一轮外观几何研究，非制造尺寸确认。

## 固定比较条件

沿用十方位视频相机与七张独立图相机，CPU 比较渲染、轮廓阈值及支柱排除范围不变。以第 180 帧相机眼点 `(1100.478706826763, 481.9590609254328, 317.0386845391606)`，将原假定的 X=116.76mm 平面轮廓投影到新的平行面。v36 已整体内收 4mm，因此先还原这个偏移，再在真实 CAD 中统一缩放和移动；不改变任何比较图片。

后肩内侧 X=89mm、后方 Y=248mm 与折转高度 Z=134mm 保留，外侧边界按新侧框重建放样。固定侧控件不移动，开口重新裁切；护框局部缺口前缘为 Y=212mm。喷口、凹舱、线束、侧圆环、实测屏幕与四支柱不动。

| 候选 | 外侧 X / 局部比例 | 十方位 IoU | 侧框外缘 RMS | 连接检查与选择 |
| --- | --- | --- | --- | --- |
| v36 | 112.76mm / 未重算 YZ | 84.57358% | 4.50157px | 基线 |
| A | 108mm / 1.0089049847 | 84.76776% | 2.65225px | 提手间隙 3.71811mm，不采用 |
| B | 102mm / 1.0150042892 | 84.86114% | 2.65247px | 提手间隙 9.73482mm，前侧桥接约 2.74139mm，不采用 |
| C | 108mm / 1.0089049847 | 84.76776% | 2.65225px | 保留原提手安装面，提手及前侧桥接间隙为零，采用 |

B 初次高级 BRep 检查在 `SideGuardLeft` 出现 `BOPAlgo_InvalidCurveOnSurface`；将裁切后的护框重新参数化为 NURBS 后仍执行相同高级检查，才得到可比较试件。C 不需要这个附加处理。没有跳过或放宽有效性检查。

## 改善与剩余差异

C 的十个视频方向均略有改善，整圈增幅 0.19418 个百分点；并未达到 90%。七张独立图诊断均值从 81.85921% 到 81.90136%，但图 03 降低 0.51640 个百分点。图 04 / 05 分别提高 0.18419 / 0.00353 个百分点；图 06 是线框图，不能视为实体还原率。后续对象 ID 归因将退步定位到右后肩 1767 个、侧护框 240 个参考轮廓像素，修正了此前对侧前护板的猜测；见 [归因证据](../nozzle-depth-study/still-03-regression-attribution.json)。继续处理后肩横截面、喷口曲率与材质。

局部统一缩放同时使板厚、灯条半径等增大约 0.89%，属于外观假设。后壳收窄不能替代喷口曲面本身的细化。凹舱暗区保留为空腔与遮挡，没有按黑影轮廓添加筒壁。

- [A](a/comparison/comparison-board.png)、[B](b/comparison/comparison-board.png)、[C](c/comparison/comparison-board.png)保留各自真实模型、渲染与叠加。
- [正式左后](../rear-profile-detail-left.png)、[正后](../rear-profile-detail-back.png)、[右后](../rear-profile-detail-right.png)依次为参考、v36、v37、50% 叠加。
- [汇总数据](review.json)记录每个方向增减；[第 03 张正式叠加](../stills-42/still-03-overlay.png)保留退步证据。

## 保存与验证

24 个既有对象修改，无对象增删；672 个可见对象网格及材质逐字段保持。四根支柱布尔对称差集为零。C 的 24 件高级检查通过；原提手安装面约 26.54mm³ 交叠，状态板五视角 75 条采样线无遮挡。生成器局部操作与 C 的几何差集为零，见 [source-equivalence.json](source-equivalence.json)。

[增量保存脚本](../../../../tools/refine_drone_rear_profile.py)保留 v36 的 674 个未改 BRep 文件及 GUI 数据，转移 C 的 24 个 BRep，并保留候选匹配的文档与拓扑映射元数据；见 [archive-transfer.json](archive-transfer.json)。随后独立 FreeCAD 读回导出 STEP，[正式实体核对](formal-geometry-check.json)和[原生 GUI 打开](native-open-check.json)通过。700 个顶层中文对象、696 个可见对象、805 个 STEP 实体；STEP 体积相对误差约 5.07×10⁻⁸。

原生 GUI 完整重建仍有前序 OCCT 崩溃问题，本轮验证的是保存转移和局部生成操作，未宣称完整重建稳定性已恢复。既有未改线束的高级曲面缺陷也未扩大为本轮修复。

## 复现入口

使用 FreeCAD 自带 Python 与库路径。候选生成脚本为 `tools/experiment_drone_rear_profile.py`；传入 `--base-model`、`--base-meshes`、`--cameras`、空的 `--output` 及 `--outer-x 108 --preserve-handle-seats` 可复现 C。A 不加最后一个开关；B 使用 `--outer-x 102 --normalize-guard`。

原始候选网格和当时脚本版本移至本机缓存，避免将约 750MB 可再生 JSON 留在仓库；路径与 SHA-256 见 [mesh-cache.json](mesh-cache.json)。三个候选保存模型、检查、参考、渲染、叠加及分数仍在本目录。正式渲染网格由保存入口写入输出目录的 `render-meshes.json`。

交付审计最初仍按旧版灯管半径 1.8mm、弯曲中心线半径 4mm 判定，因真实缩放后的 1.816029mm、4.035620mm 报错。审计现按固定第 180 帧相机与 X=108mm 方案独立计算比例，再严格核对这两个半径；没有放宽阈值或跳过检查。
