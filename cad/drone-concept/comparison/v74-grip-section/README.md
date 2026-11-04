# v74 提手包覆截面实验（未采用）

从 v69 出发，只重建 `GripBand0` 至 `GripBand9` 十件包覆实体。周期 B 样条截面改为较宽平面、小圆角、较低折皱幅度。视频平均略升，但静态下降，且 STEP 体积阈值失败，未采用。 握把芯、端箍、侧支臂、宽度和位置保持；实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm、四支柱及其他部件保持。参考包覆层更平坦的判断是外观假设，不是原件测量或源拓扑恢复。

| 固定相机组 | v69 | 本候选 | 差值 |
| --- | --- | --- | --- |
| video | 85.553320% | 85.557719% | +0.004399 个百分点 |
| stills | 82.259620% | 82.158027% | -0.101592 个百分点 |

[逐视角结果](candidate-review.json)保留所有退步。十个视频视角与七张静态图均使用 v69 相机，没有重新配准、图像拉伸或删件；比较排除新增支撑区域，预览保留全部支撑。静态第六张线框图的前景分数不能解释为实体轮廓精度。

[提手局部对照](grip-comparison.png)和[局部数据](grip-comparison.json)使用同一上沿条带 ROI，包含邻近翼板与天线，并非单独提手轮廓验收。外形与遮挡仍有差异，不能只凭“更平”宣称还原改善；正式入口保持 v61，外形研究优选保持 v69，v73 嘴部仍是独立细节候选。

[独立读回](readback-verification.json)：698 个保存对象、696 个可见对象、1008 个 STEP 实体，均有效闭合；十件网格与最终重开 FCStd 逐顶点、逐面一致，四支柱保持。v74 读回命令退出码为 1：体积相对误差 **1.74634×10⁻⁵ > 10⁻⁶**。没有放宽阈值或改写通过状态。[逐件 STEP 复核](export-failure-detail.json)保留十件体积差异，末端 GripBand9 约 +54.69 mm³。源 FCStd 是该失败实验的几何记录，STEP 不作为一致性通过交付。

[归档检查](archive-preservation.json)确认只有十件包覆 BRep 变化，其余 688 件字节一致；2095 个 GUI 外观成员与正式 v61 一致。彩色网格为 696 对象、74 组 RGB。FreeCAD RPC 连接拒绝，原生界面读取为 cgWindowNotFound；**原生窗口目视检查未完成**，保存颜色和 Blender 渲染不能替代它。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建参数与哈希](candidate-check.json)
- [视频叠加／差异](video-comparison/comparison-board.png) · [静态叠加／差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

仓库根目录复现，FreeCAD Python 设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_grip_section.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --base-mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v74-grip-section-rebuild --revision v74-grip-section
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_grip.py --candidate cad/drone-concept/comparison/v74-grip-section
```

渲染使用 `tools/render_drone_concept.py`、CPU 和 v69 视频／静态 cameras.json；叠加差异使用 `tools/compare_drone_reference.py`。读回使用 `tools/readback_drone_loop_radius_candidate.py`，`--expected-step-solids 1008`，`--verify-mesh-objects GripBand0 GripBand1 GripBand2 GripBand3 GripBand4 GripBand5 GripBand6 GripBand7 GripBand8 GripBand9`；其余参数分别为本目录 model、step、mesh 和 v69 baseline。

90% 整机轮廓与所有主要部件完整轮廓 5% 目标仍未完成。平面屏／参考曲面罩和不可观察面仍有假设，不代表打印、装配、承力、声学、光学、热、电气或实物验收。
