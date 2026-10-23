# Drone 参考比较证据

当前模型：v30 喷口外罩与贴合标记修订；按用户要求完成当前子任务后暂停。模型哈希以各报告为准；它们是图像空间诊断，不是加工验收。

- [当前十方位比较板](iteration-64/comparison-board.png)、[报告](iteration-64/comparison-report.json)、[CAD 原始渲染](iteration-64-renders/render-manifest.json)。
- [七张独立图片比较板](stills-35/comparison-board.png)、[报告](stills-35/comparison-report.json)、[原始渲染](stills-35-renders/render-manifest.json)。06 是线框图，不计入十方位轮廓目标。
- [相同渲染设置下的 v6 基线](baseline-raw-v23/comparison-board.png)及[报告](baseline-raw-v23/comparison-report.json)。
- [42 个稀疏标志点](landmark-check.json)检查翼尖、翼根、灯头与实际平面显示区的位置，不证明完整轮廓通过。
- [全部参考输入索引](review-index.json)覆盖六张编号图、补充近景、十视角拼图和原始旋转视频。
- [方法、相机假设、迭代及复现](../../../docs/drone-overlay-comparison.md)。

历史中间轮次保留比较板、数值报告、相机和渲染清单；旧清单中的逐视角文件只在被当前细节报告引用时保留于仓库，其余重复大图保留本机归档。完整图组以当前 `iteration-64` / `stills-35`、各自渲染目录及 `baseline-raw-v23` 基线为准。`object-ids-v28`、`object-ids-v29a`、`object-ids-v29b` 、`object-ids-v29` 与当前 `object-ids-v30` 保留弧面边界诊断用像素证据。旧报告绑定历史模型，不代表当前交付模型。

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
