# 凹舱开口比例与灯条遮挡候选

2026-10-24，本轮试验时正式模型为 v34，SHA-256 `45e97d81bd5025dedb19005a96258059c1795555af5e14cb8b159c950a528c98`。本轮保存五个真实 CAD 候选及固定十方位渲染；B、E 另渲染全部七张独立参考图。这五个候选当时未直接替换正式 FCStd、STEP 或其预览；后续灯条细化已采用为 v35，见[后续记录](../cavity-emitter-study/README.md)。

## 依据与结果

正后方原模型的外侧青色亮边偏宽，下边偏高。以固定扫描行检查正后、左后、右后三个视角的 12 处外侧亮边；这是发光区域位置诊断，不把喷口周围阴影当成实体轮廓。所有候选保留喷口和四根支柱，只修改后部面板、内衬、灯框和下封板四个对象。

| 候选 | 开口宽 / 底部 Z / 顶部 Z（mm） | 额外灯带后退 | 灯条位置 RMS / 最大偏差（px） | 结论 |
| --- | --- | --- | --- | --- |
| v34 | 144 / 80 / 190 | 0 | 6.09 / 9.50 | 当前正式基线 |
| A | 134 / 74 / 192 | 0 | 3.47 / 5.00 | 收窄偏多 |
| B | 138 / 76 / 192 | 0 | 1.40 / 2.50 | 开口比例较合适，连续灯框仍需处理 |
| C | 138 / 76 / 192 | 6mm | 5.93 / 8.50 | 侧后方亮边偏移，未采用 |
| D | 138 / 76 / 192 | 12mm | 11.33 / 16.50 | 位置和可见性变差，未采用 |
| E | 138 / 76 / 192 | 0 | 1.40 / 2.50 | 去除 Z=94～139mm 的发光段，作为分段解释的候选 |

尺寸均为外观推导，未冻结为制造尺寸。五个候选的整圈轮廓 IoU 都为 84.39019%，与 v34 相同，因为变化位于外轮廓内部。E 与 B 的扫描行得分相同：扫描行没有覆盖被切除的中段，因此该指标不能支持分段灯条的正确性。

[汇总](review.json) · [原模型亮边诊断](baseline-light-check.json) · [B 诊断](b/light-check.json) · [E 诊断](e/light-check.json)。扫描行算法固定使用 G−R、B−R 色差及亮度阈值，报告保留 20/25/30 三档敏感性；选择最外侧至少两个连续青色像素的中心。白色饱和、泛光和双条结构可能影响中心，不能解释为精确物理尺寸。

## 同角度比较

- B：[左后](b/detail-03.png)、[正后](b/detail-04.png)、[右后](b/detail-05.png)、[十方位](b/comparison/comparison-board.png)、[七张独立图片](b/still-comparison/comparison-board.png)。
- E：[左后](e/detail-03.png)、[正后](e/detail-04.png)、[右后](e/detail-05.png)、[十方位](e/comparison/comparison-board.png)、[七张独立图片](e/still-comparison/comparison-board.png)。

局部板按参考、v34、候选、50% 叠加排列，保持原相机与相同像素裁剪。E 去掉中段后，正后方过于完整的发光 U 形减弱，但不能只凭这个效果决定源结构。[参考 04 原图](../../../../references/alexander-shevchuk-drone/alexander-shevchuk-04.jpg)还能看到成对亮条、端部和压座；部分亮段也可能被喷口遮挡。E 的切断高度是待检验假设，直切端部和单条截面尚不接近这些细节，不合入正式模型。

## 保存实体检查及限制

每个候选的 `candidate-check.json` 保存四个修改对象的有效性、保存后所有几何签名、四支柱对称实体差集及三组凹舱接合；未修改对象的保存签名一致，四支柱差集均为零。E 的灯框为两个闭合实体，其余候选灯框为单实体；候选 FCStd 没有 GUI 状态，不是正式交付文件。

[穿插检查](interference-check.json)额外发现：v34 灯框与喷口壳体交叠约 77.18mm³，B、E 约 98.95mm³。后退灯带没有单调消除此交叠。这里包含被遮挡的上、下横段，体积值本身不能证明可见伪影的位置；也不能将灯带分段误称为已经消除穿插。面板、内衬和下封板还有记录在同表的隐藏交叠，未完成装配净空验收。

下一步以 B 开口尺寸为候选，结合参考 04 和旋转视频区分双灯条、压座及被喷口遮挡的部分，再构造独立闭合零件。保持真实喷口形体及四支柱，先验证三个后方视角和独立近景，再更新正式模型及整套交付证据。

## 复现

在仓库根目录使用 FreeCAD 自带 Python，设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，运行 `tools/experiment_drone_cavity_proportion.py --base-model <v34.FCStd> --base-meshes <v34-meshes.json> --output <新的空目录> --width <宽度> --bottom <底部 Z> --top <顶部 Z>`。C/D 追加 `--light-recess 6/12`；E 追加 `--split-light`。

使用现有 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py`，视频相机为 `comparison/cameras.json`，独立图片相机为 `comparison/stills-39/cameras.json`。亮边检查运行 `tools/measure_drone_cavity_light.py --renders <候选/renders> --reference cad/drone-concept/comparison/iteration-68 --output <报告.json>`；穿插检查使用本目录 [check-interference.py](check-interference.py)，在仓库根目录运行。

本机基线、候选网格和三版生成脚本保存在 `/Users/miclle/.codex/visualizations/2026/10/22/01a163d7-dc98-7ce1-af6b-9aa3d7bf5546/drone-cavity-proportion-study-cache/`。三个历史脚本 SHA-256 均与相应候选报告核对一致；缓存不作为仓库交付依赖。当前生成脚本保留此前参数的默认行为。
