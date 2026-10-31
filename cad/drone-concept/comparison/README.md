# Drone 参考比较证据

当前正式模型为 **v61 喷口外罩中段减薄**：十方位视频平均轮廓 IoU **85.49201687%**，七张静态图 **82.22681557%**。本轮只调整外罩中段，四根支柱、喷口本体和凹舱阴影语义保持；正式叠加和渲染见 [v61 视频](iteration-121-v61-nozzle-fairing-depth3-video-comparison/comparison-board.png)、[v61 静态图](iteration-121-v61-nozzle-fairing-depth3-stills-comparison/comparison-board.png) 与 [v61 交付检查](../delivery-verification-v61-nozzle-fairing-depth3.json)。

[v64 后护甲截面候选](v64-rear-shoulder-study/README.md)仅将左右 `RearArmourCheek` 截面指数改为 1.25。它完成了 FCStd/STEP 独立读回、十方位与七图真实 CAD 渲染、半透明叠加和差异图；视频平均 IoU **85.489951%** 略低于正式 v61，静态图 **82.259796%** 略高，因此保留为候选，正式模型不变。候选结论和哈希见 [candidate-review](v64-rear-shoulder-study/candidate-review.json)。

[v53 底壳收形](rear-belly-study/README.md) · [v52 警示贴片定位](nozzle-marking-study/README.md) · [v51 外罩上肩](fairing-shoulder-study/README.md) · [v50 外罩深度与灯角让位](fairing-depth-v49-study/README.md) · [v49 外罩中段](fairing-blend-study/README.md) · [v48 喷口内部凹腔](nozzle-interior-study/README.md) · [v47 根部与过渡壳联动](source-registration-study/README.md)

[v46 喷口叶片细节](petal-detail-study/README.md) · [v45 侧壳内退斜边](status-rim-study/README.md) · [v44 侧后切口修订](guard-notch-study/README.md) · [后壳圆角未采用试验](rear-fold-study/README.md)
[v43 金色翼板局部折面](wing-crease-study/README.md) · [侧视](wing-crease-study/b/detail-side.png) · [斜侧视](wing-crease-study/b/detail-oblique.png) · [前斜视](wing-crease-study/b/detail-front.png)。

[v42 后肩截面试验](rear-shoulder-relief-study/README.md) · [左后](rear-shoulder-relief-detail-left.png) · [正后](rear-shoulder-relief-detail-back.png) · [右后](rear-shoulder-relief-detail-right.png)。

[v41 叶片凹槽试验](petal-recess-study/README.md) · [正后放大](petal-recess-closeup-back.png) · [左后](petal-recess-detail-left.png) · [右后](petal-recess-detail-right.png)。

[v40 后下沿三档试验](rear-lower-edge-study/README.md) · [左后](rear-lower-edge-detail-left.png) · [正后](rear-lower-edge-detail-back.png) · [右后](rear-lower-edge-detail-right.png)。

[v39 双层口沿试验](nozzle-lip-study/README.md) · [左后](nozzle-lip-detail-left.png) · [正后](nozzle-lip-detail-back.png) · [右后](nozzle-lip-detail-right.png)。

[v38 喷口中段曲面试验](nozzle-depth-study/README.md) · [左后](nozzle-depth-detail-left.png) · [正后](nozzle-depth-detail-back.png) · [右后](nozzle-depth-detail-right.png)。

[v37 安装平面与轮廓研究](rear-profile-study/README.md) · [左后](rear-profile-detail-left.png) · [正后](rear-profile-detail-back.png) · [右后](rear-profile-detail-right.png)。

[v36 侧后壳收窄候选与回退](rear-side-width-study/README.md) · [正式模型与候选实体核对](rear-side-width-study/formal-geometry-check.json) · [左后](rear-side-width-detail-left.png) · [正后](rear-side-width-detail-back.png) · [右后](rear-side-width-detail-right.png)。

历史索引中的 v53 侧后壳底部收形记录继续保留；当前正式图组为 `iteration-92` / `stills-63`，对象分色为 `object-ids-v58`。旧候选和旧报告按其版本理解。

- [当前十方位比较板](iteration-83/comparison-board.png)、[报告](iteration-83/comparison-report.json)、[CAD 原始渲染](iteration-83-renders/render-manifest.json)。
- [七张独立图片比较板](stills-54/comparison-board.png)、[报告](stills-54/comparison-report.json)、[原始渲染](stills-54-renders/render-manifest.json)。06 是线框图，不计入十方位轮廓目标。
- [相同渲染设置下的 v6 基线](baseline-raw-v23/comparison-board.png)及[报告](baseline-raw-v23/comparison-report.json)。
- [42 个稀疏标志点](landmark-check.json)检查翼尖、翼根、灯头与实际平面显示区的位置，不证明完整轮廓通过。
- [全部参考输入索引](review-index.json)覆盖六张编号图、补充近景、十视角拼图和原始旋转视频。
- [方法、相机假设、迭代及复现](../../../docs/drone-overlay-comparison.md)。

历史中间轮次保留比较板、数值报告、相机和渲染清单；旧清单中的逐视角文件只在被当前细节报告引用时保留于仓库，其余重复大图保留本机归档。完整图组以当前 `iteration-87` / `stills-58`、各自渲染目录及 `baseline-raw-v23` 基线为准。`object-ids-v28`、`object-ids-v29a`、`object-ids-v29b` 、`object-ids-v29` 与当前 `object-ids-v53` 保留弧面边界诊断用像素证据。旧报告绑定历史模型，不代表当前交付模型。

[喷口出口源图拟合](nozzle-mouth-fit.json)与[保存 BRep 出口核对](nozzle-outline-check.json)只检查出口圆周；[粗回环定位](underbody-loop-fit.json)仍是图像推导。

[鳍片节距与包覆边界](cooling-fin-check.json)读取当前保存 BRep；周期、片数与布带褶皱仍属于外观推导。

[前罩边界拟合与读回](brow-outline-check.json)记录固定正面相机下的 25 个手工点；不证明整机全部轮廓达标。

[侧框源图反投影](side-frame-fit.json)、[保存轮廓检查](side-frame-check.json)与[局部前后对比](side-frame-detail.png)记录 v12；局部观测点拟合不代表整圈达标。

[侧控护板定位读回](cheek-position-check.json)、[护板前后对比](cheek-position-detail.png)与[v13 差异像素归属](object-ids-v13/contour-attribution.json)记录 v13；ID 颜色图仅用于定位检查对象，不参与主评分。

[回环完整弧线读回](loop-profile-check.json)、[回环前后对比](loop-profile-detail.png)及[v14 差异归属](object-ids-v14/contour-attribution.json)记录 v14；手工弧线拟合不代表全视角完整轮廓达标。

[小喷口四视角拟合](lower-pod-outline-fit.json)、[保存末端弧线及两个额外视角核对](lower-pod-outline-check.json)、[旧版读回](lower-pod-outline-check-v14.json)、[前后叠加细节](lower-pod-detail.png)与[v15 差异归属](object-ids-v15/contour-attribution.json)记录 v15。第 32 轮和第 15 组单图保留为 v14 历史证据。

[侧圆环四视角拟合](side-ring-fit.json)、[保存曲面外沿](side-ring-check.json)、[v15 对照](side-ring-check-v15.json)、[前后叠加细节](side-ring-detail.png)与[v16 差异归属](object-ids-v16/contour-attribution.json)记录 v16。

[喷口根环三视角拟合](nozzle-root-fit.json)、[保存中心线检查](nozzle-root-check.json)、[v16 对照](nozzle-root-check-v16.json)、[前后叠加细节](nozzle-root-detail.png)与[v17 差异归属](object-ids-v17/contour-attribution.json)记录 v17。

[提手侧视源点](handle-profile-fit.json)、[保存轮廓与对侧额外核对](handle-profile-check.json)、[v17 对照](handle-profile-check-v17.json)、[前后叠加细节](handle-profile-detail.png)与[v18 差异归属](object-ids-v18/contour-attribution.json)记录 v18。

[仪表三视角拟合](roof-instrument-fit.json)、[顶罩边界拟合](roof-crown-fit.json)、[保存几何核对](roof-instrument-check.json)、[v18 对照](roof-instrument-check-v18.json)、[前后叠加](roof-instrument-detail.png)与[v19 差异归属](object-ids-v19/contour-attribution.json)记录 v19。

[后部接口三视角拟合](rear-rail-fit.json)、[保存面板与灯头核对](rear-rail-check.json)、[v19 对照](rear-rail-check-v19.json)、[前后叠加](rear-panel-detail.png)及[v20 差异归属](object-ids-v20/contour-attribution.json)记录 v20。

[侧护框完整实体轮廓](side-frame-check.json)、[同方法 v20 对照](side-frame-check-v20.json)、[局部灯带宽度及接合](side-light-check.json)、[前后叠加](side-rounding-detail.png)和[v21 差异归属](object-ids-v21/contour-attribution.json)记录 v21。亮带宽度是局部诊断，不改变主轮廓分割方法。

[保存翼板轮廓与分层接合](wing-profile-check.json)、[v21 对照](wing-profile-check-v21.json)、[厚背层候选](wing-profile-check-v22b.json)、[前后叠加](wing-profile-detail.png)及[当前差异归属](object-ids-v27/contour-attribution.json)记录 v22 的翼板修订，当前文件已随 v23 保存模型重新读回。两个额外视角仅检查根部，不代表完整翼板已独立验收。

[正面控制条三视角拟合](front-control-fit.json)、[当前保存读回](front-control-check.json)、[v22 对照](front-control-check-v22.json)及[局部前后叠加](front-control-detail.png)记录 v23。位置误差来自同一组拟合点，不代表独立验收。

[去除英文渲染字样的基线复算](renderer-legend-removal-check.json)保留相同 v6 网格与相机；相机、光照和主分割阈值均未改变。

[旋钮端面边缘拟合](knob-outline-fit.json)、[保存端面读回](knob-outline-check.json)及[v23 对照](knob-outline-check-v23.json)取代旧中心取点作为当前旋钮轮廓依据。旧中心观测仍保留，未修改旧分数。

[状态板三视角拟合](side-status-fit.json)、[保存读回与视线检查](side-status-check.json)、[v23 对照](side-status-check-v23.json)及[局部叠加](side-status-detail.png)记录方框定位、对侧留出视角、实际凹座和背板。视线检查逐个求交遮挡件，避免重叠复合体线布尔运算的异常结果。

[侧上方圆口四视角拟合](side-socket-fit.json)、[当前保存读回](side-socket-check.json)、[v24 对照](side-socket-check-v24.json)和[前后叠加](side-socket-detail.png)记录 v25。36 个可见弧线点的距离 RMS 由 39.11 降至 2.85 像素；同点拟合和检查不是独立精度验收，外壁截面与口深仍为外观假设。

[侧环法兰近景判读](flange-detail-review.json)、[当前孔口与空腔读回](flange-detail-check.json)、[v25 对照](flange-detail-check-v25.json)及[前后叠加](flange-detail.png)记录 v26。两段曲面、错列通孔和凹入盆体均为真实几何；完整孔数、节距与隐藏结构仍是外观推定。

[红翼侧卷线拟合](side-cable-fit.json)、[当前保存中心线与端头](side-cable-check.json)、[v26 对照](side-cable-check-v26.json)和[前后叠加](side-cable-detail.png)记录 v27；额外第 120 帧中心线距离 RMS 由 8.33 降至 5.23 像素，隐藏引线和护套位置仍为推定。

[卷线扫掠修复记录](side-cable-sweep-review.json)保留第 57 轮追加检查失败及第 58 轮修复依据；当前保存卷线通过自相交检查。

[后框保存轮廓与接合](rear-rake-check.json)、[v27 对照](rear-rake-check-v27.json)、[局部叠加](rear-rake-detail.png)和[重建记录](rear-rake-rebuild-review.json)记录 v28。六块后框零件的保存实体均通过自相交检查；旧手工取点混有反光折线，其数值仅保留作历史诊断；v29 新可见下缘检查取代其外轮廓精度解释。

[后框弧面当前检查](rear-transition-check.json)、[同方法 v28 对照](rear-transition-check-v28.json)、[撤回的加深候选](rear-transition-check-v29b.json)及[局部叠加](rear-transition-detail.png)记录 v29。27 个可见下缘点的 RMS 从 11.22 降至 5.19 像素；弧面通过后结构框相接，邻近后盖的 0.296mm 分件间隙另行记录。

[2026-10-24 喷口外罩候选](nozzle-fairing-experiments/README.md)保留六个隔离试验、固定相机渲染和可见上缘点检查；F 已合入 v30，其余候选不代表当前模型。

[当前喷口可见上缘](nozzle-fairing-check.json)、[贴片表面与接合](nozzle-surface-check.json)、[前后叠加](nozzle-fairing-detail.png)和[当前差异归属](object-ids-v30/contour-attribution.json)记录 v30；局部抽样不代表整体外观达标。

[后壳凹舱检查](rear-cavity-check.json)、[未改动范围](rear-cavity-preservation.json)及[左后](rear-cavity-detail-left.png)、[正后](rear-cavity-detail-back.png)、[右后叠加](rear-cavity-detail-right.png)已更新至 v35。[五候选记录](rear-cavity-study/README.md)保留 v31 的凹舱选择过程；[v31 凹舱检查](rear-cavity-check-v31.json)与[范围检查](rear-cavity-preservation-v31.json)为历史证据。v31 上缘旧点距最大 27 像素，保留视觉失败，不将阴影直接解释为实体边界。

[肩部候选](nozzle-shoulder-study/README.md)、[两侧暴露外缘](nozzle-side-check.json)、[左后](nozzle-shoulder-detail-left.png)、[正后](nozzle-shoulder-detail-back.png)与[右后叠加](nozzle-shoulder-detail-right.png)图板更新至当前 v35；肩部修订发生于 v32；原 v31 上缘失败另见 [27px 历史报告](nozzle-fairing-check-v31.json)。

[v33 叶片候选](nozzle-petals-study/README.md)、[中央导轨节距](petal-pitch-check.json)、[左后](nozzle-petal-detail-left.png)、[正后](nozzle-petal-detail-back.png)与[右后叠加](nozzle-petal-detail-right.png)。v32 凹舱和保留范围历史报告见 [凹舱检查](rear-cavity-check-v32.json)及[范围检查](rear-cavity-preservation-v32.json)。


[v34 后肩七候选](rear-shoulders-study/README.md)、[后框重叠与浅槽检查](rear-seam-check.json)、[近景叠加](rear-seam-closeup.png)、[左后](rear-seam-detail-left.png)、[正后](rear-seam-detail-back.png)、[右后](rear-seam-detail-right.png)。仅后框及承接面两对象变化，其余 683 个可见对象保持；[v33 凹舱检查](rear-cavity-check-v33.json)及[保留范围](rear-cavity-preservation-v33.json)作为历史证据。


[v34 之后的凹舱比例与灯条五候选](cavity-proportion-study/README.md)保存十方位叠加、B/E 七张独立图复核和新增穿插诊断。B 的 12 处亮边位置 RMS 由 6.09 降至 1.40 像素；B/E 当时未直接合入，后续弯曲单灯条和反射背板采用为 v35。


[v35 灯条与反光候选](cavity-emitter-study/README.md)、[三视角主亮条拟合](cavity-emitter-study/primary-rail-fit.json)、[保存实体及接合](cavity-emitter-check.json)、[实际可见主亮条](cavity-rail-check.json)、[左后](cavity-lighting-detail-left.png)、[正后](cavity-lighting-detail-back.png)、[右后](cavity-lighting-detail-right.png)。v34 保留范围与后框检查见 [历史范围](rear-cavity-preservation-v34.json)、[凹舱](rear-cavity-check-v34.json)、[后框](rear-seam-check-v34.json)。

各 `iteration-N` / `stills-N` 目录保留对应轮次的固定相机证据；顶层 `*-detail-*.png` 随当前模型刷新，用于检查当前模型与历史基线的差异。需要当时结果时，以该轮次目录及候选目录为准。

[v42 翼板姿态交叉检查（未采用）](wing-pose-study/README.md)保存双侧观察点、真实 CAD 候选、十方位及七图结果。图 03 / 视频 7s 局部改善但整圈退步，正式模型保持；既有翼板高级 BOP 错误另有逐件记录。

## v46 出口形态后续试验

[固定相机的收口试验、保留的退步视角与焦距诊断](exit-profile-study/README.md)。正式模型仍为 v46；内收 4° 的独立试件尚未采用。


## v47 最新根部联动

v47 阶段正式模型中，根部、金色过渡壳、叶片及内衬共 126 对象同步，四支柱及出口圆保持。相同相机下保存全部十方位/七图叠加；整体轮廓基本持平。见[本轮记录与对比图](source-registration-study/README.md)。


## v48 最新内部凹腔

仅更新三个内部对象，外部喷口和四支柱保持。见[固定角度叠加、遮挡分析及保存探针](nozzle-interior-study/README.md)。


## v48 后框圆角试验（未采用）

[同角度十方位/七图比较](rear-rim-study/README.md)：R1.2 试件仅改变后结构框，增加了参考中不明显的接缝，未采用；正式模型仍为 v48。


## v49 外罩中段历史

[两侧形体、固定相机叠加与保存验证](fairing-blend-study/README.md)。本轮只改 11 件，两端、叶片、凹腔和支柱保持。

## v50 外罩深度历史

[固定角度叠加、试件取舍和保存检查](fairing-depth-v49-study/README.md)。采用 4mm 中段加深和两处灯角端部让位，保留 6mm 试件的上缘退步与相交记录。

## v51 当前外罩上肩

[四个试件与固定叠加](fairing-shoulder-study/README.md)。上沿误差下降，保留完整侧缘诊断及微小的整机分数退步；[连续视频阴影检查](upper-boundary-study/README.md)说明旧上沿测点的不确定性。


v52 历史：[三视角局部叠加与验证](nozzle-marking-study/README.md)，[十方位](iteration-86/comparison-board.png)，[七张原图](stills-57/comparison-board.png)。四支柱不变，凹舱阴影不作为筒壁。


[喷口内缘两组真实几何试验](petal-inner-edge-study/README.md)：倒角与内折边均未采用，保留完整同角度证据，该试验结束时正式模型保持 v52。

当前 v53：[三视角底部及侧后整体叠加](rear-belly-study/README.md)，[十方位](iteration-87/comparison-board.png)，[七张原图](stills-58/comparison-board.png)。四支柱不变，凹舱阴影不作为筒壁。

## v53 后续未采用试验

[后框内缘圆角](rear-frame-edge-study/README.md)与[转台灯光坐标系](orbit-lighting-study/README.md)：均保留全部固定角度证据，正式模型和灯光保持 v53；不是新几何版本，也不计作轮廓分数提升。

- [v53 喷口外罩下站试验](fairing-lower-v53-study/README.md)与[后盖外框宽度试验](rear-frame-width-v53-study/README.md)均未采用，正式模型仍为 v53。

当前 v53 的后续试件均未采用：下站收量与后框宽度见对应研究目录；对象归因报告只用于定位，不把暗部误判为喷口筒壁。
