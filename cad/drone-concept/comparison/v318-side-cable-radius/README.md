# v318 侧外挂筒线束线径

从 v315 保存模型出发，将红翼侧外挂筒的单一装饰线束圆截面半径由 1.8 mm 改为 1.5 mm。线束中心线、两个端部护套和支撑区域保持。候选为有效闭合实体，护套交叠和支撑碰撞检查无退步。[保存几何](candidate-check.json)

| 固定相机 | v315 | v318 |
| --- | ---: | ---: |
| 视频十方位 | 86.204590% | 86.210766% |
| 静态七图 | 82.687714% | 82.700248% |
| 拼图十格 | 89.958234% | 89.957320% |

视频与拼图均未提高，静态均值小幅提高，正式模型继续采用 v315。侧线束内部中心线仍是外观推定，候选未替换正式 FCStd、STEP 或预览。[视频](video-board.png) · [静态图](stills-board.png) · [拼图](sheet-board.png)

使用 `tools/experiment_drone_side_cable_radius.py --radius 1.5` 从 v315 保存模型重放。再运行 `tools/finalize_drone_petal_axial.py` 恢复显示数据并沿 v315 固定相机渲染。[v315 输入](../v315-antenna-multiview/README.md)
