# v111 底部回环路径对照

以保存 v107 为基线，取原路径与 v82 边界拟合路径之间的两个插值位置。30% 路径分别试用 2.2 mm 与 2.773 mm 截面半径。55% 路径使用 3.250 mm 半径。每组只重建左右两个回环，模型包含实测平面屏、外挂筒、侧控件、格栅和四根支柱。[v82 来源](../v82-loop-visible-boundaries/README.md)

| 路径与半径 | 视频十方位 IoU | 静态七图 IoU |
| --- | ---: | ---: |
| v107 基线 | 85.708302% | 82.445144% |
| 30%，2.2 mm | 85.708668% | 82.473895% |
| 30%，2.773 mm | 85.679489% | 82.454811% |
| 55%，3.250 mm | 85.613128% | 82.405250% |

30%、2.2 mm 候选在正后方两组可见边缘上将 RMS 由 27.04、22.98 px 降至 19.68、16.74 px。第 180 帧的 RMS 由 11.85 升至 14.56 px，最大偏差由投影屏宽的 19.25% 升至 22.95%。该视角的若干参考边缘点在 CAD 中被小喷口、底壳或线束占据。两组侧视整机 IoU 分别回落约 0.045、0.077 个百分点。当前入口采用 v107。整圈 90% 和主要部件完整轮廓 5% 的目标仍待达成。[可见边缘叠加](path30-radius2p2/visible-loop-edges.png) · [逐点距离和遮挡归属](path30-radius2p2/visible-loop-edges.json)

三组均有 696 个可见对象和 852 个有效闭合 STEP 实体。保存模型重开后，两个变更件与各自网格一致，四个回环端部与腹板均有正体积交叠，26 组支撑交叠检查无退步。FreeCAD 原生四视图颜色与可见性检查通过。曲面罩和被遮挡结构仍属于外观推定。

- [30%、2.2 mm 视频](path30-radius2p2/video-comparison/comparison-board.png) · [静态](path30-radius2p2/stills-comparison/comparison-board.png) · [FCStd](path30-radius2p2/candidate.FCStd) · [STEP](path30-radius2p2/candidate.step)
- [30%、2.773 mm 视频](path30-radius2p773/video-comparison/comparison-board.png) · [静态](path30-radius2p773/stills-comparison/comparison-board.png) · [FCStd](path30-radius2p773/candidate.FCStd) · [STEP](path30-radius2p773/candidate.step)
- [55%、3.250 mm 视频](path55-radius3p250/video-comparison/comparison-board.png) · [静态](path55-radius3p250/stills-comparison/comparison-board.png) · [FCStd](path55-radius3p250/candidate.FCStd) · [STEP](path55-radius3p250/candidate.step)

## 复建

运行以下命令可复建 30%、2.2 mm 候选。另两组使用各自的 `path-fit.json` 和构建记录中的完整半径值。输入文件中 `fitted` 的历史拟合距离来自 v82，v111 的测量以本目录中的可见边缘记录为准。

```sh
VINTROX_BASE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_CASE=cad/drone-concept/comparison/v111-underbody-loop-path/path30-radius2p2
VINTROX_RUN=$(mktemp -d)
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
gzip -dc "$VINTROX_BASE/meshes.json.gz" > "$VINTROX_RUN/base-meshes.json"
export PYTHONPATH="$VINTROX_FREECAD/lib"
"$VINTROX_FREECAD/bin/python" tools/experiment_drone_loop_path.py \
  --base "$VINTROX_BASE/candidate.FCStd" --mesh "$VINTROX_RUN/base-meshes.json" \
  --fit "$VINTROX_CASE/path-fit.json" --radius 2.2 --output "$VINTROX_RUN/diagnostic"
"$VINTROX_FREECAD/bin/python" tools/finalize_drone_petal_axial.py \
  --base "$VINTROX_BASE/candidate.FCStd" --appearance-source "$VINTROX_BASE/candidate.FCStd" \
  --diagnostic "$VINTROX_RUN/diagnostic" --output "$VINTROX_RUN/final"
```

以最终 FCStd 和网格重放 v107 的视频与静态透视相机。比较脚本会生成原视频帧、半透明叠加和差异图。可见边缘检查需要用 `tools/render_drone_object_ids.py` 渲染候选的同组视频视角，将输入文件复制到候选目录后运行 `tools/compare_drone_visible_loop_edges.py --candidate "$VINTROX_RUN/final" --baseline "$VINTROX_BASE/candidate.FCStd" --baseline-ids "$VINTROX_BASE/video-ids"`。[v107 相机与渲染命令](../v107-handle-arm-inward-tilt/README.md)
