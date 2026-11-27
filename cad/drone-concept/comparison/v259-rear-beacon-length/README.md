# v259 后部指示灯长度

从 v257 保存模型出发，两侧后部指示灯灯体和环箍沿 Y 向加长 30%，底座安装平面保持不变，端透镜向后移动 6.75 mm。10 件改动实体均通过保存读回，灯体与底座、透镜和三道环箍的接合保持，颜色和可见性随 v257 显示数据恢复。[几何检查](candidate-check.json) · [原生显示](native-display/native-display-verification.json)

| 固定相机 | v257 | v259 |
| --- | ---: | ---: |
| 视频十方位 | 85.93237% | 86.00809% |
| 静态七图 | 82.55077% | 82.57434% |
| 拼图十格 | 89.68205% | 89.77271% |

视频、静态图和拼图均值均提高。静态第 06 图下降 0.00855 个百分点。v257 的缺失轮廓诊断显示多个斜视方位的灯体参考边缘超出保存 CAD，v259 以这些共同出现的边缘为依据扩展灯体。[缺失轮廓板](v257-missing-contours.png) · [灯体近景](v257-beacon-detail.png)

独立保存读回确认 696 个可见对象和 853 个闭合 STEP 实体。FreeCAD 原生四视图核对了 70 种颜色。实测平面屏、四根支柱、外挂筒、屏幕侧控件和格栅保持。[交付校验](../../delivery-verification-current.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

使用
`tools/experiment_drone_beacon_length.py --base <v257.FCStd> --mesh <v257网格> --output <新目录> --scale 1.3`
重建候选。沿用 v257 的固定相机和同一参考分割规则。[v257 基线](../v257-mirrored-nozzle-tips/README.md)
