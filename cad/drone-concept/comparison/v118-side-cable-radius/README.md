# v118 红翼侧外挂筒卷线

从正式 v115 保存模型出发，只将红翼侧卷线的圆形截面半径从 1.8 mm 减为 1.5 mm。卷线中心线、端头及其余实体沿用 v115。两组中心线采样 RMS 分别为 4.20 和 5.23 px。参考中的下部圈线、穿孔筒面板和端盖仍有可见差异，隐藏引线位置按现有造型推定。[同角度近景](side-cable-review.png) · [卷线读回](side-cable-check.json)

| 固定相机平均轮廓 IoU | v115 | v118 |
| --- | ---: | ---: |
| 视频十方位 | 85.8446100% | 85.8502230% |
| 静态七图 | 82.4302146% | 82.4424702% |
| 参考拼图十格 | 89.5914211% | 89.5907878% |

正后方视频回落 0.0122 个百分点。三组对照沿用原相机和分割规则，比较时只排除四根新增支柱及附件。整机分数变化很小，正式外观入口采用 v115。整圈 90% 和主要部件轮廓偏差 5% 目标仍待达成。[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [参考拼图十格](sheet-comparison/comparison-board.png)

最终保存文件仅一件 BRep 改变。上下护套搭接均为正体积，13 项支撑干涉检查无退步。保存读回确认 696 个可见对象、852 个有效闭合 STEP 实体，卷线网格与重三角化一致。FreeCAD 原生四视图复核了可见性及颜色。四支柱、实测平面屏、外挂筒、侧控件和格栅均保留。[构建检查](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

## 复建

从仓库根目录执行。最终输出可按 v115 的固定相机流程重放，三组相机也随本报告保留。[v115 基线与渲染流程](../v115-antenna-curve/README.md)

```sh
VINTROX_BASE=cad/drone-concept/comparison/v115-antenna-curve
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
export PYTHONPATH="$VINTROX_FREECAD/lib"
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_side_cable_radius.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --radius 1.5 --output "$VINTROX_RUN/diagnostic"
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```
