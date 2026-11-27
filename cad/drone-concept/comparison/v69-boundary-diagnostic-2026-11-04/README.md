# v69 原始轮廓差异的区域诊断

重新从 v69 保存网格渲染十方位对象 ID，绑定原固定相机与原始彩色渲染。[区域诊断板](boundary-regions-board.png)将既有多出像素按空间位置分为外侧粉色、封闭暗区橙色，缺失像素为青色。[数据](boundary-regions.json)与[原始对象归因](contour-attribution.json)均保留；原视频平均 IoU **85.553320%** 没有改变，没有另立通过分数。

十视角累计 423,779 个多出像素，其中 229,084 个位于参考掩码的封闭暗区，194,695 个在填洞参考之外。封闭暗区可能是暗材料，也可能是真实孔洞；外侧也可能包含开放提手间隙或暗边，两者均不能自动解释为几何错误，更不能据此删件。统计对同一部件在不同视角重复计数。

外侧归因前列为喷口叶片 17,891 px、底部喷口肋 11,016 px、前罩内衬 10,838 px、屏幕内框 10,021 px、前伸罩 8,981 px。下一轮优先核对这些可观察边界，结合相邻视角区分遮挡与实体边界；黑色侧扬声器内部的大量橙色区域不直接驱动缩减几何。

复现：`tools/render_drone_object_ids.py` 使用 v69 `candidate.FCStd`、`meshes.json`、`video-comparison/cameras.json` 生成本目录 ID；随后 `tools/analyze_drone_contour.py` 与 `tools/analyze_drone_boundary_regions.py` 均传入本目录 `--ids`、v69 `--renders video-renders`、`--comparison video-comparison`。所有输入哈希在清单中核对。

这是一项差异定位证据，没有图像配准、变形、改前景阈值、删部件或修改主 IoU；不证明主要部件轮廓通过 5%，也不代表制造或实物验收。
