# v80 局部回环路径研究（未采用）

仅修改 v69 的 `UnderbodyLoop0/1`，端头坐标保持，使用 27 个独立站点坐标拟合此前的第 60／120／180 帧四组人工中心线观察。以固定原弦长参数插值，40 个法向圆截面平滑放样，半径 2.2 mm。两件变化之外的 696 件几何保持，包括四支柱、实测平面屏、外挂筒、侧控件和格栅。真实屏幕为 210 × 160 × 2 mm、可视区 200 × 150 mm；曲面罩及隐藏结构仍是假设。

**四组中心线采样虽低于 5%，仍出现不自然折弯，且视频／静态平均 IoU 均退步；未采用。** 固定十视频／七静态平均 IoU 为 **85.477261%／82.205545%**，v69 为 85.553320%／82.259620%。逐视角结果与退步保留在 [review](candidate-review.json)。没有移动相机、变形图像或删除可见部件；仅沿用原有新增支撑排除规则，预览和原生视图显示四支柱。

未约束 SciPy 预筛的低误差方案出现回折，FreeCAD 放样失败；最终改用 OCCT 真实插值基函数并加强位移及二阶差分约束。失败参数与日志保留。

独立最终保存曲面经 1000×128 参数采样，人工观察到中心线的 RMS 为 **4.146482 px**。按第 180 帧右侧、第 60 帧左侧、第 120 帧右侧／左侧顺序，最大偏差为投影屏幕水平跨度的 **4.56%／3.52%／0.97%／1.60%**。这些点与拟合相同，暗色管线身份与中心估计存在不确定性，非新留出证据；中心线采样不是完整可见部件轮廓验收。固定参数下 OCCT 插值是站点坐标的线性映射，单位站点基函数与实际 CAD 插值误差小于 10⁻⁹ mm，见 [拟合](path-fit.json)。

[最终保存验证](saved-loop-verification.json)确认两件回环有效闭合、单实体且无高级几何错误；与 13 件支撑相关零件共 26 组相交均为零，四个实际回环端部与腹板有正体积交叠。1082 个未改 BRep／映射成员和正式 v61 的 2095 个 GUI 成员逐字节相等。[独立 FCStd／STEP 读回](readback-verification.json)为 698 对象、696 可见对象、1008 个有效闭合 STEP 实体，体积相对误差约 3.7×10⁻⁷；两件变化网格逐顶点／逐面等于最终重开 FCStd。未验证制造连接、承力、电气或实物可行性。

[原生四视角](native-display/native-board.png)已目视检查，696 件可见，色差在半个 8 位色阶内，打开关闭后文件哈希不变。画面中的折弯／截面外观局限保留，未通过隐藏零件或单独调整显示来修饰结果。[共同裁切](loop-closeup.png)与完整比较均采用同一固定相机；静态第六图为线框，其前景分数不等于实体轮廓精度。

- [FCStd](candidate.FCStd) · [STEP](candidate.step) · [构建记录](candidate-check.json) · [全部对比数据](candidate-review.json)
- [十视频叠加与差异](video-comparison/comparison-board.png) · [七静态叠加与差异](stills-comparison/comparison-board.png)
- [整体预览](previews/hero.png) · [正面](previews/front.png) · [背面](previews/rear.png)

复现：使用带 FreeCAD、NumPy、SciPy、Pillow 的 FreeCAD Python，设置 `PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib`。在仓库根目录运行 `tools/fit_drone_local_loop_path.py --output /tmp/v80-fit.json`；再运行 `tools/experiment_drone_loop_path.py --base cad/drone-concept/comparison/v69-underbody-loop-radius2p2/candidate.FCStd --mesh cad/drone-concept/comparison/v69-underbody-loop-radius2p2/meshes.json --fit /tmp/v80-fit.json --radius 2.2 --output /tmp/v80-diagnostic`，输出必须为空目录。通过后使用 `tools/finalize_drone_petal_axial.py` 恢复正式 GUI 成员并导出 STEP，其输入基线同上、外观源为 `cad/drone-concept/vintrox-drone-concept.FCStd`。

完整渲染使用 `tools/render_drone_concept.py` 和 v69 的 `video-comparison/cameras.json`／`stills-comparison/cameras.json`；比较使用 `tools/compare_drone_reference.py`。保存检查使用 `tools/measure_drone_saved_loop_path.py`，导出读回使用 `tools/readback_drone_loop_radius_candidate.py --expected-step-solids 1008 --verify-mesh-objects UnderbodyLoop0 UnderbodyLoop1`，原生检查使用 `tools/verify_drone_native_display.FCMacro`；裁切与 review 使用 `tools/review_drone_loop_path.py --candidate cad/drone-concept/comparison/v80-local-loop-path --baseline cad/drone-concept/comparison/v69-underbody-loop-radius2p2 --label v80`。

正式 v61 与研究优选 v69 保持。后续需按真实可见内外边界核对截面形状与遮挡，中心线和圆截面半径不足以唯一恢复参考。90% IoU／完整主要部件 5% 目标未完成；未作制造、打印、装配、光学或实物验收。
