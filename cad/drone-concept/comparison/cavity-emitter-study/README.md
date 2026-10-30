# 凹舱灯条、反射背板与压座

2026-10-24，以 v34 为基线，在上一轮 B 的 138 × 116mm 凹舱开口上比较灯条构造。正式采用 `curved` 为 v35；不是将暗边当作喷口筒壁，也没有修改喷口本体或四支柱。

## 亮带与反光的区分

视频第 90 帧、Y=435 的主亮条像素约为 RGB(233,252,255)，相邻较暗带约为 (101,203,189)。第 150 帧也有相似亮暗差。[原像素及拟合记录](primary-rail-fit.json)保留三个视角的 RGB 扫描行。次亮带可能是金属内壁中的反射，单凭两条亮带不能推断两根实体灯管。

四处主亮条中心拟合出镜像竖轴 |X|≈65.37mm、Y≈236.50mm，拟合 RMS 0.24 像素；同三个视角另八行的 RMS 0.32 像素。人工中心不确定性约 2 像素，镜像、竖直轴线及隐藏端部均为外观假设；额外扫描行不是独立视角验收。

| 候选 | 实际几何 | 判断 |
| --- | --- | --- |
| single | 每侧一根圆头灯条、金属背板和上下压座，灯框拆开 | 已出现内侧较暗反射条；上压座尚有约 0.069mm 间隙 |
| dual | 在 single 后方另增一根灯条 | 未见明确多视角收益，新增灯条与喷口穿插；不采用 |
| curved | 单灯条两端弯回背板，压座接合修正；按喷口实体包络清除穿插，拆成四个独立灯角 | 采用为 v35 |

[候选汇总](review.json) · [单灯条与双灯条近景](emitter-hypotheses-left.png)。此近景从左到右是参考、single、dual、dual 的 50% 叠加。采用单灯条只是当前更有支持的外观解释，不证明原作实际灯具数量。

## 同相机验证

- single：[左后](single/detail-03.png)、[正后](single/detail-04.png)、[右后](single/detail-05.png)。
- dual：[左后](dual/detail-03.png)、[正后](dual/detail-04.png)、[右后](dual/detail-05.png)。
- curved：[左后](curved/detail-03.png)、[正后](curved/detail-04.png)、[右后](curved/detail-05.png)、[十方位](curved/comparison/comparison-board.png)、[七张独立图片](curved/still-comparison/comparison-board.png)。
- 正式 v35：[左后](../cavity-lighting-detail-left.png)、[正后](../cavity-lighting-detail-back.png)、[右后](../cavity-lighting-detail-right.png)。

正式局部板为参考、v34、v35、50% 叠加，所有候选沿用相同视频相机、光照和渲染器。新增零件使用现有金属/发光材质，没有专门调灯或图像变形。正式保存对象 ID 渲染的 12 行主亮条可见中心 RMS 为 1.40 像素、最大 2.50 像素，见[测量](../cavity-rail-check.json)。这与上一轮“最外侧青色边”是不同测量对象，不直接用相同数值宣称改善倍率。

整圈 IoU 仍为 84.39019%，因为主要变化位于外轮廓内部。金色喷口表面、警示标记、叶片金属层次和后肩形体仍有差异。

## 保存实体与采用范围

正式模型修改 `RearServicePanel`、`RearRecessLiner`、`RearCyanFrame`、`RearLowerSlope` 四个对象，并新增 11 个灯光相关对象；其他 681 个可见对象的网格、颜色和材质记录一致。696 个可见对象、805 个 STEP 实体，700 个顶层对象全部中文显示名。

[保存灯光检查](../cavity-emitter-check.json)覆盖四个灯角、两根主灯条、两块反射背板、四个压座：12 件均为有效闭合单实体，与喷口外罩的交叠体积为零；14 组连接的间隙小于 0.01mm 且有正体积交叠。新增灯光构件按外罩外表面放大 0.3mm 的包络裁让空间，四角单独建模；没有改动喷口来隐藏相交。

[正式与候选几何核对](formal-geometry-check.json)确认 15 个修改/新增对象的保存 BRep 对称体积差均为零。四支柱与 v34 的对称实体差集也为零。壁厚及隐藏连接只是外观示意，灯条与压座的交叠不等于制造装配接口；面板、内衬和下封板仍有先前记录的隐藏交叠，不将本次检查扩展为整机无穿插。

## 复现

在仓库根目录，使用 FreeCAD 自带 Python，设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`。运行 `tools/experiment_drone_cavity_emitters.py --base-model <v34.FCStd> --base-meshes <v34-meshes.json> --output <新目录>` 创建 single，追加 `--dual` 创建 dual，追加 `--curved` 创建采用候选。

`tools/fit_drone_cavity_rail.py` 重算主亮条轴线；`tools/measure_drone_cavity_rail.py --ids <对象 ID 目录>` 读取实际可见亮条；`tools/measure_drone_cavity_emitters.py --model <FCStd> --output <报告.json>` 核对闭合实体、喷口穿插和连接。正式构造在 `tools/drone_concept.py` 的 `rear_cavity_lighting` 中。

候选网格和两版生成脚本的本机归档位于 `/Users/miclle/.codex/visualizations/2026/10/22/01a163d7-dc98-7ce1-af6b-9aa3d7bf5546/drone-cavity-emitter-study-cache/`，不作为仓库交付依赖。候选 FCStd 无 GUI 状态；正式交付仍以仓库主 FCStd、STEP 及哈希绑定的报告为准。
