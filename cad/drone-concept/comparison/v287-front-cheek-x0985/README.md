# v287 前侧脸颊与桥板收形

基于 v276 的保存模型，以机身中心平面为基准，将左右前侧脸颊和桥板沿横向缩至 98.5%。实测 210 × 160 × 2 mm 平面屏、外挂筒、屏幕侧控件、格栅和四根支柱均保留。[候选几何](candidate-check.json)

| 固定相机 | v276 | v287 | 变化（百分点） |
| --- | ---: | ---: | ---: |
| 视频十方位 | 86.019486% | 86.033198% | +0.013712 |
| 静态七图 | 82.574760% | 82.574760% | 0 |
| 拼图十格 | 89.777430% | 89.782809% | +0.005379 |

正面视频 `video-09` 提高 0.13391 个百分点。`video-05`、`sheet-02`、`sheet-10` 分别下降 0.00313、0.00119、0.01178 个百分点。采用 v287 作为外观评审版本。视频整圈 90% 和主要部件轮廓偏差 5% 的目标仍待达成。[十方位视频](video-comparison/comparison-board.png) · [静态七图](stills-comparison/comparison-board.png) · [拼图十格](sheet-comparison/comparison-board.png)

四件修改形体通过高级几何检查。桥板与侧脊间隙均为 0 mm，脸颊与桥板的搭接约为 3,909 mm³。STEP 独立读回为 853 个有效闭合实体。FreeCAD 原生四视图核对 696 个可见对象和 70 组颜色。曲面罩及参考中不可见的细节仍按外观推定。[独立读回](independent-readback.json) · [原生颜色](native-display/native-display-verification.json) · [交付校验](../../delivery-verification-current.json)

以 v276 保存模型和重建网格运行 `tools/experiment_drone_front_cheek_contract.py --scale .985 --revision v287-front-cheek-x0985`。`--base` 和 `--appearance-source` 都使用 v276 的保存文件。从 v287 保存模型重建的网格与渲染网格逐字节一致。[v276 基线](../v276-front-cheek-x099/README.md) · [网格记录](mesh-archive.json) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)
