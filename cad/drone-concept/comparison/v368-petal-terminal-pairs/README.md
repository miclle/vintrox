# v368 大喷口两对叶片末缘

在 v363 上使用 v339 第 0、4、5、11 号叶片及其表面附件，共替换 24 个形体和对应的 24 个元素映射。第 60、180 帧标注点到可见叶片族边界的最大距离分别由投影屏宽的 20.96%、21.94% 降至 10.24%、10.03%。第 90 帧由 8.85% 降至 6.13%，第 150 帧由 4.83% 降至 4.66%，第 120 帧仍为 9.69%。采样沿用五个视频方位的末缘标注，固定相机和对象 ID 渲染保留真实遮挡。[两帧逐点对照](terminal-samples.jpg) · [v363 测量](baseline-edges.json) · [v368 测量](edges.json)

| 固定相机平均轮廓 IoU | v363 | v368 |
| --- | ---: | ---: |
| 视频十方位 | 86.2439% | 86.1378% |
| 静态七图 | 82.7176% | 82.6706% |
| 拼图十格 | 89.9825% | 89.9716% |

保留 v368 作为末缘改进试件。三个整机均值均下降，整圈比较继续以 v363 为基线。第 150 帧右回环采样最大偏差仍为 5.94%。源参考中的暗材质、重叠边界和曲面屏带来观察不确定性。实测平面屏、四支柱、侧控件、格栅、外挂筒及保存的颜色和可见性均保留。[视频叠加与差异](video-overlays.jpg) · [静态七图](stills-overlays.jpg) · [拼图十格](sheet-overlays.jpg)

**复建**　先按 [v363 恢复说明](../v363-lowerpod-chassis-combo0995/README.md) 获取基线。从仓库根目录执行以下命令，最后一项传入新的文件路径。

```sh
python3 cad/drone-concept/comparison/v368-petal-terminal-pairs/build.py "$research_dir/candidate.FCStd" cad/drone-concept/vintrox-drone-concept.FCStd "$research_dir/v368.FCStd"
```

重建的 SHA-256 为 `dc9f0c26b1e49efd9337497600ed6dc4aec52f808b83588c28e05bc70ae89695`。归档成员逐项核对，并以 FreeCAD 核对 24 个形体与来源的几何签名和高级检查结果。FCStd 读回 696 个可见对象，FCStd 与 STEP 各有 853 个有效闭合实体，体积相对误差约 5.20 × 10⁻⁷。[几何检查](source-check.json) · [独立读回](independent.json)

十个视频方位合计新增 10,461 个 CAD 前景像素，7,652 个落在参考遮罩之外。其中 7,254 个在原参考帧中的最大 RGB 通道为 1–18。暗部亮度分割会影响整机得分，这些像素是否对应实物边缘仍需沿连续帧判断。本次使用原阈值和完整视角计算。[逐帧像素变化](mask-deltas.json)

## FreeCAD 原生显示与修订文件

上面的初次组合按归档成员转移元素映射。在 FreeCAD 原生窗口打开时出现了 26 条元素名称映射警告。修订版让 FreeCAD 在 v363 文档中复制 v339 对应的叶片形体、重新生成文档内映射，再恢复 v363 的颜色载荷。使用同一四视图宏重开，修订版和 v363 基线均为零条元素映射警告。修订版 696 个可见对象与保存网格逐件一致，70 种原生显示颜色与网格颜色最大通道差为 2.97 × 10⁻⁸。关闭前后文件哈希一致。[四视图记录](native/native-display-verification.json) · [等轴视图](native/v368-isometric.png)

在仓库根目录运行 FreeCAD Python，执行 `native/rebuild.py`，位置参数依次为恢复的 v363 彩色 FCStd、正式 v339 FCStd 和新的输出 FCStd 路径。独立读回修订版的 FCStd 和 STEP 均有 853 个有效闭合实体。[重建脚本](native/rebuild.py) · [读回报告](native/step-readback.json)

修订版重新导出的网格在视频、静态、拼图的平均 IoU 分别为 86.1379%、82.6705%、89.9717%。上表的局部采样来自初次组合。两份文件的哈希与逐视角报告分别保留。[视频](native/video.json) · [静态](native/stills.json) · [拼图](native/sheet.json)
