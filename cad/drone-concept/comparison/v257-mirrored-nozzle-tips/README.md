# v257 大喷口镜像叶片端部

从 v250 的保存模型出发，仅调整大喷口第 6、10 号镜像叶片的末段，包括叶片、嵌片、两侧压条和末端折边，共 10 件。局部 Z 接续位置为 111 mm，轴向倍数为 1.28，每 17 mm 原跨度的径向与局部 Y 偏移分别为 0.75 mm 和 1 mm。68 项接合未发现退步，13 件支撑实体的差集为零。与 v250 比较，归档中的几何变更仅涉及这 10 件，2,095 个原生显示成员逐字节一致。[几何报告](candidate-check.json)

| 固定相机 | v250 | v257 |
| --- | ---: | ---: |
| 视频十方位 | 85.9272020% | 85.9323720% |
| 静态七图 | 82.5506861% | 82.5507670% |
| 拼图十格 | 89.6719037% | 89.6820512% |

视频第 01 视角下降 0.00928 个百分点。第 02、06 视角的叶片端部采样 RMS 分别由 27.33 px 降到 26.52 px、由 28.55 px 降到 27.47 px，最大偏差仍为投影屏宽的 20.96% 和 21.94%。七个采样视角仍有六个超过 5%。[叶片采样](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

独立读回通过，包含 853 个闭合 STEP 实体。FreeCAD 原生四视图核对了 696 个可见对象和 70 种颜色。模型保留实测平面屏、外挂筒、屏幕侧控件、格栅和四根支柱。[交付校验](../../delivery-verification-current.json) · [原生显示](native-display/native-display-verification.json)

[视频十方位](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

复建时，使用 v250 保存 FCStd 与重建网格运行 `tools/experiment_drone_petal_axial.py --construction tip-splice --station 111 --factor 1.28 --tip-radial-shift .75 --tip-centre-shift 1 --leaf-indices 6 10`。用 `tools/finalize_drone_petal_axial.py` 恢复显示数据与其余 BRep，并导出 STEP。固定相机和叶片采样沿用 v250 的配置。[基线与相机](../v250-brow-tip-profile/README.md)
