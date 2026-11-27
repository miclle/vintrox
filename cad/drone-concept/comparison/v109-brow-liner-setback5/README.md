# v109 前罩内衬前缘后移 5 mm

从保存 v107 出发，只缩短 `BrowUnderside` 内衬。沿原深度方向将前缘向后移 5 mm，并固定后端截面 `Y + 0.4 × Z = 96.8 mm`。外罩、金属包边、实测平面屏和四根支柱沿用 v107。内衬与外罩的间隙仍为 0 mm。FreeCAD 高级检查在 v107 内衬报告 16 条曲线错误，在候选内衬报告 0 条。[几何记录](candidate-check.json)

| 固定相机轮廓 IoU | 视频十方位 | 静态七图 |
| --- | ---: | ---: |
| v107 | 85.7083020% | 82.4451438% |
| v109 | 85.7083258% | 82.4450894% |

变化量分别为 +0.0000238 和 −0.0000544 个百分点。局部图中参考前罩的外缘和侧肩落差仍可见，回收内衬对这些边缘影响很小。v109 保留为几何候选，正式外观入口仍采用 v107。整圈 90% IoU 和完整主要部件 5% 轮廓偏差仍待达成。[局部三栏对照](brow-triptych.jpg) · [视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png)

独立读回确认 696 个可见对象、852 个有效闭合 STEP 实体，体积相对误差为 3.08 × 10⁻⁷。内衬网格与重开模型后三角化结果一致。FreeCAD 原生四视图的颜色和可见性检查通过。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [读回校验](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

从仓库根目录运行。沿用 [v107 的渲染与叠加命令](../v107-handle-arm-inward-tilt/README.md)，将模型和网格参数指向新生成的 `candidate.FCStd` 和 `meshes.json`，保持 v107 的视频与静态相机配置。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
PYTHONPATH="$VINTROX_FREECAD/lib" "$VINTROX_FREECAD/bin/python" \
  tools/experiment_drone_front_brow_contract.py \
  --base "$VINTROX_BASE/candidate.FCStd" --base-mesh "$VINTROX_RUN/base-meshes.json" \
  --appearance-source "$VINTROX_BASE/candidate.FCStd" --scale 1 --liner-setback 5 \
  --revision v109-brow-liner-setback5 --output "$VINTROX_RUN/candidate"
```
