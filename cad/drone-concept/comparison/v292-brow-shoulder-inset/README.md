# v292 前罩肩部弧面内罩收形

在 v287 保存模型上，将两侧前罩肩部弧面内罩及对应白纹各向内移 2 mm。共十件保存形体通过闭合性、正体积及高级几何复核。20 项接合距离检查通过，内罩与前罩主体间隙为零。实测平面屏、外挂筒、屏幕侧控件、格栅和四根支柱均保留。[几何与接合](candidate-check.json)

| 固定相机 | v287 | v292 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.033198% | 86.034597% | +0.001399 |
| 静态七图 | 82.574760% | 82.587208% | +0.012448 |
| 拼图十格 | 89.782809% | 89.783549% | +0.000740 |

静态第 05 图提高 0.03421 个百分点。该图在填洞参考遮罩外的 CAD 像素由 56,550 降至 56,360，其中左内罩由 2,616 降至 1,407，前罩主体由 1,527 升至 2,673。视频第 04 方位下降 0.00298 个百分点，拼图第 02 格下降 0.00250 个百分点。采用 v292 作为外观评审版，视频整圈 90% 和主要部件轮廓偏差 5% 仍待达成。[v287 静态归因](v287-still-05-boundary.json) · [v292 静态归因](still-05-boundary.json) · [视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

独立读回确认 853 个有效闭合 STEP 实体。FreeCAD 原生四视图核对了 696 个可见对象和 70 组颜色。外罩曲面和参考中被遮挡的细节仍按外观推定。[保存读回](../../readback-verification.json) · [原生显示](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

以 v287 保存 FCStd 运行 `v270-v271-front-shoulder/replay.py --inward-mm 2 --group crown`，以新 FCStd 哈希更新临时清单，再导出渲染网格。沿用 v287 的三组固定相机。独立重建网格与渲染输入逐字节一致。[候选脚本](../v270-v271-front-shoulder/replay.py) · [v287 输入与相机](../v287-front-cheek-x0985/README.md) · [网格记录](mesh-archive.json) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
