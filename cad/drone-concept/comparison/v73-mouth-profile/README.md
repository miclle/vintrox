# v73 嘴部轮廓实验（细节研究候选）

从 v69 出发，只重建 `PixelMouth`、`PixelSmileHighlight` 两件实体，眼睛保持 v69；嘴部在一个拟合视角和两个留出视角、三个阈值下的特征 IoU 均改善，保留为细节研究候选。 使用视频 frame 270 手工描点，通过既有固定相机反投影到 Y = −9.6 mm 平面，生成真实 CAD 轮廓实体。实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm、屏框、四支柱及其余外形保持。曲面透明罩仍为外观假设。

整机轮廓视频十方位 / 静态七图 IoU 为 **85.553320% / 82.259620%**，与 v69 完全相同；屏内调整没有改善整机外轮廓。正式模型继续为 v61，外形研究基线继续为 v69。

[嘴部比较](expression-comparison.json)采用固定相机投影 ROI、绿色通道阈值 140 / 160 / 180、2 px 闭运算与孔洞填充。下列每格依次列三个阈值下 v69 → 候选的特征 IoU：

| 视角 | 140 / 160 / 180 |
| --- | --- |
| video-00（留出） | 0.526 → 0.815 / 0.501 → 0.882 / 0.512 → 0.876 |
| video-08（留出） | 0.500 → 0.635 / 0.501 → 0.633 / 0.499 → 0.628 |
| video-09（拟合） | 0.562 → 0.937 / 0.569 → 0.710 / 0.525 → 0.977 |

[完整细节对照图](expression-comparison.png)与[结论报告](candidate-review.json)保留眼睛退步及所有边缘误差；v73 未改眼睛的渲染掩码仍有小于 0.001 的 IoU 差异，不等同于几何修改。源图纹理、玻璃反光和阈值敏感性会影响结果，部分边缘 p95 仍可能退步；这些局部掩码分数不能证明全部主要部件完整轮廓偏差 ≤5%。ROI 仅作诊断裁切，没有图像配准、拉伸或几何变形。

[独立读回](readback-verification.json)：698 个保存对象、696 个可见对象、1008 个有效闭合 STEP 实体；可见 FCStd 与 STEP 体积相对误差约 3.66×10⁻⁷。修改网格与最终重开 FCStd 逐顶点、逐面一致，四支柱保持。[归档检查](archive-preservation.json)确认仅 2 件 BRep 改变，其余 696 件字节一致；2095 个 GUI 外观成员与正式 v61 一致。彩色网格为 696 对象、74 组 RGB。原生窗口目视检查未完成；离屏 GUI 尝试因 OpenGL 不支持退出，不能算显示验收。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建参数与哈希](candidate-check.json)
- [视频叠加及差异](video-comparison/comparison-board.png) · [静态叠加及差异](stills-comparison/comparison-board.png)
- [整体彩色预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

在仓库根目录复现；FreeCAD Python 需设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_expression.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v73-mouth-profile-rebuild --revision v73-mouth-profile --features mouth
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_expression.py --baseline cad/drone-concept/comparison/v69-underbody-loop-radius2p2 --candidate cad/drone-concept/comparison/v73-mouth-profile
```

渲染使用 `tools/render_drone_concept.py`、CPU 和 v69 的视频/静态 cameras.json；整机比较使用 `tools/compare_drone_reference.py`，与基线相同地排除新增支撑区域，预览包含全部支撑。构建时与提交时脚本哈希的关系见归档检查；v72 早于嘴部独立选项，保留历史构建哈希。

本轮未完成 90% 整机轮廓目标，不代表制造、打印、装配、承力、光学、声学、热、电气或实物验收。
