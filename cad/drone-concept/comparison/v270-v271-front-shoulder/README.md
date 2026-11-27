# v270–v271 前罩肩部内移

根据 v259 静态第 05 图的对象级外溢定位，左右前罩肩部连同白纹、滑槽内衬和螺钉等 16 件形体分别向内移动 4 mm 和 2 mm。候选仅替换这些对象的 BRep，沿用正式包的显示数据、屏幕和四支柱。保存读回的 16 件形体均为有效闭合实体，高级检查错误集合与原件相同。

| 版本 | 视频十方位 | 静态七图 | 拼图十格 | 静态第 05 图变化 |
| --- | ---: | ---: | ---: | ---: |
| v259 | 86.008085% | 82.574342% | 89.772706% | 基准 |
| v270，各 4 mm | 85.995728% | 82.604224% | 89.749672% | +0.117545 个百分点 |
| v271，各 2 mm | 86.001172% | 82.591620% | 89.757456% | +0.061475 个百分点 |

v270 的甲片与前罩内衬各新增约 344 mm³ 交叠。v271 消除了这两处交叠，两档的视频和拼图平均 IoU 均低于 v259，正式交付采用 v259。静态第 05 图变化为整机 IoU，主要部件轮廓 5% 的目标仍待验证。[v270 几何检查](v270/candidate-check.json) · [v271 几何检查](v271/candidate-check.json)

- v270 [视频](v270/video-comparison/comparison-board.png) · [静态](v270/still-comparison/comparison-board.png) · [拼图](v270/sheet-comparison/comparison-board.png)
- v271 [视频](v271/video-comparison/comparison-board.png) · [静态](v271/still-comparison/comparison-board.png) · [拼图](v271/sheet-comparison/comparison-board.png)

从仓库根目录用 FreeCAD Python 运行复现脚本。将 `--inward-mm 2` 改为 `--inward-mm 4` 可重建另一档。

```sh
VINTROX_FREECAD=/Applications/FreeCAD.app/Contents/Resources
VINTROX_RUN=$(mktemp -d /tmp/vintrox-shoulder.XXXXXX)
PYTHONPATH="$VINTROX_FREECAD/lib:$PWD/tools" "$VINTROX_FREECAD/bin/python" \
  cad/drone-concept/comparison/v270-v271-front-shoulder/replay.py \
  --base cad/drone-concept/vintrox-drone-concept.FCStd \
  --output "$VINTROX_RUN/candidate" --inward-mm 2
```

将当前 `concept-manifest.json` 复制到临时目录，用候选报告的 `fcstd_sha256` 更新副本。使用 `tools/export_saved_drone_meshes.py --model <候选 FCStd> --manifest <清单副本> --output <临时网格>` 导出显示网格，再用 `tools/render_drone_concept.py` 和 `tools/compare_drone_reference.py` 重放[视频](../cameras.json)、[静态图](../still-cameras.json)和[拼图](../contact-sheet-cameras.json)相机。归档保留三组总览图、逐方位报告和渲染清单。候选未进入独立 STEP 读回或原生颜色检查。
