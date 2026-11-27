# v148 大喷口内盆后移

从保存的 v140 出发，将低音锥盆与防尘帽沿喷口轴向内移 4 mm。内喉管仍与锥盆相接，计算搭接为 30.03 mm³，锥盆与外罩和后背板之间未发现体积交叠。预检中的 8 mm 方案与内喉管产生约 0.048 mm 间隙。[接合预检](bowl-contact-screen.json) · [构建与接合](candidate-check.json)

后移让第 120 帧的一个标注点首先击中叶片。两张静态图仍有五个采样点先击中锥盆，第 60、180 帧落在整机投影之外的十个标注点仍落在投影之外。两张静态图的局部 RMS 略降，第 150 帧从 7.68 升至 9.04 px。27 个固定视角的整机轮廓分数与 v140 相同，正式模型采用 v140。内盆与防尘帽为外观示意，实际低音部件仍待选型。[视线求交](petal-occlusion.json) · [逐点距离](visible-petal-edges.json) · [局部对照](visible-petal-edges.png)

独立读回确认两件变更网格与保存实体逐顶点、逐面一致，四支柱几何一致，853 个 STEP 实体有效闭合。FreeCAD 原生四视角确认 696 个可见对象和 70 组显示颜色。[保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

使用 FreeCAD Python 运行本目录的 `recess-bowl.py`，以 v140 的 FCStd 和解压网格作为 `--model` 和 `--meshes`，传入 `--depth-mm 4` 并指定新的 `--output` 目录。脚本从仓库的 `tools` 导入试验检查函数。再用 `tools/finalize_drone_petal_axial.py` 恢复 v140 的原生显示并导出 STEP，沿用 v140 的固定相机重放。[v140 输入及重放流程](../v140-shoulder-petal-pod/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
