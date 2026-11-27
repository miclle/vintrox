# v96 前侧护壳横向收缩候选

v96 以已采用的 v95 为基线，只将左右 `FrontCheek` 与 `FrontCheekBridge` 四个真实 CAD 实体绕模型中心 X=0 横向缩放到 **0.970**。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、外挂筒、屏幕侧控件和格栅均保持；没有图像变形、逐部件配准或删件。

固定 v95 相机下，视频十方位平均轮廓 IoU 为 **0.855817875**，相对 v95 的 `0.855533201` 提升 **0.028467 个百分点**；静态七图平均为 **0.822961983**，相对 v95 的 `0.822596196` 提升 **0.036579 个百分点**。视频各视角逐项比较保存在 `video-comparison/comparison-report.json`，静态图保存在 `stills-comparison/comparison-report.json`。

保存候选 FCStd 为 `71e0d53bbd8787765a8a45caf6a1530368b52147820e438c38c4cdcabd0eebb2`，STEP 为 `0896826e0f329ac6965f271b1aac2ecb154c14c53af6291371b0c6b9c0ed30cd`。独立读回通过：698 个保存对象、696 个绑定渲染对象、1008 个有效闭合 STEP solids；屏幕几何保持，四根支柱保护通过，GUI 外观成员复制 `2095` 项，颜色审计有 `74` 个 RGB 三元组。`video-ids/`、`still-ids/` 与 `boundary-regions.json` 保存对象级轮廓归因，归因只用于检查目标，不改变主指标。

该结果仍是静态外观研究。IoU 仍低于 90%，主要后壳、喷口、翼板与侧面细部差异仍在；参考曲面屏用透明罩表达，不能代表制造、打印、装配、光学、声学、热、电气或实物验收。

复现候选：

```sh
BASE=cad/drone-concept/vintrox-drone-concept.FCStd
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  tools/experiment_drone_front_cheek_contract.py \
  --base "$BASE" --base-mesh cad/drone-concept/comparison/v95-v69-v73/meshes.json \
  --appearance-source "$BASE" --output /tmp/vintrox-v96/front-cheek-0p970 \
  --scale 0.970 --revision v96-front-cheek-contract097
```
