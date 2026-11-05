# v97 喷口叶片与前眉联合外观入口

v97 以已采用的 v96 为基线，在真实 CAD 中加入三项外观候选：`ProjectingBrow`/`BrowUnderside` 绕模型中心 X=0 横向缩放到 **0.985**，12 片喷口叶片及其铰链按局部切向比例 **0.960** 收形，并保留 v96 的 `FrontCheek`/`FrontCheekBridge` 横向缩放 **0.970**。实测平面屏 `210 × 160 × 2 mm`、可视区 `200 × 150 mm`、四根支柱、外挂筒、屏幕侧控件和格栅均保持；没有图像变形、逐部件配准或删件。

固定相机下，视频十方位平均轮廓 IoU 为 **0.855731710**，静态七图平均为 **0.823587197**。视频各视角逐项比较保存在 `video-comparison/comparison-report.json`，静态图保存在 `stills-comparison/comparison-report.json`。

保存正式 FCStd 为 `2ab40ea74dacd2be487e8c3f77ff540b63110daff9c506f79cf332c8e016412a`，STEP 为 `739c3c02b13c532d3b72fc7b29701558b458b77e37410d2f75e078020c72d178`。独立读回通过：700 个保存对象、696 个绑定渲染对象、852 个有效闭合 STEP solids；屏幕几何保持，四根支柱保护通过，GUI 外观与颜色绑定来自正式保存模型。新渲染清单和比较报告均绑定该 FCStd 哈希。

该结果仍是静态外观研究。IoU 仍低于 90%，主要后壳、喷口、翼板与侧面细部差异仍在；参考曲面屏用透明罩表达，不能代表制造、打印、装配、光学、声学、热、电气或实物验收。

复现候选：

```sh
BASE=cad/drone-concept/vintrox-drone-concept.FCStd
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  tools/experiment_drone_front_cheek_contract.py \
  --base "$BASE" --base-mesh cad/drone-concept/comparison/v95-v69-v73/meshes.json \
  --appearance-source "$BASE" --output /tmp/vintrox-v96/front-cheek-0p970 \
  --scale 0.970 --revision v97-petal096-brow0985-on-v96
```

本轮比较仍是静态外观研究；IoU 低于 90%，不能代表制造、打印、装配、光学、声学、热、电气或实物验收。
