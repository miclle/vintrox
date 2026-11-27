# v151 提手支臂内倾

以保存的 v140 为基线，将左右提手支臂、内嵌面、端箍和标记各向内转 1.5°，从相同转轴累计内倾 4°。十四项接合检查通过。支臂与侧壳的搭接体积从约 39.35 增至 48.20 mm³，支臂和端箍与握把的间隙为 0 mm。独立读回确认 12 件变更网格、853 个闭合 STEP 实体和四支柱几何。原生四视角确认 696 个可见对象及 70 组显示颜色。[几何与接合](candidate-check.json) · [保存读回](readback-verification.json) · [原生显示](native-display/native-display-verification.json)

| 模型 | 视频十方位 IoU | 静态七图 IoU | 拼图十格 IoU |
| --- | ---: | ---: | ---: |
| v140 | 85.854104% | 82.472554% | 89.593124% |
| v151 | 85.865014% | 82.483732% | 89.610957% |

第 120 帧正后视 IoU 提高 0.14489 个百分点，静态图 03 下降 0.12792 个百分点。两组侧视支臂样点的 RMS 从 3.05、1.77 px 升至 3.62、2.20 px。v151 依据三组整机均值和正后视改善成为正式外观版本。整圈 90% 和主要部件完整轮廓偏差 5% 仍待达成。[v140 侧视样点](baseline-handle-profile.json) · [v151 侧视样点](handle-profile.json)

复建时将 v140 保存模型及解压网格传给 `tools/experiment_drone_handle_tilt.py`，使用 `--angle 1.5`，随后运行 `tools/finalize_drone_petal_axial.py` 恢复原生显示并由最终保存模型导出 STEP。重放时使用本目录三组固定相机。实测平面屏随完整模型渲染，曲面罩和参考中不可见的结构属于外观推定。[v140 基线](../v140-shoulder-petal-pod/README.md) · [网格清单](mesh-archive.json)

v154 接替 v151 后，v151 的 FCStd、STEP 和压缩网格已移出本地 `main` 历史。可按上述参数复建，或使用本机恢复包与 LFS 缓存取回原件。[清理与恢复记录](../../../../docs/storage-cleanup.md) · [v154 当前模型](../v154-handle-petal-combination/README.md)

- [视频十方位](video-comparison/comparison-board.png)
- [静态七图](stills-comparison/comparison-board.png)
- [拼图十格](sheet-comparison/comparison-board.png)
