# v335 大喷口镜像叶片端角

第 90 帧里可连续追踪的叶片端角位于 (263, 606)，v329 最近的可见边界位于 (268, 606)，对应第 10 号叶片。将该片与镜像第 6 号叶片末段沿径向外展。第 90 帧端角偏差由 5 px 降至 1 px，第 60 和 180 帧的独立端角仍为 5 px 和 1 px。[连续原帧](../v334-nozzle-video-tracks/tracks.png) · [端角距离](corner-check.json)

| 固定相机 | v329 | v335 |
| --- | ---: | ---: |
| 视频十方位平均 IoU | 86.01488% | 86.01661% |
| 静态七图平均 IoU | 82.61126% | 82.60498% |
| 拼图十格平均 IoU | 89.87747% | 89.87424% |
| 第 120 帧原末缘标注最大偏差 / 屏宽 | 5.45% | 2.17% |
| 第 120 帧原末缘标注 RMS | 7.92 px | 4.93 px |

原有七个标注视角中六个的末缘 RMS 降低，第 60 帧由 8.66 增至 8.74 px。采用 v335 作为正式评审版，依据为连续帧端角与七视角复测。静态第 04 图及拼图第 07 格的整机 IoU 分别下降 0.01837 与 0.01856 个百分点。第 60、180 帧的原末缘最大误差仍为投影屏宽的 8.42% 和 5.01%。[同相机局部叠加](visible-edges.png) · [逐点数据](visible-edges.json) · [视频](video.json) · [静态](stills.json) · [拼图](sheet.json)

从 v329 保存模型及其重建网格运行 tools/experiment_drone_petal_axial.py，选择 `--construction tip-splice --station 103 --factor 1.0001 --tip-radial-shift 1.7 --leaf-indices 6 10`。径向位移随局部 Z 超出 103 mm 的距离线性增长，每 17 mm 增加 1.7 mm。使用 tools/finalize_drone_petal_axial.py 恢复 v329 原生显示并导出 STEP。12 件改动形体通过高级几何检查，70 项邻件距离复核通过，13 件支撑形体的差集为零。[几何与接合](geometry.json)

FCStd 与 STEP 独立读回通过，696 个可见对象，853 个闭合 STEP 实体。固定相机渲染使用的网格与从正式保存模型独立重建的网格逐字节一致。FreeCAD 原生四个方向均能显示，核对了 70 组颜色。实测平面屏、侧控件、格栅、外挂筒和四根支柱均保留。参考曲面屏与被遮挡部位仍限制外观对照。[读回](readback.json) · [网格](mesh-archive.json) · [原生显示](native-display/native-display-verification.json)
