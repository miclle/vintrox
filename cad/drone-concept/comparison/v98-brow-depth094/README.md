# v98 前眉总成深度候选（未采用）

以保存 v97 为基线，21 件前眉及附属对象绕 Y=30.172439653712 mm 后平面做深度比例 0.94 变换，X/Z 不变。其余 677 件形体、实测平面屏、四支柱、外挂筒、侧控件及格栅保持。

固定相机视频十方位平均轮廓 IoU 为 **0.855272725874**，相对 v97 **-0.045898441 个百分点**；静态七图为 **0.823529646885**，变化 **-0.005754963 个百分点**。两项均退步，拒绝此候选，正式入口仍为 v97。逐视角变化见 [评审记录](candidate-review.json)。

FCStd SHA-256：`537da812b5d625292c794a277a09a1989750f58a80042abcf61c8ab616cc1b41`；STEP：`41f56aafbf48f75f812aa81ea43a38515a078880246d606d1d2b9fb40cdcb240`。独立读回确认 698 个形体对象、696 个可见对象、852 个有效闭合 STEP 实体，21 件变化网格与保存读回一致，四支柱保护通过。原生 FreeCAD 四视图颜色／可见性审计及截图目视检查完成，关闭后文件哈希保持；详见 [读回](readback-verification.json)和[原生显示记录](native-display/native-display-verification.json)。原生审计路径保留原始来源；v99 记录同时包含正式 v97。

[视频叠加板](video-comparison/comparison-board.png) · [静态叠加板](stills-comparison/comparison-board.png)。真实 CAD 网格、彩色渲染、对象 ID、透明叠加及差异图均归档；相机与分割规则保持，仅比较时排除新增支柱，不修改正式模型。归因结果是屏幕空间诊断，不能证明完整主要部件偏差不超过 5%。

复现几何（仓库根目录）：

```sh
BASE=cad/drone-concept/comparison/v97-petal096-brow0985-on-v96
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_front_brow_contract.py \
  --base "$BASE/candidate.FCStd" --base-mesh "$BASE/meshes.json" \
  --appearance-source "$BASE/candidate.FCStd" --scale 1 --depth-scale 0.94 \
  --revision v98-brow-depth094 --output /tmp/vintrox-v98-replay
```

固定相机重放使用 `tools/render_drone_concept.py --comparison` 及 `tools/compare_drone_reference.py --cameras`，分别传入本目录的 `video-comparison/cameras.json` 和 `stills-comparison/cameras.json`；对象 ID 使用 `tools/render_drone_object_ids.py` 与同一相机配置。90% 整圈轮廓及完整主要部件 5% 目标仍未完成；以上仅为静态外观研究，未作制造、装配、光学、声学、热、电气或实物验收。
