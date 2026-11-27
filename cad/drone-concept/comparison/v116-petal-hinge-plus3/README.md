# v116 喷口叶片铰接角试验

从保存的 v115 出发，将 12 组叶片和随动细节绕各自铰座中心作 ±3° 刚体旋转，共涉及 108 件形体。用已保存的真实 CAD 网格和同一组固定相机比较。仅在参考比较中沿用四支柱及其附件的排除规则。实测平面屏、外挂筒、屏幕侧控件及格栅保留。参考曲面屏和被遮挡部位仍有造型假设。[+3° 构建](candidate-check.json) · [−3° 构建](minus3-check.json)

| 固定相机平均轮廓 IoU | v115 | +3° |
| --- | ---: | ---: |
| 视频十方位 | 85.8446100% | 85.8470958% |
| 静态七图 | 82.4302146% | 82.4249510% |
| 参考拼图十格 | 89.5914211% | 89.6010167% |

七组既有喷口末端标注到可见叶片边缘的 RMS 均下降。最坏观察点偏差从投影屏宽的 22.74% 降至 21.94%，位于 `video-06`。`still-04` 的该视角最大偏差从 6.55% 增至 6.68%。标注只覆盖可辨认的末端，可见边缘还包含遮挡边界。正式模型采用 v115。整圈 90% 和主要部件完整轮廓偏差 5% 目标仍待达成。[边缘对照](visible-petal-edges.png) · [逐点数据](visible-petal-edges.json)

+3° 通过 132 项接合距离复核，无新增高级几何检查错误。独立读回确认 696 个可见对象、852 个有效闭合 STEP 实体、108 件变更网格与保存实体一致，以及支撑形体一致。FreeCAD 原生四视图复核了可见性和颜色。−3° 出现 17 项接合距离退步，在构建检查阶段结束。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

在正式 v115 上，视频十方位累计 178,168 个像素落在参考填洞轮廓之外，另有 228,983 个落在参考封闭暗区。外侧差异归因中，大喷口叶片占 17,527 px，前罩内衬占 11,775 px，小喷口肋占 11,086 px。暗色材料和开口均可能进入统计。保留原分割和原整机 IoU。[区域差异板](boundary-regions-board.png) · [区域数据](boundary-regions.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [参考拼图十格](sheet-comparison/comparison-board.png)

## 复建与复测

从仓库根目录运行。用独立输出目录将 `--angle` 改为 `-3` 可复建反向诊断。使用带 Pillow、NumPy、SciPy 的 Python 重放分析。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v115-antenna-curve
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
export PYTHONPATH="$VINTROX_FREECAD/lib"
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_petal_hinge_angle.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --angle 3 --output "$VINTROX_RUN/diagnostic"
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```

用最终 FCStd、网格和三组 `cameras.json` 重放[固定相机渲染与叠加](../v107-handle-arm-inward-tilt/README.md)。基线参考帧通过 `tools/compare_drone_reference.py` 重放。用 `tools/render_drone_object_ids.py` 生成基线与候选的视频和静态对象 ID，再用 `tools/compare_drone_visible_petal_edges.py` 比较 [v110 的既有标注](../v110-nozzle-pose-minus7/tip-measurement.json)。该脚本的基线目录需要解压后的 `meshes.json`、两组相机配置及重放参考帧。将 v115 对象 ID、视频彩色渲染和重放参考帧传给 `tools/analyze_drone_boundary_regions.py` 可复算区域诊断。归档网格可直接用于重放渲染。[网格清单](mesh-archive.json)
