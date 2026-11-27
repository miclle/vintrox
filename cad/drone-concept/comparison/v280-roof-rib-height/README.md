# v280 顶罩凸筋高度筛选

将 v276 顶罩的两条凸筋从 6 mm 分别降到 4.5 mm 和 3 mm，以检查凸筋是否推高参考外轮廓。两档都以原凸筋底面为基准缩放实际 CAD 几何。保存读回中每条凸筋均为有效闭合单实体，高级几何检查通过，与检修板的间距约为 2 mm。[4.5 mm 几何检查](height-4.5/candidate-check.json) · [3 mm 几何检查](height-3.0/candidate-check.json)

| 凸筋高度 | 视频十方位平均 IoU | 相对 v276（百分点） |
| --- | ---: | ---: |
| 6 mm（v276） | 86.019486% | 0 |
| 4.5 mm | 85.929484% | −0.090003 |
| 3 mm | 85.869206% | −0.150280 |

两档均在九个方位下降，第 06 方位持平。正式模型采用 v276 的 6 mm 高度。本轮验证覆盖候选保存几何和视频十方位，候选 STEP 与 FreeCAD 原生显示尚未复核。[4.5 mm 十方位对照](height-4.5/video-comparison/comparison-board.png) · [3 mm 十方位对照](height-3.0/video-comparison/comparison-board.png)

从保存的 v276 导出网格后，在 FreeCAD Python 环境中运行 `PYTHONPATH="$VINTROX_FREECAD/lib:$PWD/tools" "$VINTROX_FREECAD/bin/python" cad/drone-concept/comparison/v280-roof-rib-height/replay.py --base <v276 FCStd> --mesh <v276 网格> --output <新目录> --height 4.5`。将高度改为 `3.0` 可复跑第二档。使用生成的 FCStd 和网格沿原固定视频相机重放渲染与叠加。[编辑与复现](../../../../docs/drone-concept.md#编辑与复现) · [v276 视频相机](../v276-front-cheek-x099/video-comparison/cameras.json)

4.5 mm 档已独立重放，FCStd 内各文件和网格数据与归档试验一致。FCStd 的 ZIP 时间戳随重建变化，重放时以新报告的哈希绑定本次渲染。
