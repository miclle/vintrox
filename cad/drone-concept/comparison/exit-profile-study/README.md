# v46 喷口出口形态试验

2026-10-24。本轮保留正式 **v46**；试件尚未替代正式 FCStd、STEP 和预览。目标仍是侧后壳与喷口的整体接近度，四根支柱不动。

## 固定角度结果

| 检查 | v46 | 内收 4° 试件 |
| --- | ---: | ---: |
| 十方位轮廓均值 | 84.84526% | 84.89382% |
| 七图轮廓均值 | 81.94253% | 81.97971% |
| 正后视频轮廓 | 见逐帧报告 | 下降 0.01884 个百分点 |
| 图 04 叶片末端抽样 RMS | 17.685px | 16.123px |
| 图 05 叶片末端抽样 RMS | 16.955px | 15.667px |
| 视频 60 帧末端抽样 RMS | 4.149px | 4.598px |
| 视频 120 帧末端抽样 RMS | 3.220px | 2.338px |
| 视频 180 帧末端抽样 RMS | 3.122px | 4.320px |

末端抽样使用保存模型的实际圆弧，包含未做遮挡剔除的弧段；手工亮边取点存在角点/层次对应不确定性，且是在查看 v46 差异时选取，不能当作独立验收集。该口径不同于此前的连续圆拟合分数。整机 IoU 也不表示细节还原率。

- [图 04：参考 / v46 / 试件 / 50% 叠加](still-04-taper.png)
- [图 05：参考 / v46 / 试件 / 50% 叠加](still-05-taper.png)
- [视频左后](video-02-taper.png) · [正后](video-04-taper.png) · [右后](video-06-taper.png)
- [十方位完整对比](taper-4/video-comparison/comparison-board.png) · [七图完整对比](taper-4/still-comparison/comparison-board.png)
- [逐帧视频分数](taper-4/video-comparison/comparison-report.json) · [逐图分数](taper-4/still-comparison/comparison-report.json)
- [实际末端圆弧检查](taper-4/terminal-arcs-check.json) · [图 04 取点](still-04-observations.png) · [图 05 取点](still-05-observations.png)

## 做了什么

用保存的 v46 生成独立试件，十二片叶片及各自附属压条、凹槽衬片、导轨、边轨、末端折边绕根部切向轴向内转 4°，共 **96 个对象**。每片内部零件保持共同刚体变换；金色外罩、金色口沿、根部卷边、后部凹舱和后壳不变。暗区继续由凹入壳体和遮挡形成，没有新增圆筒来填补阴影。

96 个变换实体通过 advanced BOP、闭合/单实体和体积不变检查；保存读回后 **602 个其它对象**几何签名不变，四根支柱双向实体差集为 0，十二片主叶片与固定根部卷边最大间隙约 7.11e-15mm。试件仍是外观研究；没有声学、机械机构或制造验收。[保存检查](taper-4/candidate-check.json)

本轮改善较小，金色口沿及整个出口的低视角偏移仍在。两个视频斜视角的末端边缘变差，正后方轮廓也略退步。暂保留试件，当时计划将收口方向重建为受控的共同根部曲面（已由下文试件完成），并同步核对根部连接及末端验证，不能跳过原有“共用根环/出口圆”检查直接覆盖正式模型。

## 排除的解释

1. **焦距诊断**：只用既有十二个参考地标，联合拟合三个后视图的共同焦距得到 79.81mm；各视图的地标坐标 RMS 变化很小。2px 扰动下结果范围约 68.14–91.65mm（不是置信区间）。诊断渲染的分数变化来自相机变化，不能计入几何改进；正式相机仍保持 88mm。[拟合记录](focal-diagnostic.json) · [图 05 诊断](still-05-focal.png)
2. **整体出口圆缩小/后移**：将低视角手工末端点与原有三个视频角度一起拟合，得到更小、靠后的圆；低视角改善，但视频两个斜视角 RMS 从约 4.10/2.78px 恶化到约 8.96/8.27px，未采用。[记录](multiview-exit-fit.json)

## 来源与复现

[审查记录及哈希](review.json)。正式 v46 SHA-256：`475c208851231c3c98da53e59c62ad1a18de1bf969f6d0622db8e5f93b03b7e5`。试件 SHA-256：`3b05576acdf41ee8d72bead9f290d29ea2bcfe4f3240926c73dfe223be7bb56b`。

从仓库根目录运行，使用 FreeCAD 内置 Python 与既有 Blender 渲染器：

- `tools/experiment_drone_exit_taper.py --base-model <v46.FCStd> --base-meshes <v46 meshes.json> --degrees 4 --output <空目录>`
- `tools/render_drone_concept.py`：指定试件 `--model`、对应 `--meshes`；两次分别使用原 `comparison/cameras.json` 和 `comparison/stills-51/cameras.json`，保持 CPU / 16 samples。
- `tools/compare_drone_reference.py`：分别生成十方位和七图比较，不做图像变形。
- `diagnostic-scripts/fit-exit-multiview.py`、`measure-taper.py`、`prepare-review.py` 保存本轮测量与裁图步骤；从仓库根目录运行，测量脚本要求正式基线仍为 v46，防止后来版本被误当基线。

网格缓存和 v46 基线副本保存在 `review.json` 指向的本地缓存目录；未加入仓库。试件 FCStd 是几何研究文件，材质通过哈希绑定的基线网格传给渲染器，不作为正式 GUI/STEP 交付。本轮未提交或推送。

## 本轮证据检查

[检查记录](study-validation.json)：148 张 PNG、6 个脚本语法、来源/相机/模型哈希及 96 个保存实体检查通过；相邻主叶片体积交叠为 0，最小间隙约 1.197mm。此间隙是外观试件的几何结果，不是机构公差验收。`git diff --check` 通过。

## 后续：共同根环曲面试件（2026-10-24）

已完成上一轮提出的共同根部曲面重建：根部截面与出口平面保持，叶片半径沿长度逐渐收小，末端半径 **43.6→41.5mm**；衬片、压条、导轨、边轨与折边跟随曲面。初始只改外层的试件与旧内衬产生交叠，因此又同步重建内部喉管和锥面，共改动 **98 个对象**。

| 固定相机检查 | v46 | 整片内收 4°（上一轮） | 共同根环曲面 |
| --- | ---: | ---: | ---: |
| 十方位 IoU 均值 | 84.84526% | 84.89382% | 84.88164% |
| 七图 IoU 均值 | 81.94253% | 81.97971% | 81.97064% |
| 原三个视频角度的连续出口圆 RMS | 3.298px | 口径不同，不直接比较 | 3.675px |
| 两对可见导轨间距 RMS | 0.791px | 未复测此项 | 1.000px |

正后方轮廓下降 0.02174 个百分点；其它视频变化逐帧保存。上述微小分数变化不表示整体形体已还原。共同根环试件没有解决金色口沿和出口的低视角整体偏移，且导轨间距和原视频出口边界略有退步，因此**继续保留正式 v46，不将本试件发布为 v47**。四根支柱、金色外罩、后壳及凹舱均不变。

- [图 04 对比](still-04-profile21.png) · [图 05 对比](still-05-profile21.png)
- [左后视频](video-02-profile21.png) · [正后视频](video-04-profile21.png) · [右后视频](video-06-profile21.png)
- [十方位整板](profile-21-lined/video-comparison/comparison-board.png) · [七图整板](profile-21-lined/still-comparison/comparison-board.png)
- [候选审查和逐视角变化](profile-review.json) · [保存实体与证据检查](profile-validation.json)
- [内衬同步前的交叠](profile21-initial-liner-check.json) · [同步后的全叶片间距与四支柱检查](profile-21-lined/candidate-check.json)
- [共面出口圆](profile-21-lined/outline-check.json) · [口沿接触](profile-21-lined/lip-check.json) · [导轨可见间距](profile-21-lined/guide-width.json)

98 个保存实体有效、闭合且单实体，600 个其余对象几何签名保持；36 个通道探针确认空槽及背底仍存在。相邻主叶片无体积重叠，最小间隙约 2.216mm；叶片到喉管/内部锥面最小间距约 1.387mm；四根支柱实体差集为 0。108 张候选 PNG 及渲染/ID 来源哈希检查通过。零收口构造另核对了第 7 片叶片的八个零件及两件内表面，与 v46 对应实体等价；没有将这一抽样写成全模型等价。

另外用原视频 23 个根环观察点放开轴角进行诊断，最佳试验角约 34.54°，原假设为 35.02°，RMS 约 2.89→2.49px。它不支持凭静态图印象大幅倾斜喷口；拟合仍复用了原观察点，并非独立验收。[轴角记录](root-axis-free-fit.json)

下一步核对静态图中口沿/末端与参考视频重建之间的对应关系，先区分标定误差、边缘识别和真实几何差异。任何相机诊断均单列，不能计作模型改进；正式对比相机继续冻结。

源构造为 `tools/drone_petal_profile.py`，候选由 `tools/experiment_drone_petal_profile.py --inset 2.1` 和 `diagnostic-scripts/complete-profile.py` 生成。原始 96 件外层试件的源模块冻结在 `profile-21/source-profile.py`，随后扩展了内表面构造。两份大网格文件已移入 `profile-review.json` 中记录的本地缓存；重新运行完成脚本前将相应缓存放回 `profile-21/meshes.json`。正式生成器及正式模型哈希未变，未提交或推送。
