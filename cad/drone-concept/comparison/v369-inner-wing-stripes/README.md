# v369 红翼内侧斜纹

参考视频第 150 帧可见红翼内侧一宽一窄的斜纹，第 180 帧从另一方位仍可看到。v363 只在翼外侧有斜纹。v369 从第 150 帧的冻结相机反投影条带，在内翼面、凸脊顶面和侧面裁切实体，每条纹增加 8 个闭合薄实体，沿用既有色条对象和颜色。0.18 mm 是涂层的建模厚度。

第 150 帧两条纹跨过凸脊，主条纹在翼上缘的起点略高于参考。第 180 帧未参与定位，导线遮挡后仍可看见两条纹，但主条纹在凸脊附近有突角，模型条纹也明显亮于参考。保留为局部研究成果。参考灯光、表面磨损和精确涂层颜色仍未知。[两帧同区域对照](wing-comparison.jpg)

| 固定相机组 | v363 平均 IoU | v369 平均 IoU |
| --- | ---: | ---: |
| 视频十方位 | 86.24385% | 86.24539% |
| 静态七图 | 82.71757% | 82.71694% |
| 拼图十格 | 89.98254% | 89.98364% |

沿用原相机、支柱排除区域和整机比较流程。第 150 帧整机 IoU 为 82.08%，仍是视频十方位中最低的一帧。[视频叠加](video-overlays.jpg) · [静态叠加](stills-overlays.jpg) · [拼图叠加](sheet-overlays.jpg)

使用 FreeCAD 1.1.4 的 Python 环境，按 [v363 说明](../v363-lowerpod-chassis-combo0995/README.md) 恢复基线后运行以下命令。

```sh
python cad/drone-concept/comparison/v369-inner-wing-stripes/build.py "$research_dir/candidate.FCStd" "$research_dir/v369.FCStd"
```

修订版保存后重新打开，696 个可见对象、70 种颜色和网格对应，四个原生视角已保存。原生打开时记录到的元素映射警告为零。FCStd 与 STEP 各有 869 个有效闭合实体，体积相对误差为 5.20 × 10⁻⁷。[独立读回](independent.json) · [原生四视角及色值核对](native/native-display-verification.json)
