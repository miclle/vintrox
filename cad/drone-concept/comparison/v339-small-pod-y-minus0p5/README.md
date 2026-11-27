# v339 小喷口整体姿态 Y−0.5 mm

以 v338 保存模型为基线，将两侧共 152 件小喷口总成沿各自局部装配根部做对称 Y 向 −0.5 mm 平移。四根支柱、实测 `210 × 160 × 2 mm` 平面屏、外挂筒、屏幕侧控件和格栅保持。

固定相机三组平均轮廓 IoU 如下。

| 组别 | v338 | v339 |
| --- | ---: | ---: |
| 视频十方位 | 86.04076% | **86.04973%** |
| 静态七图 | 82.61858% | **82.62481%** |
| 拼图十格 | 89.89583% | **89.90136%** |

渲染来自保存 FCStd 的真实 CAD 三角网格。注册只使用相机投影，没有图像拉伸、非刚性变形、逐部件对齐或忽略可见部件。比较时按既有规则排除四根支柱及其配套座脚。v339 的保存读回确认 696 个可见对象、853 个 STEP 闭合实体，STEP 体积相对误差约 `5.36e-7`。

视频整圈 90% 与主要部件轮廓偏差不超过投影屏宽 5% 仍未达成。原生 FreeCAD 四视图因当前 macOS 会话锁屏仍待窗口截图复核，保存 GUI 颜色载荷已核对。曲面屏罩和不可观察内部细节仍是外观推导，结果不代表制造、装配或实物验收。

## 复现

```sh
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/python \
tools/experiment_drone_small_pod_pose.py \
  --base cad/drone-concept/vintrox-drone-concept.FCStd \
  --output <candidate-dir> --offset 0 -0.5 0 --rotation-vector 0 0 0
```

使用 `tools/restore_candidate_display.py` 恢复保存颜色，以 `tools/export_saved_drone_meshes.py` 导出网格，再按 `cameras.json`、`still-cameras.json` 和 `contact-sheet-cameras.json` 运行固定相机渲染与比较。`readback-verification.json`、`candidate-check.json` 和 `pose-invariant-check.json` 记录几何检查。
