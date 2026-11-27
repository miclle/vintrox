# v285 大喷口叶片末段斜切

基于 v284 保存模型，从喷口局部 Z 112 mm 逐步收窄第 6、7、9、10 号叶片末段的单侧切向外缘。切面在接续处距各叶片径向基线 12 mm，两档每前进 1 mm 分别内收 0.32、0.40 mm。四件叶片、末端折边及与切面相交的压条沿同一切面裁切。两档分别通过 10、12 件保存形体及 14、16 项接合检查。其余 FCStd 成员逐字节一致。[0.32 几何](slope-0.32/candidate-check.json) · [0.40 几何](slope-0.40/candidate-check.json)

| 版本 | 视频十方位 | 静态七图 | 拼图十格 |
| --- | ---: | ---: | ---: |
| v276 正式版 | 86.019486% | 82.574760% | 89.777430% |
| v284 | 86.056119% | 82.548780% | 89.845627% |
| v285，0.32 | 86.053032% | 82.550196% | 89.839022% |
| v285，0.40 | 86.050360% | 82.551012% | 89.835099% |

两档静态七图均值回升幅度不足 0.003 个百分点。图像对照仍支持采用 v276。候选 STEP 与原生 FreeCAD 颜色检查尚待复查。[0.32 视频](slope-0.32/video-comparison/comparison-board.png) · [0.32 静态图](slope-0.32/stills-comparison/comparison-board.png) · [0.32 拼图](slope-0.32/sheet-comparison/comparison-board.png) · [0.40 视频](slope-0.40/video-comparison/comparison-board.png) · [0.40 静态图](slope-0.40/stills-comparison/comparison-board.png) · [0.40 拼图](slope-0.40/sheet-comparison/comparison-board.png)

先按 v284 的流程重建候选 FCStd 与网格，再在 FreeCAD Python 环境运行 `PYTHONPATH="$VINTROX_FREECAD/lib:$PWD/tools" "$VINTROX_FREECAD/bin/python" cad/drone-concept/comparison/v285-petal-flank-taper/replay.py --base <v284 FCStd> --mesh <v284 网格> --output <新目录> --slope 0.32`。另一档使用 `--slope 0.40`。三组对照沿用 v276 的固定相机。[v284 复建](../v284-petal-tip-inward/README.md) · [固定相机与渲染](../v281-mirrored-petal-long-tip/README.md)
