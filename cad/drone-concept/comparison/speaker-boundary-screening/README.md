# Speaker boundary screening v199–v203

根据 v193 区域归因中的 `SpeakerOuterLip`、`SpeakerVisualCone`、`SpeakerHubNeck` 差异，分别对真实 CAD 的音箱对象做小幅解析重建。候选保持实测平面屏、外挂筒、屏幕侧控件、格栅和四根支柱。

| 候选 | 改动 | 视频十方位 IoU | 相对 v193 |
| --- | --- | ---: | ---: |
| v201 | 外口压圈、细压边径向 0.5% 收缩 | 85.909973% | −0.000079 个百分点 |
| v202 | 外口压圈、细压边径向 0.5% 外扩 | 85.909437% | −0.000616 个百分点 |
| v203 | 锥盆、悬边径向 0.5% 收缩 | 85.909696% | −0.000356 个百分点 |

三项均低于 v193，正式模型保持 v193。每项保存 FCStd、STEP、十方位渲染、半透明叠加、边缘和差异图。网格不随仓库保存，复现时使用 `tools/export_saved_drone_meshes.py` 从候选 FCStd 临时重建，不依赖 Git LFS。

- [筛选记录](screening.json)
- [v201](v201/video-comparison/comparison-board.png)
- [v202](v202/video-comparison/comparison-board.png)
- [v203](v203/video-comparison/comparison-board.png)

这些结果只用于外观轮廓筛选，不能证明整圈 90% IoU、主要部件 5% 偏差、制造、装配或实物验收已完成。
