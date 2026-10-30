# v52 喷口警示贴片与曲面定位

2026-10-24，接续 v51 上肩形体修订，结合视频第 90、120、150 帧调整三角标记、红色内片、白色警示牌与红边条，共四个有厚度的 CAD 实体。保留外罩、后壳凹舱、出口叶片及四支柱，其余 **694 个 BRep** 原样保留。没有把凹舱阴影解释成新增筒壁。

## 固定角度对照

从左至右：参考、v51、v52、50% 叠加；不改变相机、裁切、灯光、分割阈值或支柱排除规则。

- [左后](detail-left.png) · [正后](detail-back.png) · [右后](detail-right.png)。
- [十方位比较](../iteration-86/comparison-board.png) · [七张原图比较](../stills-57/comparison-board.png)。
- [人工观察点](observations.json) · [实际 CAD 可见边界检查](marking-check.json) · [逐视角变化](review.json)。

| 检查 | v51 | v52 |
| --- | ---: | ---: |
| 三角边界 RMS，9 点 | 18.282px | 4.384px |
| 警示牌边界 RMS，23 点 | 9.276px | 1.142px |
| 十方位轮廓 IoU | 84.879237% | 84.879897% |
| 七张独立图轮廓均值 | 81.969599% | 81.970037% |

同一组人工点参与拟合，读回只说明 CAD 实现了这组拟合，不是独立精度验证。点位约有 2～4px 人工不确定性，右后牌面高光边未作为实体边界；使用最近可见边缘距离，不等于严格顶点对应。整体分数基本持平，90% 目标仍未达到。

A 版文字落点不合适；B 版文字回到牌面并放大感叹号，但右后视末字越出白牌；C 版将 WARNING 字号收至 6.2mm，保留边距。三版的四个 CAD 贴片相同，文字仅为渲染标注，未伪称 CAD 刻字。参考细小副标题无法可靠辨认，未补写内容。

## 保存与验证

[源构造、候选及保存实体检查](formal-geometry-check.json)核对四件双向布尔差、694 件保留形体、四根支柱、64 个外罩端面采样及 12 件凹舱灯具；[归档转移](archive-transfer.json)保留未改 BRep、GUI 材质和 XML 资源顺序。[原生打开](native-open-check.json)确认 700 个顶层对象、696 个可见对象及颜色读回一致。FCStd SHA-256：`73e6670b87a9ba0c572181d64a359e6706133d9186e6edcf1cf6436c7c072b07`。

正式 FCStd、STEP、九张预览、12 秒转台、十个固定视频角度、七张原图及当前局部证据已同步，见[交付报告](../../delivery-verification.json)。原有翼板的高级 BOP 问题继续保留；当前仍是外观模型，未做打印、装配或声学实测。

## 剩余差异和复现

后壳接缝、凹舱内的明暗分布、叶片末端与金属表面仍有差异；本轮没有改变这些形体。下一步继续从两侧后视检查后壳开口转折和喷口根部遮挡，不依据单幅暗边增加筒壁。

`tools/experiment_drone_nozzle_markings.py` 从精确 v51 模型与网格构造四片曲面层；`tools/refine_drone_nozzle_markings.py` 转移到正式模型；`tools/measure_drone_warning_geometry.py` 和 `tools/measure_drone_nozzle_markings.py` 分别核对实体与固定机位投影。网格、冻结源文件、日志及检查点见[缓存索引](mesh-cache.json)。未提交或推送。
