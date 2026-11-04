# v71 屏框每边外扩 2 mm 候选（未采用）

以 v69 为基线，继承 2.2 mm 底部回环，仅重建 `ScreenBezel`、`BezelLip`：内框外尺寸 220 × 172 → 224 × 176 mm，压边名义外尺寸 224 × 176 → 228 × 180 mm。圆角压边的真实包络以 [保存参数](candidate-check.json) 为准。202 × 152 mm 开口、实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm 保持；其余 696 件 BRep 字节不变，四根支柱、中心座、外挂筒、侧控件和格栅全部保留。

固定相机真实 CAD 比较：视频十方位平均 IoU **85.551238%**（v69 **85.553320%**，−0.002082 个百分点），七张静态图 **82.184177%**（v69 **82.259620%**，−0.075442 个百分点）。局部改善不足以抵消 video-08 等视角退步，故不采用；正式入口保持 v61，研究优选保持 v69。[逐视角结论](candidate-review.json)保留全部退步。

[独立读回](readback-verification.json)：698 保存对象、696 可见对象，全部实体有效闭合；STEP 只导出这 696 个可见对象，1008 个实体，与可见 FCStd 实体数相等，体积相对误差 3.65×10⁻⁷。历史候选的 1010 实体包含两个隐藏占位，本轮不将其误判为丢件。[导出一致性](export-consistency.json)还确认两件新网格与重新打开的保存 FCStd 逐顶点、逐面一致。

696 个彩色网格对象、74 组 RGB；2095 个 GUI 外观成员取自正式 v61。[归档检查](archive-preservation.json)确认只有两件屏框 BRep 改变。原生 FreeCAD 窗口无法被当前界面工具读取，**未完成原生窗口目视检查**；保存颜色数据、彩色渲染与原生显示验收分别记录。

- [视频十方位叠加板](video-comparison/comparison-board.png) · [静态七图叠加板](stills-comparison/comparison-board.png)
- [彩色整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)
- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [保存参数与哈希](candidate-check.json)

复现时从仓库根目录执行；FreeCAD Python 需设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_bezel_expansion.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v71-rebuild --expansion 2 --revision v71-bezel-expand2mm
```

渲染沿用 `tools/render_drone_concept.py`、CPU 和 v69 的两份 cameras.json；比较沿用 `tools/compare_drone_reference.py`，无图像拉伸、非刚性变形、逐件配准或删件。比较仅排除新增四支撑区域；彩色预览包含全部支撑。参考曲面屏/透明罩和不可见面仍为假设；5% 全部主要部件轮廓与 90% IoU 目标未达，不代表制造、打印、装配、承力、光学、声学、热、电气或实物验收。
