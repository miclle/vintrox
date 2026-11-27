# v260 黄翼 v259 重放筛选

从当前正式 v259 保存模型重建黄翼金属包边、内侧彩色面、后缘折面、抬高面和外侧彩色面。后缘局部坐标最大内收 5 mm，前缘第 1 至 4 站偏移为 `.5 5.5 2.5 2` mm。实测平面屏、外挂筒、屏幕侧控件、格栅和四根支柱保持。

候选实体通过高级几何检查和接合检查。三组固定相机均使用保存 CAD 的真实三角网格、相同相机和相同分割规则，排除范围仅为新增四支柱及其附属件。视频十方位均值由 86.008085% 变为 86.008441%，静态七图由 82.574342% 变为 82.574405%，拼图十格保持 89.772706%。变化处于渲染与三角化噪声量级，候选不进入正式模型，v259 继续作为入口。

对象级诊断显示视频外溢主要集中在 `NozzlePetal`、`LowerPodRib`、`BrowUnderside` 和 `ScreenBezel`。`still-05` 外溢主要集中在 `ClosedBellyPan`、`ControlRail`、`BottomChassis`、`BassVisualCone` 和 `WingFoldFacetLeft`。[视频诊断](video-diagnostic/boundary-regions-board.png) · [静态诊断](still-05-boundary-regions-diagnostic.png)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](still-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png) · [评分记录](candidate-review.json)

候选 FCStd 和 STEP 保留用于审阅。渲染网格不重复存储，可由候选 FCStd 重建。重放示例如下。

```sh
PACKAGE=cad/drone-concept/comparison/v260-gold-wing-v259-screening
TMP=$(mktemp -d)
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  tools/export_saved_drone_meshes.py \
  --model "$PACKAGE/final/candidate.FCStd" \
  --manifest cad/drone-concept/concept-manifest.json \
  --output "$TMP/meshes.json"
```

候选来源脚本为 `tools/experiment_drone_gold_wing_outline.py`。完整候选保存读回由 `final/candidate-check.json` 绑定，正式入口的颜色、可见性和交付验证继续由 v259 包及 `tools/verify_drone_current_delivery.py` 覆盖。参考曲面屏与实测平面屏、遮挡区域和人工翼板样点仍有识别限制，整圈 90% 与主要部件 5% 目标未达成。
