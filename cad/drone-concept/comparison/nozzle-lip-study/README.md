# v39 喷口双层口沿与垫圈

采用 C，正式 FCStd SHA-256 `ea492d3652025456d2dcf20d264cc826f46d479edaf1a9fb3742ff9dcf70ebe3`，基线 v38 为 `81ca290b2a2ab1c9cb6d9a4a1f123b66d580cb04aec0d2fba88c4c931e4435b2`。三件外观实体改变：金色卷边、金属口环、黑色垫圈；四支柱、凹舱、外罩、叶片保持。

## 取证与选择

侧视第 495 行的最外点属于金色卷边，紧邻黑色垫圈。v38 两侧该行分别超出参考 8px；卷边与垫圈的外凸会影响末端形体。

| 试件 | 金色卷边大半径 / 截面半径 / 轴向位置 | 垫圈外半径 | 金属环截面半径 | 侧缘 RMS / 最大 | 全圈 IoU |
| --- | --- | --- | --- | --- | --- |
| v38 | 53.62 / 1.7 / 94.81mm | 55mm | 2mm | 3.15096 / 8px | 84.77781% |
| A | 53.5 / 0.9 / 95.2mm | 53.5mm | 2mm | 2.39046 / 6px | 84.77886% |
| B | 52.82 / 1 / 95.6mm | 52.5mm | 2mm | 2.22004 / 5px | 84.77899% |
| C | 52.82 / 1 / 95.6mm | 52.5mm | 1mm | 2.22004 / 5px | 84.78016% |

B 的金色卷边正后方仅约 193 个可见像素，层次被原金属环遮住过多。C 收薄金属环后约 849 个像素可见，保留独立的双层口沿；[可见性数据](gold-lip-visibility.json)仅作遮挡诊断，不代表已测出参考金边面积。金属环的拟合中心线半径 52.3215mm、轴向位置 96.8067mm、偏移和轴向保持，叶片位置不动。

七张独立图均值为 81.90992%，图 05 相比 v38 增加约 0.01370 个百分点，其余六张轮廓分数相同。总体增益很小，后肩、表面曲率、叶片与材质仍需细化，未达到完整还原目标。

[汇总](review.json) · [A](a/comparison/comparison-board.png) · [B](b/comparison/comparison-board.png) · [C](c/comparison/comparison-board.png) · [C 逐图](c/stills/comparison-board.png) · [正式左后](c/detail-03.png) · [正后](c/detail-04.png) · [右后](c/detail-05.png)。正式局部板为参考、v38、v39、50% 叠加。

## 几何与连接检查

三个实体高级 BRep 检查通过。C 金色卷边与外罩布尔交叠约 58.29mm³，垫圈与外罩约 2308.44mm³；12 片叶片与金属口环仍有约 14.36～17.36mm³ 交叠。金色卷边与金属环的布尔交集返回零，尽管 8 个方位、每方位轴向 ±0.1mm 及中心共 24 个点严格位于两环材料内部。保留这个内核计算矛盾，不将零值解释为完全分离；[独立包含检查](lip-contact-check.json)同时保留原始布尔值及逐点结果。

[正式实体检查](formal-geometry-check.json)、[生成器局部操作](source-equivalence.json)与 C 候选逐件差集为零；四支柱差集为零。[保存入口](../../../../tools/refine_drone_nozzle_lip.py)保留 695 个未改 BRep 文件及 GUI 状态，转移 3 个候选 BRep，配套保留候选文档与拓扑映射；见 [archive-transfer.json](archive-transfer.json)。693 个可见对象的网格及材质记录保持。

原生 GUI 打开检查见 [native-open-check.json](native-open-check.json)。当前仍为外观示意，完整从头 GUI 重建的稳定性问题尚未解决，不作为制造或实物验收。

## 评分边界与复现

[v38 内部暗区诊断](../mask-interior-diagnostic-v38.json)显示，原始 CAD 多出像素的约一半处于参考内部闭合暗区。无差别填孔后的 91.56% 只能用于定位分割差异，因为真实孔隙、阴影和黑色材料都会被填掉；不能取代原始约 84.78% 指标、不能宣称 90% 达成，也不能据此删除实体或挖孔。

使用 FreeCAD 自带 Python 运行 `tools/experiment_drone_nozzle_lip.py`，输入 v38 保存模型和同哈希网格，指定空输出目录及 `--variant a` / `b` / `c`。保持视频与独立图相机及渲染参数不变。`tools/measure_drone_nozzle_lip.py` 检查保存实体、环截面、24 个接合探针与 12 片叶片。

候选模型、检查、渲染、叠加均保留。约 750MB 原始网格及各阶段脚本在本机缓存，路径与哈希见 [mesh-cache.json](mesh-cache.json)；其中也保存内部暗区诊断脚本。正式保存入口在输出目录写入对应哈希的 `render-meshes.json`。
