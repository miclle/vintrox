# 喷口叶片节距与细节候选

2026-10-24，基线为 v32，最终采用 D 的几何进入正式 v33。固定十个视频相机，另核对左后、正后、右后三张局部叠加。四支柱、喷口外罩及后壳保持不变。没有图像拉伸或相机重拟合。

## 为什么修订叶片数量

正后视参考中央是一片完整叶片，旧 16 片布局中央为缝。调相后，两侧导轨仍过密。第 120 帧、第 590 行选取三组清楚可辨的下段导轨边缘 `(417,429)`、`(470,483)`、`(519,530)`，以各对中点检查周向节距，人工判读约有 2px 不确定性。源帧直接从 `video-cam.mp4` 抽取并逐像素核对。该样本只覆盖中央局部，左右后视还须独立看叠加，隐藏部分的数量仍为外观推断。

| 版本 | 叶片数 | 中点横向 RMS / 最大偏差 | 十方位 IoU | 结论 |
| --- | --- | --- | --- | --- |
| v32 基线 | 16 | 12.23 / 18.50px | 84.38323% | 中央错相且间距偏密 |
| A | 16 | 8.91 / 12.50px | 84.38200% | 整圈旋转 11.25°，同时改变倾斜出口平面，未采用 |
| B | 16 | 9.07 / 12.50px | 84.38795% | 加薄边与圆角，但保留 A 的出口平面问题，未采用 |
| C | 16 | 8.66 / 11.50px | 84.38725% | 按各截面内部调相，增加分段加强条；节距仍偏密 |
| D | 12 | 1.66 / 2.50px | 84.39002% | 较宽叶片匹配三个后方视角，采用 |
| 正式 v33 | 12 | 1.66 / 2.50px | 84.39019% | 真实保存模型；完整外观目标仍未达到 |

[基线节距](pitch-v32.png) · [D 节距](d/pitch-check.png) · [D 左后](d/detail-03.png) · [D 正后](d/detail-04.png) · [D 右后](d/detail-05.png) · [数值及模型哈希](review.json)。正式图板见[左后](../nozzle-petal-detail-left.png)、[正后](../nozzle-petal-detail-back.png)、[右后](../nozzle-petal-detail-right.png)。候选和正式模型的节距、出口圆读回相同；[保存实体复核](formal-geometry-check.json)确认 108 个对象的几何签名相同，九个代表对象的对称实体差集为零。两条生成路径均使用 0.12mm 三角化参数，但缓存网格不同，整体 IoU 存在约 0.00016 个百分点的微小差异，不宣称全部像素相同。

## D 的实际几何

- 12 片、30° 周期，在各倾斜截面内调相 15°，保留截面中心与出口圆的原倾角。
- 叶片主厚度由 3.5 改为 2mm，四个板角倒圆 0.85mm；末端仍保留可读回的圆弧。
- 中央加强条上段凸起、下段细导轨，边压条半径从 0.45 改为 0.28mm，并在圆角前结束。均为独立闭合实体及真实接合，不是渲染法线贴图。
- 原 144 个叶片相关对象变为 108 个；多出的四组共 36 个对象移除，其余 577 个可见网格记录不变。四支柱的保存 BRep 对称实体差集为零。

[D 保存读回](d/candidate-check.json)、[出口圆读回](d/terminal-check.json)保留每个对象的证据。出口圆 RMS 约 3.30px、最大约 6.28px，与 v32 相同。正式模型另经完整读回与交付审计，见[读回报告](../../readback-verification.json)和[交付报告](../../delivery-verification.json)。候选 FCStd 仅为几何试验，无 GUI/STEP 交付状态。

## 复现

使用 FreeCAD Python、仓库现有 Blender 渲染脚本和固定 `cameras.json`。先提供哈希为 `72c8968f252d52be29c9e82a53d7b9b61b68542ae994f6beb195761cb4ad5655` 的 v32 FCStd，以及与其绑定的网格 JSON；脚本拒绝哈希不匹配的基线。当前本机基线、生成器快照和候选网格缓存在 Codex visualization 目录的 `drone-nozzle-petals-study-cache`，不将网格 JSON 重复提交进仓库。

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_nozzle_petals.py \
  --base-model /path/to/v32.FCStd --base-meshes /path/to/v32-meshes.json \
  --output /tmp/new-petal-d --variant d --phase-degrees 15
```

输出目录必须为空。以候选模型和其网格调用 `render_drone_concept.py --comparison cad/drone-concept/comparison/cameras.json` 及 `render_drone_object_ids.py`，再用 `measure_drone_petal_pitch.py`、`measure_drone_nozzle_outline.py --expected-petals 12` 和 `compare_drone_side_detail.py` 复核。源码中的生成尺寸是外观假设，不是制造尺寸；本轮未验证打印、实物装配或声学性能。
