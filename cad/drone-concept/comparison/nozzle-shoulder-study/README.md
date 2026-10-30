# 喷口肩部与凹舱封板修订（2026-10-24，v32）

本轮从 v31 的真实凹舱出发，保留相同十个视频相机、光照和分割方法，比较 G、H、I 三个较圆收的喷口肩部。根部、金属口沿、出口叶片和四支柱保持不变。选择 I 后同步正式 FCStd、STEP、全部预览、逐图叠加和转台；保存读回与交付审计通过，整体目标未完成。

| 版本 | 上缘 RMS / 最大点差（px） | 两侧外缘 RMS / 最大偏差（px） | 十方位 IoU | 判断 |
| --- | --- | --- | --- | --- |
| v31 | 10.24 / 27.00 | 5.91 / 9 | 84.37622% | 宽肩遮住了凹舱中的封板侵入 |
| G | 9.48 / 27.00 | 5.31 / 8 | 84.38017% | 上缘阈值仍失败 |
| H | 7.55 / 24.41 | 4.83 / 8 | 84.38232% | 圆收改善，仍超阈值，露出两块金色封板台阶 |
| I / v32 | 6.09 / 19.24 | 4.72 / 8 | 84.38323% | 采用；修掉封板侵入，不用宽肩遮盖问题 |

根部和口沿截面保持不变，中间两截面半宽从 84/73mm 收到 70/68mm，超椭圆指数改为 2；这是外观推定，不是原作实测。六片白纹和四片警示标记重新贴合实际曲面。下部封板只切除伸入凹舱的后侧区域，保留前侧材料及两侧连接。额外六个空隙、四个内壁材料探针和三组接合检查通过。

[左后对比](../nozzle-shoulder-detail-left.png) · [正后对比](../nozzle-shoulder-detail-back.png) · [右后对比](../nozzle-shoulder-detail-right.png) · [当前上缘点位](../nozzle-fairing-check.png) · [两侧外缘](../nozzle-side-check.png) · [候选索引](review.json)

上缘 35 点保留原点位和 22.75px 阈值，但其中两点仍可能落在渐变阴影上；通过这组检查不证明它们都是物理边界。新增两侧外缘检查选取第 60/180 帧对着黑背景的 14 个行样本，联合外罩、白纹、警示牌和卷边的对象 ID，避免把贴片遮挡当成外罩边界。参考阈值 12/18/24 的边缘变化最大 1px。两组检查分开报告，均不代表完整外罩或隐藏表面精度。

v31 的局部失败保存在[历史上缘报告](../nozzle-fairing-check-v31.json)与[两侧基线](../nozzle-side-check-v31.json)。v32 相对 v31 仅改变 11 个外罩/贴片对象及下部封板，其余 709 个可见对象的网格、标签、材质属性完全一致；四支柱另用保存实体差集核对。喷口出口叶片的完整形体、后壳曲面、标记位置及材质仍需继续完善。

复现使用 `tools/experiment_drone_nozzle_fairing.py --base-model /v31.FCStd --base-meshes /v31-meshes.json --variant i --output /新目录`；g/h/i 均保留，i 同时修订凹舱下部封板。候选 FCStd 为几何专用，不替代正式交付。用原渲染器和 `comparison/cameras.json` 重建十方位，分别运行 `measure_drone_nozzle_fairing.py`、`measure_drone_nozzle_side.py`、`measure_drone_nozzle_surfaces.py` 和 `measure_drone_rear_cavity.py`；侧缘脚本要求 `--ids`、`--renders`、`--comparison`、`--output`，凹舱脚本另指定 `--baseline-model`。使用 FreeCAD 自带 Python 和 Blender。
