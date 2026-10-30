# v63 屏幕外框候选

本目录是 VINTROX Drone 外观研究 v63 的未采用候选。它从正式 v61 FCStd 复制出独立模型，只修改真实 CAD 的 `ScreenBezel` 与 `BezelLip`，保留实测平面屏、可视区、四根支柱、外挂筒、屏幕侧控件和格栅。

## 可复现入口

```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import sys; sys.argv=['tools/experiment_drone_v63_screen_bezel.py','--base','cad/drone-concept/vintrox-drone-concept.FCStd','--output','cad/drone-concept/comparison/v63-screen-bezel-study-3']; exec(compile(open('tools/experiment_drone_v63_screen_bezel.py').read(),'tools/experiment_drone_v63_screen_bezel.py','exec'))"
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd -c "import sys; sys.argv=['tools/readback_drone_v63_screen_bezel.py','--model','cad/drone-concept/comparison/v63-screen-bezel-study-3/candidate.FCStd','--output','cad/drone-concept/comparison/v63-screen-bezel-study-3','--base-hash','0c5a5e32c69519f8985493906ddc6b5d3f79ffa30cd8463e2604a433de831840']; exec(compile(open('tools/readback_drone_v63_screen_bezel.py').read(),'tools/readback_drone_v63_screen_bezel.py','exec'))"
```

`meshes.json` 绑定候选 FCStd SHA-256，Blender 使用其真实 CAD 网格渲染。`video-comparison/` 使用固定的十方位 `cameras.json`，`still-comparison/` 使用七张静态参考图的校准相机；两者都保存原始渲染、50% 叠加、边缘轮廓和差异图。流程只做相机投影，不做图像变形、拉伸、逐部件对齐或部件忽略。

## 结果

- 视频十方位平均 IoU：`0.8545203738`；v61：`0.8549201687`，下降 `0.0003997950`。
- 静态七图平均 IoU：`0.8223130556`；v61：`0.8222681557`，上升 `0.0000448998`。
- 因视频整圈退步，候选保留为研究证据，不替换正式 v61。
- [`candidate-check.json`](candidate-check.json) 记录 FCStd 保存读回、保护支柱和屏幕保持；[`step-readback.json`](step-readback.json) 记录独立 STEP 导入的 1008 个闭合实体。

这些是可见轮廓诊断，不是曲面屏光学、制造、装配、热、电气或实物验收。参考中的曲面屏仍以透明外观假设表示，真实输入仍是平面屏对象。
