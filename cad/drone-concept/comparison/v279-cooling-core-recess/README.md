# v279 后部鳍片暗色基座

对照正后和两侧斜后的视频近景，15 片鳍片的节距已接近参考。用现有鳍片截面重建暗色基座，固定底面高度 236 mm，分别降低基座顶部 1.5 mm 和 3 mm。两档保存读回均为有效闭合单实体，高级几何检查通过，与 15 片鳍片及后上封板均有正体积搭接。[1.5 mm 几何记录](drop-1.5/candidate-check.json) · [3 mm 几何记录](drop-3.0/candidate-check.json)

两档的十方位逐视角 IoU 均与 v276 相同，均值为 86.019486%。正后视角中，下移基座露出了槽顶后的金色壳面，参考同一位置呈暗色，因此继续采用 v276。当前检查覆盖暗槽的可见效果和保存实体，候选 STEP 与 FreeCAD 原生显示留待后续交付验证。[三方位近景](fin-recess-board.png) · [1.5 mm 视频评分](drop-1.5/comparison-report.json) · [3 mm 视频评分](drop-3.0/comparison-report.json)

复现时先用 `tools/export_saved_drone_meshes.py` 从 v276 保存模型导出临时网格。在 FreeCAD Python 环境运行本目录的 `replay.py --base <v276 FCStd> --mesh <临时网格> --output <新目录> --drop 1.5`，再用同一保存模型渲染流程重放固定视频相机。将下移量改为 3.0 mm 可复跑另一档。[固定视频相机](../cameras.json) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
