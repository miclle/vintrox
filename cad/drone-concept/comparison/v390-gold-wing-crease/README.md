# v390 金色右翼折线转角

在原始 940 × 800 视频的第 207–213 帧，第 319 行可以追踪两条独立边界。翼面折线从 x=635 移到 666，右翼外缘从 x=694 移到 718。第 210 帧两者分别为 651 和 707。旧轮廓标注 x=698 落在翼面内，保留在既有验收记录中。[相邻七帧](adjacent.jpg) · [窗口与逐行坐标](scanlines.json)

在 v388 的右翼漆面、凸面和折面上，将第二处内部控制点改到局部 (Y, Z) = (132.02, 230.14) mm，沿转角两侧分别插值曲线。这个坐标由第 180、210 帧的转角估算。翼尖、轮毂、外围轮廓站位沿用 v388。三个新实体通过 FreeCAD 高级几何检查，六处接合距离均小于 0.01 mm。[几何重建](replay.py) · [接合距离](joints.json)

在两帧的第 290–360 行每隔 5 px 取一条扫描线。各图在相同的 25 px 窗口内取相邻像素 RGB 梯度最大处，线性插值搜索窗口的中心。第 180 帧折线横坐标的均方根偏差由 4.97 降至 3.37 px，第 210 帧由 4.67 降至 3.26 px。该测量反映折线附近的明暗变化，参考上的暗边宽度与渲染仍有差异。逐点窗口含转角拟合用的两帧，不能支持整翼 5% 达标。[两帧近景，左起为参考、v388、v390](crease.jpg)

冻结相机复测视频十方位平均 IoU 为 86.09500%，静态七图为 82.64437%，拼图十格为 89.93633%。独立静态第 03 图上，转角仍低于且偏向参考左侧，第 04 图上的暗边也有明显的深浅差异。本轮保存为研究候选，正式版采用 v388。[静态 03](still-03-check.jpg) · [静态 04](still-04-check.jpg) · [视频](video.json) · [静态](still.json) · [拼图](sheet.json)

从仓库根目录使用 FreeCAD Python，将 tools 加入 PYTHONPATH。运行本目录 replay.py，向 --model 传入 v388 FCStd，--output 指向新目录。用 tools/restore_candidate_display.py 从 v388 恢复保存颜色，以候选 FCStd 的 SHA-256 更新临时概念清单，运行 tools/export_saved_drone_meshes.py 导出完整网格。使用 tools/render_drone_concept.py 和 tools/compare_drone_reference.py 重放 comparison 下的 cameras.json、still-cameras.json 和 contact-sheet-cameras.json。本候选未独立导出 STEP。
