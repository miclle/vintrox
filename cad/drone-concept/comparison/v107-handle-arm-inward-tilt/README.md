# v107 提手支臂内倾

以保存 v106 为基线，两侧提手支臂、内嵌面、端箍和标记共 12 件随各自转轴向内旋转 2.5°。握把芯和包覆带保留，实测平面屏、四根支柱、外挂筒、侧控件和格栅均保留。[几何参数与接合数据](candidate-check.json)

| 固定相机轮廓 IoU | v106 | v107 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位平均 | 85.5948200% | 85.7083020% | +0.1134820 |
| 静态七图平均 | 82.3655109% | 82.4451438% | +0.0796329 |
| 视频 04 正后视 | 82.8201% | 83.4199% | +0.5999 |

正后视五条扫描线的十个外缘点，水平偏差 RMS 从 9.93 降至 2.65 px，最大值从 11 降至 4 px，占该视角投影屏宽的 1.08%。两侧已有轮廓样点中，右侧最大偏差从 4.35 升至 6.08 px，左侧从 3.89 降至 3.12 px，两侧 RMS 均回升。静态图 03 的 IoU 下降约 0.151 个百分点。采用 v107 是基于后视宽度改善及两组整机均值提升。[正后视叠加](handle-rear-observations.png) · [正后视样点](handle-rear-observations.json) · [侧视测量](handle-profile-check.json) · [逐视角结果](candidate-review.json)

14 项接合检查通过。支臂与侧壳的交叠体积从约 42.3 降至 39.35 mm³，支臂及端箍与握把的间隙仍为零。两件支臂已有的高级曲线检查错误数量和类别保持，其他变更件未出现新增错误。最终 FCStd 读回确认 696 个可见对象、852 个有效闭合 STEP 实体，12 件变化网格与保存实体重新三角化结果一致。原生 FreeCAD 四视图颜色和可见性检查通过，重新关闭后文件哈希一致。[读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

视频与静态图沿用 v106 的相机和分割方式，保留全部视角结果。参考比较排除四根新增支柱及附属件，曲面罩是围绕实测平面屏的外观假设。正后视点组仅覆盖提手上端，主要部件完整轮廓 5% 和整圈 90% 目标仍待达成。[视频十方位叠加](video-comparison/comparison-board.png) · [静态七图叠加](stills-comparison/comparison-board.png)

从仓库根目录解压归档网格后重放。静态图使用 `stills-comparison/cameras.json` 和单独的输出目录。[网格清单](mesh-archive.json)

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v107-handle-arm-inward-tilt
VINTROX_REPLAY=$(mktemp -d)
gzip -dc "$VINTROX_PACKAGE/meshes.json.gz" > "$VINTROX_REPLAY/meshes.json"
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
  --model "$VINTROX_PACKAGE/candidate.FCStd" --output "$VINTROX_REPLAY/video-renders" \
  --comparison "$VINTROX_PACKAGE/video-comparison/cameras.json"
/Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
  --renders "$VINTROX_REPLAY/video-renders" --output "$VINTROX_REPLAY/video-comparison" \
  --cameras "$VINTROX_PACKAGE/video-comparison/cameras.json"
```

几何复建使用 `tools/experiment_drone_handle_tilt.py`，传入保存 v106 的 FCStd、解压网格与 `--angle 2.5`。用 `tools/finalize_drone_petal_axial.py` 恢复保存的颜色、可见性数据，并从最终文件导出 STEP。用 `tools/measure_drone_handle_profile.py` 复算两组侧视样点。
