# v338 小喷口整体 Y−1 mm 姿态

以正式 v335 保存模型为基线，将两侧 152 件小喷口总成沿各自局部装配根部做对称刚体 Y 向 −1 mm 平移。四根新增支柱、实测 `210 × 160 × 2 mm` 平面屏、外挂筒、屏幕侧控件和格栅均保持。

固定相机三组平均轮廓 IoU 如下。

| 组别 | v335 | v338 |
| --- | ---: | ---: |
| 视频十方位 | 86.01661% | **86.04076%** |
| 静态七图 | 82.60498% | **82.61858%** |
| 拼图十格 | 89.87424% | **89.89583%** |

渲染使用保存 FCStd 重建的真实 CAD 三角网格和同一组固定相机，注册只使用相机投影，没有图像拉伸、非刚性变形、逐部件对齐或忽略可见部件。支柱仅按既有比较规则排除。完整证据保存在 `video-comparison/`、`stills-comparison/` 和 `sheet-comparison/`。

152 件小喷口对象均通过保存读回的有效、闭合和实体数检查。独立邻接报告保留 328 项接触检查，姿态不变量检查通过。现有旧版验证器要求叶片末端固定在旧 Z=53 mm，不能用于刚体姿态候选，本轮改用姿态不变量检查并明确记录该限制。

正式模型的三组目标仍未完全达成。视频整圈 90% 和主要部件轮廓偏差不超过投影屏宽 5% 尚未证明。屏幕本体是实测平面屏，参考曲面屏罩与不可观察内部细节仍属于外观推导。结果不代表制造、装配、光学或实物验收。

## 复现

```sh
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/python \
tools/experiment_drone_small_pod_pose.py \
  --base cad/drone-concept/vintrox-drone-concept.FCStd \
  --output <candidate-dir> --offset 0 -1 0 --rotation-vector 0 0 0
```

使用 `tools/restore_candidate_display.py` 恢复保存颜色后，以 `tools/export_candidate_drone_meshes.py` 导出网格。将网格分别传给 `tools/render_drone_concept.py` 与 `tools/compare_drone_reference.py`，相机依次使用 `comparison/cameras.json`、`comparison/still-cameras.json` 和 `comparison/contact-sheet-cameras.json`。`readback.json`、`pose-invariant-check.json` 和 `lower-pod-verification.json` 记录独立读回与局部检查。
