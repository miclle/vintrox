# v90 前侧护壳横向收缩候选（研究保留）

v90 从 v89 保存 CAD 出发，仅将左右 `FrontCheek` 与 `FrontCheekBridge` 四个真实 CAD 实体绕模型中心 X=0 横向收缩到 `0.970`。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、外挂筒、屏幕侧控件和格栅均保持；没有图像变形、逐部件配准或删件。`0.985` 档同时保留在临时参数记录中作为对照，`0.970` 在视频和静态平均值均更高。

固定 v89 相机下，十视频平均轮廓 IoU 为 **0.8558303431**，相对 v89 的 **0.8555455397** 提升 **0.0284803 个百分点**；七静态平均为 **0.8235075464**，相对 v89 的 **0.8231338869** 提升 **0.0373659 个百分点**。视频改善 7/10 方位、3/10 持平；静态改善 5/7、2/7 持平。该提升仍远低于 90% 目标，因此候选保留为当前研究候选，正式 v61 与研究优选 v69 不变。

证据包括：

- [FCStd](candidate.FCStd)、[STEP](candidate.step)、[网格绑定](meshes.json)、[候选检查](candidate-check.json)、[评审结论](candidate-review.json)
- [独立读回](readback-verification.json)：698 个保存对象、696 个可见对象、1071 个有效闭合 STEP 实体；屏幕输入和四支柱保护保持
- [视频十方位真实 CAD 渲染、叠加与差异](video-comparison/)、[静态七图](stills-comparison/)
- [对象 ID 与外侧差异归因](video-ids/boundary-regions.json)：仍以 `NozzlePetal`、`BrowUnderside`、`LowerPodRib`、`ScreenBezel` 为主；`FrontCheek` 局部归因在选定参数下下降但不代表整机轮廓通过
- [原生 FreeCAD 显示审计](native-display/native-display-verification.json)：696 个可见对象、颜色/网格合同检查、四视图截图和关闭后文件哈希保持

复现：

```sh
BASE=cad/drone-concept/comparison/v89-petal-brow-combination
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  tools/experiment_drone_front_cheek_contract.py \
  --base "$BASE/candidate.FCStd" --base-mesh "$BASE/meshes.json" \
  --appearance-source "$BASE/candidate.FCStd" \
  --output /tmp/vintrox-v90/cheek-0p970 --scale 0.970 \
  --revision v90-front-cheek-contract-0p970
```

渲染和比较沿用 `tools/render_drone_concept.py`、`tools/compare_drone_reference.py`、`tools/render_drone_object_ids.py` 与 `tools/analyze_drone_boundary_regions.py`，使用 v89 固定视频/静态相机；没有非刚性图像变形或忽略可见部件。参考曲面屏仍以透明罩表示，不代表制造、打印、装配、光学、声学、热、电气或实物验收。
