# VINTROX Drone 外观迭代交接

目标仍在执行。当前发布基线为 `miclle/vintrox` 的 `main` 上的 v310，采用普通 Git 交付。[v310 正式记录](../cad/drone-concept/comparison/v310-right-wing-fold/README.md) · [v259 基线](../cad/drone-concept/comparison/v259-rear-beacon-length/README.md)

## 当前证据

- v310 保留实测 210 × 160 × 2 mm 平面屏、外挂筒、侧控件、格栅和四根支柱。曲面罩按参考外观推导，原作内部和遮挡细节仍有未知项。[设计说明](drone-concept.md)
- 视频十方位、静态七图和拼图十格的平均 IoU 为 86.1848%、82.6391% 和 89.9055%。第 210 帧右翼折面一处偏差从 7.62 px 降至 2.00 px，该视角最大偏差仍为投影屏宽的 7.65%。第 180 帧翼根保持 5.29%。视频整圈 90% 与主要部件轮廓偏差 5% 目标仍待达成。[交付核验](../cad/drone-concept/delivery-verification-current.json) · [翼缘复测](../cad/drone-concept/comparison/v310-right-wing-fold/visible-wing-edges.json)
- `python3 tools/verify_drone_current_delivery.py` 通过。FCStd 与 STEP 独立读回确认 696 个可见对象、853 个闭合实体。FreeCAD 原生四视图复核颜色和可见性。九张预览、转台和三组固定相机对照已同步。[读回报告](../cad/drone-concept/readback-verification.json) · [原生显示](../cad/drone-concept/comparison/v310-right-wing-fold/native-display/native-display-verification.json)
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
- v269 重建后肩护甲和接片，视频十方位均值降至 85.767475%，继续采用 v259。重新生成的对象 ID 将静态第 05 图两处前罩外溢归因到弧面内罩和甲片。[后肩筛选和静态诊断](../cad/drone-concept/comparison/v269-rear-shoulder-screening/README.md)
- v270、v271 对称内移前罩肩部 4 mm、2 mm。静态第 05 图分别提高 0.117545 和 0.061475 个百分点。2 mm 档避开了 4 mm 档的内衬交叠，两档视频和拼图均值下降。[三组对照](../cad/drone-concept/comparison/v270-v271-front-shoulder/README.md)
- v272、v273 分别内移弧面内罩和甲片。v272 三组均值略升，静态第 05 图的内罩外溢转为由前罩主体形成。v273 视频和拼图均值下降。[三组对照与对象归因](../cad/drone-concept/comparison/v272-v273-front-shoulder-parts/README.md)
- v274 将前罩主体和内衬横向收至 0.985 倍，十方位视频均值下降 0.028486 个百分点。静态第 05 图定位到内罩内移后露出的前罩主体上缘，可优先核对该处的局部截面。[v274 视频筛选](../cad/drone-concept/comparison/v274-brow-x0985/README.md)
- v275 通过射线将 `still-05` 前罩主体外溢分为上缘和前端两段。局部切削上缘后，静态第 05 图 IoU 与 v272 一致，视频和拼图均值略降。[固定相机对照与几何记录](../cad/drone-concept/comparison/v275-brow-upper-edge/README.md)

- v276 将前侧脸颊与桥板对称收窄 1%，27 个固定视角的轮廓 IoU 均持平或提高。保存读回、桥板接合和原生显示均通过，采用为当前模型。[正式对照](../cad/drone-concept/comparison/v276-front-cheek-x099/README.md)
- v277 筛查了两档底部回环渐变半径，四组局部采样 RMS 均下降，视频十方位均值下降 0.052838 和 0.096477 个百分点。两端半径和四支柱净空通过复核，正式采用 v276。[回环筛选与放样参数](../cad/drone-concept/comparison/v277-loop-radius-screen/README.md)
- v278 联动拟合回环路径与渐变半径，第 120 帧左右回环的最大采样偏差降到投影屏宽的 5% 以内，第 180 帧右回环上升到 25.75%。三组整机均值均下降，正式采用 v276。[三组比较与可见边界](../cad/drone-concept/comparison/v278-loop-path-fit/README.md)
- v279 将后部鳍片暗色基座的顶部降低 1.5 mm、3 mm。两档十方位逐视角 IoU 均与 v276 相同，槽顶露出的金色壳面与参考暗槽有差异，继续采用 v276。[近景与保存几何](../cad/drone-concept/comparison/v279-cooling-core-recess/README.md)
- v280 将顶罩两条凸筋从 6 mm 降到 4.5 mm、3 mm。保存实体检查通过，视频十方位均值分别降至 85.9295%、85.8692%，正式采用 v276。[固定相机对照与复建](../cad/drone-concept/comparison/v280-roof-rib-height/README.md)
- v281 在 v276 上延长四组镜像叶片末段；两个侧后视最大偏差降至投影屏宽的 17.63%、20.68%，视频和静态图整机均值均下降，正式采用 v276。[固定相机、射线与读回](../cad/drone-concept/comparison/v281-mirrored-petal-long-tip/README.md)
- v282 将四组叶片的接续面向根部前移。98 mm 与 103 mm 档出现第 4 号叶片高级几何错误，101 mm 档通过保存读回，视频十方位均值降至 85.9832%，正式采用 v276。[接续面筛查](../cad/drone-concept/comparison/v282-petal-splice-stations/README.md)
- v283 延长第 6、7、9、10 号可见叶片，视频和拼图均值分别提高 0.03880 和 0.06363 个百分点。静态 `still-05` 的第 9、10 号叶片向背景伸出，静态均值下降 0.03261 个百分点，正式采用 v276。[固定相机对照与局部归因](../cad/drone-concept/comparison/v283-visible-petal-pairs/README.md)
- v284 将同一组末段径向内收并取消局部 Y 位移。视频和拼图均值分别提高 0.03663、0.06820 个百分点，静态均值仍下降 0.02598 个百分点，正式采用 v276。[径向内收对照](../cad/drone-concept/comparison/v284-petal-tip-inward/README.md)
- v285 在 v284 叶片末段采用两档单侧斜切。静态七图均值较 v284 回升不足 0.003 个百分点，正式采用 v276。[保存读回与固定相机对照](../cad/drone-concept/comparison/v285-petal-flank-taper/README.md)
- v286 在 v276 上对提手支臂试验内倾和外倾 1.5°。两档通过 14 项接合检查，三组平均 IoU 均低于 v276。[提手倾角筛查](../cad/drone-concept/comparison/v286-handle-tilt-screen/README.md)
- v287 将 v276 的前侧脸颊和桥板沿横向再收窄 1.5%。正面 `video-09` 提高 0.13391 个百分点，三组均值中视频和拼图提高、静态持平，采用为正式版。[正式对照与复建](../cad/drone-concept/comparison/v287-front-cheek-x0985/README.md)
- v288 将 v287 的前侧脸颊和桥板再收窄 3%。视频均值下降 0.004814 个百分点，拼图均值提高 0.001838 个百分点，正式采用 v287。[三组对照](../cad/drone-concept/comparison/v288-front-cheek-x097/README.md)
- v289 小喷口叶片轴向延长 6% 后，两个未参与原拟合的视角端缘 RMS 降至 6.28 px，整机三组 IoU 均下降，正式采用 v287。[保存几何和三组对照](../cad/drone-concept/comparison/v289-small-pod-axial-extension/README.md)
- v289 接合复核已改用同侧和局部扇区配对，延长档的 216 项距离检查全部通过。缩短 6% 时，20 对叶片与口环的原有间隙增大。[更正后的接合检查](../cad/drone-concept/comparison/v289-small-pod-axial-extension/README.md)
- v290 以口环站位为基准缩短叶片 6%，通过 216 项距离检查，三组整机均值均提高。原拟合外两视角的端缘 RMS 由 7.38 升至 8.30 px，正式版采用 v287。[整机与端缘对照](../cad/drone-concept/comparison/v290-small-pod-axial-contraction/README.md)
- v291 将小喷口外罩和口环延长 0.25 mm，三组整机均值略降，正式版采用 v287。1 mm、2 mm 档分别导致 2 处和 8 处原有口环与叶片接触分离。[小喷口外罩筛查](../cad/drone-concept/comparison/v291-small-pod-shell-extension/README.md)
- v292 将前罩肩部弧面内罩及白纹各向内移 2 mm。静态第 05 图的左内罩外溢下降，前罩主体仍有外溢。三组整机均值提高，采用为正式版。[几何、像素归因与交付](../cad/drone-concept/comparison/v292-brow-shoulder-inset/README.md)
- v293 核对 v292 底部六个固定视角。参考线框显示回环根部板件，静态图 05 的底壳外溢归因同时覆盖暗底面、线束和间隙。下一轮结合可见弧段联动筛选回环路径与粗细，复核第 180 帧的遮挡。[底部近景与复现](../cad/drone-concept/comparison/v293-underbody-visibility/README.md)
- v294 对回环路径与截面做三档筛选，视频十方位均值均下降。等径档在第 120 帧左侧达到 4.84% 局部最大偏差，第 180 帧右侧升至 22.95%。正式采用 v292。后续路径拟合应约束第 180 帧可见边界，并引入独立侧后视角检查。[候选对照与复现](../cad/drone-concept/comparison/v294-underbody-loop-screen/README.md)
- v295 新增第 90 帧标注并提高第 180 帧拟合权重。第 120 帧左右最大偏差均低于 5%，第 180 帧仍为 19.65%，独立第 150 帧由 5.94% 升至 9.02%。正式采用 v292。下一次筛选优先评估保存 CAD 的可见边缘及遮挡。[拟合与固定相机复测](../cad/drone-concept/comparison/v295-loop-multiview-fit/README.md)
- v296 按射线遮挡结果限制回环前段的位移，第 180 帧最大偏差回到 v292 的 6.28%，第 150 帧仍退步，视频十方位均值为 85.9433%。正式采用 v292。[射线与候选](../cad/drone-concept/comparison/v296-loop-root-blend/README.md)
- v297 将第 6、10 号和第 7、9 号喷口叶片分对筛选。第 7、9 号内移 3 mm 后视频和拼图均值分别为 86.0532% 和 89.8290%，静态图 05 下降 0.04870 个百分点。正式采用 v292。[固定相机、接合与复建](../cad/drone-concept/comparison/v297-nozzle-pair-screen/README.md)
- v298 收窄第 7、9 号叶片末段外侧切向边缘，静态图 05 的降幅收窄到 0.03189 个百分点，视频十方位均值为 86.0440%，正式采用 v292。[三组对照与复建](../cad/drone-concept/comparison/v298-nozzle-flank/README.md)
- v299 将第 7、9 号叶片末段径向内收增至 3.6 mm。静态图 05 较 v292 略退步，4.5 mm 档在脊条的保存几何检查失败。正式采用 v292。[径向筛选](../cad/drone-concept/comparison/v299-nozzle-radial-inset/README.md)

- v300 组合后肩收窄和第 7、9 号叶片末段内收。三组整机均值均提高，静态第 03 图下降 0.12913 个百分点。正式包通过 STEP 读回与原生颜色检查。[固定相机与复建](../cad/drone-concept/comparison/v300-rear-shoulder-nozzle/README.md)
- v301 按静态第 03 图和视频第 150 帧的射线定位，在四档接续位置恢复后肩前段宽度。Y=240 mm 档恢复静态第 03 图的轮廓得分，静态七图均值略降。正式采用 v300。[局部宽度与固定相机](../cad/drone-concept/comparison/v301-local-rear-shoulder/README.md)

- v302 仅在 Z=137 mm 以上恢复后肩宽度。静态第 03 图较 v300 提高 0.07055 个百分点，三组整机均值均提高。正式包通过独立 STEP 读回与 FreeCAD 原生颜色检查。[v302 固定相机与复建](../cad/drone-concept/comparison/v302-upper-rear-shoulder/README.md)
- v303 筛选两档水平和两档斜向后肩接续。斜率 1 档静态第 03 图提高 0.02057 个百分点，第 06 图得分相同，三组整机均值略降。正式采用 v302。[接续几何与固定相机](../cad/drone-concept/comparison/v303-rear-shoulder-transition/README.md)

- v304 将前侧护壳厚度缩至 75%。正面视频提高 0.04802 个百分点。六个直接邻件的距离复核在左右两侧均保住原有接触。侧后桥板接续试验未改变视频分数，仍需按参考边界判断。[v304 固定相机与复建](../cad/drone-concept/comparison/v304-front-cheek-thickness/README.md)
- v305 分对延长第 0、4 号和第 5、11 号喷口叶片。第 5、11 号使第 60、180 帧的末缘偏差降至 18.94% 和 20.68%，两档视频、静态均值均下降。该阶段采用 v304。[侧后视对照](../cad/drone-concept/comparison/v305-nozzle-pair-terminal/README.md)

- v306 对称微调左右翼板，采用半角度档。视频十方位提高 0.11662 个百分点，静态七图和拼图十格均值同时提高。静态第 01 图下降 0.26592 个百分点，需复核翼缘及遮挡。翼板四处接合检查通过。[v306 固定相机与重放](../cad/drone-concept/comparison/v306-wing-pose/README.md)

- v307 筛选第 6、10 号喷口叶片的两档末段。109.5 mm 接续档提高侧后视轮廓得分，静态七图均值下降，侧后视最大偏差仍为 20.96% 和 21.94%。正式采用 v306。[保存几何和三组对照](../cad/drone-concept/comparison/v307-nozzle-pair-6-10/README.md)

- v308 收窄第 6、10 号叶片末缘，静态第 05 图的回退缩小约一半，视频和拼图增益也缩小。静态均值仍低于 v306。[外溢归因、几何与三组对照](../cad/drone-concept/comparison/v308-nozzle-outer-flank/README.md)

- v309 延长第 1、3 号叶片末段，第 90 帧局部最大偏差从 8.85% 降到 8.42%。三组平均 IoU 略降，正式采用 v306。[保存几何与固定相机](../cad/drone-concept/comparison/v309-inner-nozzle-leaf-pair/README.md)

- v310 采用右翼折面局部站位调整。三组整机均值小幅提高，第 180 帧翼根复测与 v306 相同。全量拟合使跨视角整机指标下降。[重放与候选记录](../cad/drone-concept/comparison/v310-right-wing-fold/README.md)

## 续接

1. 结合 `video-02`、`video-03`、`video-06` 和 `still-05` 核对喷口口环及叶片末缘。沿第 9、10 号叶片在静态近景中的外缘定位外溢截面，检查末段收窄能否同时保住两个侧后视频方位的轮廓收益。用小喷口参考近景区分壳体与叶片的交线、阴影和出口边缘。[大喷口视频近景](../cad/drone-concept/comparison/v281-mirrored-petal-long-tip/v276-tip-crops.png) · [大喷口静态近景](../cad/drone-concept/comparison/v283-visible-petal-pairs/still-delta-crops.png)
2. 从保存 v310 生成候选，在临时目录保存 FCStd 和网格。沿用十个视频姿态、七张静态图与十格拼图检查整机轮廓，再复测关键局部，以同相机的投影屏宽归一化。进入正式交付的候选需补齐 STEP 独立读回、接合与四支柱复查、原生颜色与可见性检查，并同步正式模型、预览与文档。[编辑与复现](drone-concept.md#编辑与复现)
3. GitHub 发布分支使用精简历史，保留当前正式包、关键基线对照和试验报告。用正式 CAD 与固定相机生成新候选所需网格。[存储说明](storage-cleanup.md)
