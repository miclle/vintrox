# v235/v236 底壳外沿高度筛选

本轮以正式 v229 为保存 CAD 基线，固定中央 60 mm 保留带和四根支柱，只改变 `ClosedBellyPan` 外沿高度，并同步移动两侧检修板和螺钉。v235 使用 50.5 mm，v236 使用 52.5 mm。

两组候选均完成 FCStd 保存、STEP 导出、696 个可见对象读回、十视频真实 CAD 渲染和固定相机叠加差异。没有图像变形、逐件配准或省略可见零件。

| 候选 | 视频十方位平均 IoU | 相对 v229 | 结论 |
| --- | ---: | ---: | --- |
| v235，外沿 50.5 mm | 85.9131649% | −0.0025939 个百分点 | 保留 v229 |
| v236，外沿 52.5 mm | 85.9144715% | −0.0012863 个百分点 | 保留 v229 |

两组候选均退步，正式模型保持 v229。底壳高度仍属于外观拟合假设，未完成制造、装配、承力和整机物理验证。

- [筛选汇总](screening.json)
- [v235 固定相机报告](v235-belly-floor505/video-comparison/comparison-report.json)
- [v236 固定相机报告](v236-belly-floor525/video-comparison/comparison-report.json)

网格不进入 Git。候选网格可从保存 FCStd 使用 `tools/export_candidate_drone_meshes.py` 临时重建，颜色从 v229 保存 GUI 载荷读取，不依赖 GitHub LFS。
