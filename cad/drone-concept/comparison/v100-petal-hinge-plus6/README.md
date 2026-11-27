# v100 大喷口叶片开合角度研究

从保存 v97 出发，绕各铰座的体积加权中心旋转 12 组叶片及其附件，正负试验各涉及 108 件形体。旋转轴为喷口局部切向。正 6° 通过 132 项接合距离检查，无新增高级几何错误。负 6° 有 20 项接合距离退步，止于几何诊断阶段。实测平面屏 210 × 160 × 2 mm、可视区 200 × 150 mm、四支柱、外挂筒、侧控件和格栅均保留。[正角度检查](candidate-check.json) · [负角度诊断](negative-angle-diagnostic.json)

| 固定相机对比 | v97 | 正 6° | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位平均 IoU | 85.5731710% | 85.5759611% | +0.0027900 |
| 静态七图平均 IoU | 82.3587197% | 82.3491130% | −0.0096066 |

视频收益很小，静态平均退步，正 6° 保留为未采用候选。七个已标注视角的叶片可见边界采样 RMS 均下降，但候选的两个近侧视角最大误差仍达投影屏宽的 21.09% 和 20.89%。采样覆盖部分末端，家族边界也包含遮挡边缘，完整主要部件 5% 目标仍待验证。参考曲面屏与实测平面屏的差异及隐藏几何仍有限制。[逐视角结果](candidate-review.json) · [可见边界对照](visible-petal-edges.png) · [采样数据](visible-petal-edges.json)

最终保存模型保留 696 个可见对象，独立读回确认 852 个有效闭合 STEP 实体、108 件变更网格一致、保护支撑一致。原生 FreeCAD 四视图通过目视检查，可见性与网格一致，颜色最大通道差为 0.001960814，关闭后模型哈希一致。验证范围为静态外观，制造和实物验收仍待进行。[FCStd](candidate.FCStd) · [STEP](candidate.step) · [读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

视频和静态图沿用 v97 的相机、分割和四支柱比较排除规则。渲染来自真实 CAD 网格，叠加按同一相机投影计算。[十方位叠加](video-comparison/comparison-board.png) · [七图叠加](stills-comparison/comparison-board.png) · [视频轮廓归因](video-ids/boundary-regions-board.png)

从仓库根目录解压归档网格并重放。原始网格字节和压缩件哈希见[网格清单](mesh-archive.json)。

```sh
VINTROX_PACKAGE=cad/drone-concept/comparison/v100-petal-hinge-plus6
VINTROX_REPLAY=$(mktemp -d)
gzip -dc "$VINTROX_PACKAGE/meshes.json.gz" > "$VINTROX_REPLAY/meshes.json"
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python tools/render_drone_concept.py -- --meshes "$VINTROX_REPLAY/meshes.json" \
  --model "$VINTROX_PACKAGE/candidate.FCStd" --output "$VINTROX_REPLAY/video-renders" \
  --comparison "$VINTROX_PACKAGE/video-comparison/cameras.json"
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib:$PWD/tools \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/compare_drone_reference.py \
  --renders "$VINTROX_REPLAY/video-renders" --output "$VINTROX_REPLAY/video-comparison" \
  --cameras "$VINTROX_PACKAGE/video-comparison/cameras.json"
```

静态图使用 `stills-comparison/cameras.json` 和单独的输出目录。复建几何使用 `tools/experiment_drone_petal_hinge_angle.py`，指定 v97 FCStd 和同包 `meshes.json`、独立输出目录与 `--angle 6`，再用 `tools/finalize_drone_petal_axial.py` 从最终保存模型重新导出 STEP。
