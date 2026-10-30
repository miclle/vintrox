# 后肩与后框表面候选

2026-10-24，基线为 v33，FCStd SHA-256 `b0f4416e5e20622b93987f837b111e630973615b9968faf441cee555ba9d6635`。各候选使用相同十方位相机、渲染设置和轮廓分割规则；[汇总](review.json)保留每个模型哈希、分数与结论。候选 FCStd 仅供隔离试验，正式模型为 v34。

正后方参考的金色区域比模型窄，但这是颜色与明暗边界，尚不能当作实体边界。A/B 尝试收窄后肩并增加暗色承接件；侧后方实际渲染出现没有参考依据的深沟，因此未采用。轮廓分数略高并不代表内部形体更接近。

| 候选 | 几何变化 | 十方位 IoU | 结论 |
| --- | --- | --- | --- |
| A | 后肩外侧 X 108，增加内退承接件 | 84.52720% | 黑沟；未重切原侧状态板开口，不可直接采用 |
| B | 后肩外侧 X 100.8，增加内退承接件 | 84.53492% | 黑沟更大；同样未重切状态板开口 |
| C | 保持 X 116.76，侧端 Y 216.5，重切状态板开口 | 84.53232% | 多视角改善不明确 |
| D | C 加宽接口承接面至 201.6 | 84.51367% | 原共面重叠产生的黑缝扩大 |
| E | D 切除承接面与后框重叠部分 | 84.51367% | 黑缝消失，但增宽及曲率改变依据不足 |
| F | 原 v33 后肩和承接面尺寸，仅切除重叠 | 84.39019% | 组合外形完全保持；浅槽仍被后框填实 |
| G | F 同时将两处浅槽切入后框 | 84.39019% | 采用为 v34 |

每个目录均保存 `candidate-check.json`、`comparison-report.json`、`renders/render-manifest.json` 及 `detail-02.png` 至 `detail-06.png`。例如 [A 左后](a/detail-03.png)、[B 右后](b/detail-05.png)、[G 正后](g/detail-04.png)。数字为图像诊断，不能视为整体还原率。

## 共面诊断与采用范围

后结构框和接口承接面原来在 Y=248 有 637.94mm² 重叠面，体积交叠 10559.81mm³。对象 ID 与实际渲染将黑色 U 形缝定位到后框，F 只分离这两件后黑缝消失，组合实体对称差为零，见 [F 读回](f/overlap-check.json)。这支持将其判为重叠表面伪影，而非参考中的槽。

G 再把天线两侧既有浅槽切入后框，避免被后框填实；[候选检查](g/seam-check.json)与[正式 v34 检查](../rear-seam-check.json)记录两件有效闭合、共面及体积交叠为零、接触间隙为零、槽底有材料。组合实体仅减少两槽所需的 94.51mm³。正式模型仅这两个对象变化，其余 683 个可见对象记录一致，四支柱保存 BRep 差集为零。

[正式近景](../rear-seam-closeup.png)按参考、v33、v34、50% 叠加排列。同相机同裁剪，没有局部拉伸，也未更改材质或灯光来隐藏差异。后肩整体宽度与曲率仍未解决，喷口周边阴影继续按真实凹舱和遮挡关系判断。

## 复现

使用仓库 `tools/experiment_drone_rear_shoulders.py`，运行环境为 FreeCAD 自带 Python，`PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`。各次指定同一 v33 `--base-model`、`--base-meshes`，并使用新的空 `--output` 目录。

| 候选 | 附加参数 |
| --- | --- |
| A | `--outer-x 108` |
| B | `--outer-x 100.8` |
| C | `--outer-x 116.76 --edge-y 216.5 --no-return --status-clearance` |
| D | C 参数加 `--wide-carrier` |
| E | D 参数加 `--trim-frame-overlap` |
| F | `--outer-x 116.76 --no-return --carrier-only --trim-frame-overlap` |
| G | F 参数加 `--open-frame-slots` |

候选网格、原 v33 FCStd、原生成脚本保存在本机 `/Users/miclle/.codex/visualizations/2026/10/22/01a163d7-dc98-7ce1-af6b-9aa3d7bf5546/drone-rear-shoulders-study-cache/`，不是仓库交付依赖。固定相机与正式证据入口见[比较索引](../review-index.json)。使用 `tools/measure_drone_rear_seam.py --baseline-model <v33.FCStd>` 可从保存实体复核当前后框和浅槽；当前模型与测量脚本哈希均写入报告。
