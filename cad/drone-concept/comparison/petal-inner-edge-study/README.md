# v52 喷口叶片内缘形体试验

2026-10-24。正式模型继续保持 v52；本轮两组真实 CAD 试件均未采用。试验针对侧后方喷口末端的黑色延伸和内缘层次，四根支柱、后壳、凹舱、外罩、实际屏幕及出口外圆保持。

## 先区分形体与阴影

[连续视频第 90～160 帧](reference-inner-edge-sequence.png)确认：参考也能看见喷口背侧叶片和下方开口，并非模型独有的多余筒壁。不能根据黑色区域直接截短叶片或封住开口。[来源与同像素裁切记录](reference-inner-edge-sequence.json)保存视频/帧哈希；[三方向参考与 v52](baseline-inner-edge.png)为共同裁切、共同二倍展示，未作非刚性变形。

较明确的局部差异是末端亮边：参考可见分片窄边与不均匀反光，模型内侧则是大块黑面及少量竖向反光。亮边不能直接提供折边宽度或原作截面，以下尺寸均为外观假设。

## 两组实际几何

| 试件 | 形体变化 | 十方位 IoU | 七张原图均值 | 选择 |
| --- | --- | ---: | ---: | --- |
| 正式 v52 | 原有叶片 | 84.879897% | 81.970037% | 保持 |
| bevel065 | 0.65mm 内缘倒角，12 片 | 84.884453% | 81.972862% | 不采用 |
| return15 | 向内折回 1.5mm、轴向厚度 0.8mm 的短边，12 片 | 84.879795% | 81.970037% | 不采用 |

倒角由末端内弧起选，OCCT 沿相切边传播到整圈内缘，实际每片削去约 22～24mm³，并非只倒末端一条边。相同机位下没有明显解决参考亮边；约 0.00456 个百分点的轮廓增幅不足以证明外观更接近。

内折边从圆角以内起止，向原叶片内搭 0.5mm 并融合，保持开口、外圆和分片间隙，没有增加封口筒壁。它带来真实内缘层次，但仍未重现参考的亮边分布，外观改善不足以替换正式模型；十方位微降约 0.00010 个百分点，七图均值保持。所有视角的增减完整保留在[读回与逐视角结果](review.json)。

## 固定相机叠加

四联图依次为参考、正式 v52、试件、50% 叠加；相机、照明、材质、分割阈值和支柱排除规则保持。文字和其他表面未调整。

- 倒角：[左后](bevel065/detail-left.png) · [正后](bevel065/detail-back.png) · [右后](bevel065/detail-right.png) · [十方位](bevel065/video/comparison-board.png) · [七张原图](bevel065/stills/comparison-board.png)。
- 内折边：[左后](return15/detail-left.png) · [正后](return15/detail-back.png) · [右后](return15/detail-right.png) · [十方位](return15/video/comparison-board.png) · [七张原图](return15/stills/comparison-board.png)。

当前证据只支持“这两种内缘几何单独改变的收益不足”，不能证明参考一定没有折边，也不能证明剩余差异全部来自材质。下一步分别核对叶片表面反光、末端边界以及后壳开口转折，避免为解释阴影不断改变已对齐的外圆。

## 验证及复现

每个试件仅改变 12 片主叶片，其余 686 个非空形体签名保持；两组共 24 个保存实体高级检查及 8 次支柱双向布尔差检查见 [review.json](review.json)。出口外圆半径保持 43.6mm，原 19 个参考观察点的连续圆距离 RMS 保持约 3.298px；连续圆会跨越分片间隙，不代表整件精度。

试件是几何研究文件；渲染使用与其哈希绑定的真实保存网格及基线颜色，不作为正式 GUI/STEP 包。正式 FCStd、STEP、预览和交付验证均保持 v52，哈希 `73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07`。未制造验证，未提交或推送。

使用 FreeCAD 内置 Python 与库路径，运行 `tools/experiment_drone_petal_inner_edge.py --base-model <精确 v52> --base-meshes <对应网格> --width .65 --method bevel --output <空目录>`；折边改用 `--width 1.5 --method return`。`diagnostic-scripts/review-candidate.py --candidate <试件目录>` 重跑十方位与七图；`diagnostic-scripts/verify-study.py` 读回保存形体。倒角原始脚本与模块在其目录内冻结；恢复网格路径见[缓存索引](mesh-cache.json)。
