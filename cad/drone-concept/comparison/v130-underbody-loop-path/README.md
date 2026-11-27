# v130 底部回环

采用半径 2.2 mm 的镜像回环。由 v127 的路径出发，四个前段控制点分别后移 1.8、3、2.1、0.6 mm，保留四个端点。按 40 个圆截面放样。实测平面屏、四支柱、外挂筒、侧控件和格栅随完整模型一起渲染。回环被遮挡的路径根据可见弧段推定。

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v120 | 85.842979% | 82.434163% | 89.583531% |
| v129 | 85.851014% | 82.438719% | 89.587106% |
| v130 | 85.852768% | 82.442841% | 89.589450% |

v129 在第 180 帧改善明显，第 60 帧 RMS 升至 14.21 px。v130 缩小前段的移动量，使四组既有采样 RMS 均低于 v120。其中第 180 帧从 11.85 降至 6.50 px，最大采样偏差从投影屏宽的 19.25% 降至 7.52%。第 60 帧的最大采样偏差从 14.77% 升至 15.17%。局部距离只覆盖可见标注点，完整主要部件轮廓的 5% 目标仍待达成。[逐点对照](visible-loop-edges.png) · [距离和遮挡归属](visible-loop-edges.json)

正式 FCStd 与 STEP 通过保存读回，含 696 个可见对象和 853 个有效闭合 STEP 实体。两件回环与生成函数的几何对称差为 0 mm³，四个端点和机身正体积搭接，四支柱复核通过。FreeCAD 原生四视图通过颜色及可见性检查。[生成几何](generator-geometry-check.json) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [正式交付校验](../../delivery-verification-current.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

按 v130 的保存网格重算十方位差异后，参考轮廓外、归到大喷口叶片、前罩内衬和小喷口脊条的像素仍最多，分别为 17,528、11,775 和 11,086。两侧斜前视的内衬和屏框差异包含参考暗边。整机 IoU 仍采用原分割。[区域差异板](video-ids/boundary-regions-board.png) · [逐视角归属](video-ids/boundary-regions.json)

v140 接替正式入口后，v130 的 FCStd、STEP 和压缩网格移出本地 `main` 历史。重放时先从本机恢复包取回 v130 的 `candidate.FCStd` 和 `meshes.json.gz`，包括本地 LFS 对象，置于单独的临时目录。控制点与插值参数保存在 `path-fit.json`。其既有参考标注用于复测，当前距离以 `visible-loop-edges.json` 为准。[清理与恢复记录](../../../../docs/storage-cleanup.md) · [网格清单](mesh-archive.json) · [参数](path-fit.json) · [v129 逐点对照](v129/visible-loop-edges.json)

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v130-underbody-loop-path
VINTROX_REPLAY=$(mktemp -d)
VINTROX_INPUT=/absolute/path/to/recovered-v130
gzip -dc "$VINTROX_INPUT/meshes.json.gz" > "$VINTROX_REPLAY/meshes.json"
for group in video stills sheet; do
  cameras="$VINTROX_PACKAGE/$group-comparison/cameras.json"
  /Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 \
    --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
    --model "$VINTROX_INPUT/candidate.FCStd" --output "$VINTROX_REPLAY/$group-renders" \
    --comparison "$cameras"
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
    --renders "$VINTROX_REPLAY/$group-renders" --output "$VINTROX_REPLAY/$group-comparison" \
    --cameras "$cameras"
done
```
