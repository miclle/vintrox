# v97 喷口叶片与前眉外观记录

当前保存外观模型为 v97，生成脚本记录前眉横向比例 0.985、喷口叶片局部切向追加比例 0.960，以及沿用的前侧护壳比例 0.970。保存文件与生成脚本的完整几何等价性未在本轮验证。

使用 v96 的固定相机，视频十方位平均轮廓 IoU 为 **0.855731710**，相对 v96 **-0.008616 个百分点**；静态七图平均为 **0.823587197**，相对 v96 **+0.062521 个百分点**。逐视角升降保存在 `candidate-review.json`；视频均值退步，不能宣称整圈改善或达到 90% 目标。

FCStd SHA-256：`2ab40ea74dacd2be487e8c3f77ff540b63110daff9c506f79cf332c8e016412a`；STEP：`739c3c02b13c532d3b72fc7b29701558b458b77e37410d2f75e078020c72d178`。独立保存读回通过：696 个可见对象、852 个 STEP 实体，实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm 和四根支柱检查通过。相对 v96 的 1008 个 STEP 实体，实体数量已变化；此处不将静态有效性解释为生成器完全等价、制造或装配通过。

无 GUI 导出网格最初退化为单色；当前 FCStd 与 v96 保存 GUI 外观载荷已逐对象核对一致，按稳定对象名恢复 74 个 RGB 三元组，并逐对象核对顶点和面未改变，见 `palette-restoration.json`。彩色渲染、对象 ID、轮廓归因和差异图已重新生成，全部绑定当前 FCStd；仅比较时排除新增支柱前缀，不改变正式 CAD。

复现固定相机渲染与比较（从仓库根目录执行）：

```sh
PACKAGE=cad/drone-concept/comparison/v97-petal096-brow0985-on-v96
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$PACKAGE/meshes.json" \
  --model "$PACKAGE/candidate.FCStd" --output /tmp/vintrox-v97-replay/video-renders \
  --comparison "$PACKAGE/video-comparison/cameras.json"
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
  --renders /tmp/vintrox-v97-replay/video-renders --output /tmp/vintrox-v97-replay/video-comparison \
  --cameras "$PACKAGE/video-comparison/cameras.json"
```

静态七图使用 `stills-comparison/cameras.json` 同法重放。2026-11-05 已从当前保存 v97 网格刷新[九视角预览与转台](../../renders/render-manifest.json)，12 秒视频含 96 个不同角度；[原生 FreeCAD 四视图审计](native-display/native-display-verification.json)确认颜色／可见性及关闭后哈希保持，截图已目视检查。历史全套交付审计未刷新。以上仅为静态外观研究，不代表打印、装配、光学、声学、热、电气或实物验收。
