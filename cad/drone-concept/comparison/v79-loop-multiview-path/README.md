# v79 底部回环多视角路径研究（未采用）

从 v69 的两件 `UnderbodyLoop0/1` 保存中心线出发，拟合有界的 X 外移／剪切、Y 偏移／展开和 Z 偏移／展开。两端坐标保持，半径仍为 2.2 mm；采用 40 个法向圆截面的平滑放样。仅这两件 BRep 改变，其余 696 件几何保持，包含四根支柱、实测平面屏、外挂筒、侧控件与格栅。屏幕仍为 210 × 160 × 2 mm、可视区 200 × 150 mm；曲面罩及隐藏结构为假设。

**未采用**。固定十视频平均 IoU 为 **85.502853%**，低于 v69 的 85.553320%；七静态为 **82.291857%**，略高于 v69 的 82.259620%。视频仅 2/10 方位改善，静态 4/7 改善；逐视角退步全部保留在 [review](candidate-review.json)。正背视回环从两条直线变为有宽度的弯环，但侧视仍不一致。不能由局部路径更像推断整体通过。

三帧四组人工中心线观察的拟合 RMS 为 6.945994 px；最终保存曲面经独立 1000×128 参数采样重测，为 **6.952350 px**。第 180、60 帧最大观察偏差分别为投影屏幕水平跨度的 **6.26%／5.56%**，仍超过 5%；第 120 帧两侧为 2.46%／4.06%。这些只是人工中心线观察，不是完整可见部件轮廓。全部帧已在历史研究查阅，没有新留出数据；暗色管线身份、厚度、镜像和变形模型均有不确定性。

初始未约束路径虽减小拟合残差，却使左回环与中央支撑座新增 12.607588 mm³ 相交，已拒绝。保留[旧拟合参数及来源哈希](rejected-unconstrained-fit.json)和[拒绝日志](rejected-unconstrained-build.txt)。新拟合将最内侧站点的 X 位移及沿 Y 剪切限制为非负；优化从边界内部起步，避免有界求解器在零边界提前停止。没有移动支撑或切掉回环以消除相交。

[最终保存检查](saved-loop-verification.json)：两件回环均为有效闭合单实体，无高级几何错误；与 13 件支撑相关零件共 26 组相交体积均为零。四个实际回环端部与腹板均有约 38.78 mm³ 正体积交叠。1082 个未改 BRep／映射归档成员、正式 v61 的 2095 个 GUI 成员逐字节保持。[独立读回](readback-verification.json)为 698 对象、696 可见对象、1008 有效闭合 STEP 实体，体积相对误差 3.66×10⁻⁷；两件变化网格逐顶点／逐面等于最终重开 FCStd。没有用端头探测球代替实际实体接合验收。

[原生四视角](native-display/native-board.png)已目视检查，696 件可见，颜色误差在半个 8 位色阶内；打开关闭后 FCStd 哈希不变。[三视角共同裁切](loop-closeup.png)采用相同矩形，所有比较保留原固定相机，无非刚性变形或逐部件配准。只有既定新增支撑区域从 IoU 渲染中排除，整体预览和原生视图显示支撑。静态第六图为线框，分数不等于实体轮廓精度。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建记录](candidate-check.json) · [拟合](path-fit.json)
- [十视频叠加／差异](video-comparison/comparison-board.png) · [七静态叠加／差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

复现时设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`，使用 FreeCAD Python，在仓库根目录执行；构建和打包输出必须为空目录：

```sh
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/fit_drone_loop_multiview.py --output /tmp/vintrox-v79-fit.json
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/experiment_drone_loop_path.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --fit /tmp/vintrox-v79-fit.json --output /tmp/vintrox-v79-diagnostic
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/finalize_drone_petal_axial.py --diagnostic /tmp/vintrox-v79-diagnostic --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --output /tmp/vintrox-v79-package
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/measure_drone_saved_loop_path.py --model cad/drone-concept/comparison/v79-loop-multiview-path/candidate.FCStd --baseline cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --appearance-source cad/drone-concept/vintrox-drone-concept.FCStd --fit cad/drone-concept/comparison/v79-loop-multiview-path/path-fit.json --cameras cad/drone-concept/comparison/v69-underbody-loop-radius2p2/video-comparison/cameras.json --output /tmp/vintrox-v79-check.json
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/review_drone_loop_path.py --candidate cad/drone-concept/comparison/v79-loop-multiview-path --baseline cad/drone-concept/comparison/v69-underbody-loop-radius2p2
```

彩色 CPU 渲染及叠加使用 `tools/render_drone_concept.py`、`tools/compare_drone_reference.py` 和 v69 的 `video-comparison/cameras.json`、`stills-comparison/cameras.json`；导出读回使用 `tools/readback_drone_loop_radius_candidate.py`，参数为 `--expected-step-solids 1008 --verify-mesh-objects UnderbodyLoop0 UnderbodyLoop1`。原生颜色检查使用 `tools/verify_drone_native_display.FCMacro`，输出清单绑定最终模型、网格和宏哈希。

正式 v61 与研究优选 v69 保持。下一步需联合核对回环厚度、近根段转折和遮挡，避免继续依赖单视角中心线或全局线性剪切。90% IoU／完整主要部件 5% 目标未完成；未作制造、打印、装配、承力、电气或实物验收。
