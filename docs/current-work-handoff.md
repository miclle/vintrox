# VINTROX Drone 外观迭代交接

目标仍在执行。当前发布基线为 `miclle/vintrox` 的 `main` 上的 v259，采用普通 Git 交付。可从 `b0da9f19` 追溯 v242 模型，从 `6c87b15b` 查阅 v245、v246 的试验参数和对照。[v259 正式记录](../cad/drone-concept/comparison/v259-rear-beacon-length/README.md) · [v245 与 v246](../cad/drone-concept/comparison/v245-v246-petal-terminal/README.md)

## 当前证据

- v259 保留实测 210 × 160 × 2 mm 平面屏、外挂筒、侧控件、格栅和四根支柱。曲面罩按参考外观推导，原作内部和遮挡细节仍有未知项。[设计说明](drone-concept.md)
- 视频十方位、静态七图和拼图十格的平均 IoU 分别为 86.0081%、82.5743%、89.7727%。固定相机使用保存 CAD 渲染，比较时排除新增支撑总成。90% 视频整圈与主要部件 5% 的目标仍待达成。v257 的大喷口叶片末端复测中，七个已标注视角有六个超过 5%，两处侧后视的最大偏差为 20.96% 和 21.94%。[交付与固定相机](../cad/drone-concept/delivery-verification-current.json) · [叶片复测](../cad/drone-concept/comparison/v257-mirrored-nozzle-tips/visible-petal-edges.json)
- `python3 tools/verify_drone_current_delivery.py` 核对 FCStd 和 STEP 哈希、696 个可见对象、853 个闭合 STEP 实体，以及预览和四个原生显示视图。v259 的独立保存读回和 FreeCAD 颜色记录随正式交付保存。[读回报告](../cad/drone-concept/readback-verification.json) · [颜色记录](../cad/drone-concept/comparison/v259-rear-beacon-length/native-display/native-display-verification.json)
- v245 新增三处高级几何检查失败。v246 通过候选几何与接合检查，视频得分微升，静态图略降，七个叶片采样视角仍有六个超过 5%。两版均保留试验记录，v246 的 STEP 独立读回和原生颜色显示待验证。参数可配合 v242 的保存网格重建候选。[试验记录](../cad/drone-concept/comparison/v245-v246-petal-terminal/README.md)
- 重新运行 `tools/measure_drone_lower_pod_outline.py` 读取 v242，确认两侧各 18 片小喷口叶片。四个拟合视角的口沿测量 RMS 为 4.53 px，两个未参与拟合的视角为 7.38 px，最大 12.62 px。测量限定于外端圆弧。小喷口外露部分与前罩内衬仍待结合可见边缘和参考阴影核对。[小喷口读回](../cad/drone-concept/comparison/v242-belly-y097/lower-pod-outline-check.json) · [视频对象归因](../cad/drone-concept/comparison/v242-belly-y097/video-comparison/boundary-regions.json)
- v247 小喷口镜像姿态试验降低了两张未参与拟合视图的末端偏差，三组整机 IoU 均下降。六处参考近景显示前罩内衬和小喷口多处像素归因落在仍可辨认的暗色表面。后续几何更新应以可辨认的外沿及实体交界为依据。[v247 对照与参数](../cad/drone-concept/comparison/v247-small-pod-pose/README.md)
- v248 给前罩内衬两处前下缘加 5 mm 圆角。侧视的一处内衬峰值偏差由 7.97% 降至 6.92%，前罩总成外边的两处侧视峰值仍为 8.67% 和 9.48%。圆角在若干方位被外罩或包边遮住，三组整机评分变化很小。接下来检查前罩本体和包边的端部关系。[v248 局部标注与整机对照](../cad/drone-concept/comparison/v248-brow-tip-roundover/README.md)
- v249 在外罩、包边和内衬端部切出 7 mm 圆弧。两处侧视的前罩总成最大偏差降至 5.09% 和 5.02%。对象 ID 显示圆弧前方残留薄边主要属于外罩本体。视频和静态得分小幅提高，拼图略降，正式交付采用 v242。[v249 对照](../cad/drone-concept/comparison/v249-brow-assembly-roundover/README.md)
- v250 扩展切削范围并采用 8 mm 圆弧，两处侧视频视角的前罩端部偏差降至 4.69% 和 4.26%。[v250 逐点测量](../cad/drone-concept/comparison/v250-brow-tip-profile/brow-tip-samples.json)
- v251 与 v252 从 v250 的保存几何延长并外移大喷口叶片末段。两处侧后视的十条参考点射线均未碰到 v250 几何，候选使两处局部偏差有所下降，静态七图整机均值也下降。v253 的第 9 号脊条分裂为两个实体，构建终止。[试验与射线记录](../cad/drone-concept/comparison/v251-v253-petal-tip-screen/README.md)
- v254–v256 筛查了另一组径向和中心偏移。v256 通过保存几何和接合检查，视频与拼图提高，静态差异仍集中在 `still-05`。v251 的像素归因将该视角的外溢主要定位在第 8 至 11 号叶片。[筛查记录](../cad/drone-concept/comparison/v254-v256-petal-tip-refine/README.md)
- v258 在 v257 上调整第 0、4、5、11 号叶片。两处侧后视的端部最大偏差降到 19.36% 和 20.89%，但视频和静态组的整机均值下降，正式模型采用 v257。[v258 固定相机对照](../cad/drone-concept/comparison/v258-mirrored-nozzle-pairs/README.md)

- v259 以斜视缺失轮廓为依据，加长两侧后部指示灯。三组均值提高，静态第 06 图下降 0.00855 个百分点。翼板外缘在多个方位仍有缺失，值得用前后视和侧视联合定位。[v259 对照与十方位诊断](../cad/drone-concept/comparison/v259-rear-beacon-length/README.md)
- v260 在当前 v259 保存模型上重放黄翼后缘内收 5 mm、前缘 `.5 5.5 2.5 2` mm 的真实 CAD 方案。视频、静态图和拼图均值变化分别为 +0.00036、+0.00006 和 0 个百分点，属于渲染与三角化噪声量级，候选不采用。[v260 筛选](../cad/drone-concept/comparison/v260-gold-wing-v259-screening/README.md)
- v261 筛选大喷口全部叶片的 0.90 和 0.88 倍局部切向收窄。两档视频和拼图均下降，静态图分别提高 0.01234 和 0.01600 个百分点，候选均不采用。两档 STEP 独立读回均为 1033 个闭合有效实体。[v261 筛选](../cad/drone-concept/comparison/v261-nozzle-contract-screening/README.md)
- v262 筛选镜像叶片 `5/11`、`6/10` 的 0.90 倍局部收窄。`5/11` 视频提高 0.00004 个百分点，`6/10` 下降 0.00983 个百分点，均未采用。[v263 记录](../cad/drone-concept/comparison/v263-mirrored-petal-screening/README.md)
- v263 继续筛选 `0/4` 的 0.90 倍和 `5/11` 的 0.95 倍局部收窄。`0/4` 在视频、静态图和拼图均提高约 0.000058 个百分点，属于噪声量级，`5/11` 视频仅提高 0.000006 个百分点，均不替换 v259。`0/4` 和 `5/11` 的 STEP 独立读回分别为 869 和 866 个闭合有效实体。[v263 记录](../cad/drone-concept/comparison/v263-mirrored-petal-screening/README.md)
- v264 筛选前罩总成深度 0.96 倍和内衬高度 0.95 倍。前者视频均值下降 0.06154 个百分点，后者下降 0.00087 个百分点，均不采用。两组均完成保存 FCStd、STEP 和视频固定相机证据。[v264 筛选](../cad/drone-concept/comparison/v264-brow-screening/README.md)
- v265 筛选 `ClosedBellyPan` Y 向 0.99 和 1.01 倍。0.99 倍在三组均值上仅提高约 0.000025、0.000001、0.000003 个百分点，属于噪声量级，1.01 倍视频下降 0.000010 个百分点，均不采用。[v265 筛选](../cad/drone-concept/comparison/v265-belly-y-screening/README.md)
- v266 尝试用历史拟合口沿重建 v259 小喷口族，`LowerPodRib_1_0` 未通过有效、闭合、单实体门槛，候选在几何阶段停止，没有进入渲染或正式交付。[v266 门槛记录](../cad/drone-concept/comparison/v266-lower-pod-lip-gate/README.md)
- v267 筛选 `BassVisualCone` 凹碗收缩 0.5 mm 与 1.5 mm。视频分别提高约 0.000071 和 0.000068 个百分点，0.5 mm 档静态和拼图分别下降 0.000112 和 0.000066 个百分点，均不采用。[v267 筛选](../cad/drone-concept/comparison/v267-bass-visual-cone-screening/README.md)
- v268 筛选 `BottomChassis` Y 向 0.99 倍，视频、静态图和拼图分别提高 0.000021、0.000010 和 0.000003 个百分点，属于噪声量级，未采用。[v268 筛选](../cad/drone-concept/comparison/v268-bottom-chassis-screening/README.md)

## 续接

1. 以 v257 的大喷口末端复测和 v259 的对象级外溢分布为基线，沿 `video-02`、`video-03` 和 `video-06` 的可见边缘核对叶片与邻件遮挡，再试验真实 CAD 端部几何。用小喷口参考近景区分壳体与叶片的交线、阴影和出口边缘。[大喷口复测板](../cad/drone-concept/comparison/v257-mirrored-nozzle-tips/visible-petal-edges.png) · [v259 对象归因](../cad/drone-concept/comparison/v260-gold-wing-v259-screening/video-diagnostic/boundary-regions-board.png) · [小喷口近景](../cad/drone-concept/comparison/v247-small-pod-pose/v242-contour-detail.png)
2. 从保存 v259 生成候选，在临时目录保存 FCStd 和网格。沿用十个视频姿态、七张静态图与十格拼图检查整机轮廓，再复测关键局部，以同相机的投影屏宽归一化。进入正式交付的候选需补齐 STEP 独立读回、接合与四支柱复查、原生颜色与可见性检查，并同步正式模型、预览与文档。[编辑与复现](drone-concept.md#编辑与复现)
3. `24e3f39f` 已从当前快照移除 112 个落选 Drone 候选 FCStd、STEP 和几何副本。精简历史保留正式 v259 包与复现证据，当前活动分支采用普通 Git 交付，不依赖 GitHub LFS。[存储说明](storage-cleanup.md)
