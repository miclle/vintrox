# v269 后肩重建筛选

在 v259 上用 `experiment_drone_rear_shoulders.py` 将左右后肩护甲的外侧 X 坐标设为 ±108 mm，重建侧状态口净空并补回两块后肩接片。四件新建或改动几何通过高级实体检查，保存读回核对了 696 个其余形体和四根支柱。候选用途为固定相机筛选，STEP 独立读回和原生颜色检查留在正式交付阶段。[实体与接合记录](candidate/candidate-check.json)

沿用 v259 的视频十方位相机。平均 IoU 从 86.008085% 降到 85.767475%，八个方位退步，最大降幅出现在 `video-08`，为 0.637293 个百分点。正式入口采用 v259。[十方位对照板](video-comparison/comparison-board.png) · [逐方位数据](video-comparison/comparison-report.json) · [渲染清单](video-renders/render-manifest.json)

本轮也复核了正式 v259 的 `still-05`。按可见对象 ID 归因，左前罩弧面内罩和左甲片分别贡献了参考外侧的 2,616 和 1,619 个像素。该统计受参考分割、锯齿和遮挡影响，用于定位可见边缘。前罩的横向仿射试件触发 `GeomAbs_C0`，原弧面内罩也能复现这类高级检查错误。该试件停在几何阶段。后续应通过局部实体重建或修整缩小这段外沿，并复查白纹、滑槽和邻接面。[对象归因](still-05-boundary.json) · [差异图](still-05-boundary-diagnostic.png)

复现时先用 FreeCAD Python 运行 `tools/export_saved_drone_meshes.py` 导出 v259 的临时网格，然后运行以下步骤。

```sh
VINTROX_BASE=cad/drone-concept/vintrox-drone-concept.FCStd
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_rear_shoulders.py \
  --base-model "$VINTROX_BASE" --base-meshes "$VINTROX_RUN/base-meshes.json" \
  --output "$VINTROX_RUN/v269" --outer-x 108 --status-clearance
```

用候选输出的 `meshes.json` 与 `candidate.FCStd` 运行 `tools/render_drone_concept.py`，传入归档的 [视频相机](../cameras.json)，再用 `tools/compare_drone_reference.py` 重建逐方位叠加和轮廓差异。静态对象归因采用同一正式 v259 模型、[静态相机](../still-cameras.json)及 `tools/render_drone_object_ids.py` 与 `tools/analyze_drone_still_boundary_regions.py`。
