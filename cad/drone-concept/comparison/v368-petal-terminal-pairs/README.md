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

重建的 SHA-256 为 `dc9f0c26b1e49efd9337497600ed6dc4aec52f808b83588c28e05bc70ae89695`。归档成员逐项核对，并以 FreeCAD 核对 24 个形体与来源的几何签名和高级检查结果。FCStd 读回 696 个可见对象，FCStd 与 STEP 各有 853 个有效闭合实体，体积相对误差约 5.20 × 10⁻⁷。本轮颜色核对覆盖保存的显示数据和彩色渲染，尚未单独核对 v368 原生窗口。[几何检查](source-check.json) · [独立读回](independent.json)
