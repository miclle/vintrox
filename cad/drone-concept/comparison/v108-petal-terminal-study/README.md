# v108 大喷口叶片末端研究

从保存 v107 的十方位彩色渲染、物件 ID 和参考视频复算差异。外部差异归因中，大喷口叶片为 17,525 像素，前罩内衬为 11,775 像素，小喷口肋为 11,086 像素。侧后方对照可见大喷口在一部分边缘偏外，末端又偏短。暗材料、开口和相互遮挡会影响像素归因。[区域差异图](boundary-regions-board.png) · [归因数据](boundary-regions.json)

两组试验均在喷口局部 Z=98 mm 处分开保存实体，沿轴拉伸末端，并向径向内侧剪切，再融合至根部。每组改动 72 件叶片和随动细节，保留根部导轨和铰座。120 项接合距离检查无退步，13 件受保护支撑的体积差检查通过。实测平面屏、外挂筒、侧控件及格栅保留。

| 固定相机轮廓 IoU | 视频十方位 | 静态七图 |
| --- | ---: | ---: |
| v107 | 85.708302% | 82.445144% |
| 轴向 1.35 倍，径向内收 2 mm | 85.685285% | 82.428459% |
| 轴向 1.25 倍，径向内收 1 mm | 85.695961% | 82.432231% |

径向内收量按原末端 17 mm 轴向跨度计。两组均在 video-07 略有提升，video-01、02、03、05、06 和 still-05 回落。FreeCAD 高级检查分别发现 3 件和 1 件末端脊条出现新的 `BOPAlgo_InvalidCurveOnSurface`。两组均归档为未采用的诊断候选，当前外观入口为 v107。候选完成了 FCStd 重开和网格生成。v107 的 STEP 与原生颜色验证记录见其基线目录。整圈 90% IoU 及完整主要部件偏差 5% 目标仍待达成。

- [1.35 倍候选 FCStd](axial135-radial-minus2/candidate.FCStd) · [几何检查](axial135-radial-minus2/candidate-check.json) · [视频十方位](axial135-radial-minus2/video-comparison/comparison-board.png) · [静态七图](axial135-radial-minus2/stills-comparison/comparison-board.png)
- [1.25 倍候选 FCStd](axial125-radial-minus1/candidate.FCStd) · [几何检查](axial125-radial-minus1/candidate-check.json) · [视频十方位](axial125-radial-minus1/video-comparison/comparison-board.png) · [静态七图](axial125-radial-minus1/stills-comparison/comparison-board.png)

## 复现

从仓库根目录运行下列命令。第二组使用新的输出目录，参数改为 `--factor 1.25 --tip-radial-shift -1`。静态图传入 `stills-comparison/cameras.json` 及各自的输出目录。流程沿用 v107 的固定相机、分割和四支柱排除规则，渲染使用保存 CAD 的三角面，以 50% 透明度叠加参考图。[v107 基线](../v107-handle-arm-inward-tilt/README.md)

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/baseline-meshes.json"
PYTHONPATH="$VINTROX_FREECAD/lib" "$VINTROX_FREECAD/bin/python" \
  tools/experiment_drone_petal_axial.py --base-model "$VINTROX_BASE/candidate.FCStd" \
  --base-meshes "$VINTROX_RUN/baseline-meshes.json" --output "$VINTROX_RUN/candidate" \
  --construction tip-splice --station 98 --factor 1.35 --tip-radial-shift -2
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_RUN/candidate/meshes.json" \
  --model "$VINTROX_RUN/candidate/candidate.FCStd" --output "$VINTROX_RUN/video-renders" \
  --comparison "$VINTROX_BASE/video-comparison/cameras.json"
"$VINTROX_FREECAD/bin/python" tools/compare_drone_reference.py \
  --renders "$VINTROX_RUN/video-renders" --output "$VINTROX_RUN/video-comparison" \
  --cameras "$VINTROX_BASE/video-comparison/cameras.json"
```
