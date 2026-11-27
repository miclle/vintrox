# v293 底壳与线束遮挡核对

用 v292 保存 CAD 的三角网格，在静态图 04、05、06 和视频第 60、90、180 帧核对底壳、两根黑色回环和多芯线束。对照板从左到右显示参考、真实 CAD 渲染和对象归因。红色为底壳，青色为回环，黄色为多芯线束。六张图的 IoU 均与 v292 报告一致。[六视角对照](underside-views.png) · [逐视角数据和输入哈希](underside-views.json)

静态图 05 在填洞后的参考遮罩外有 11,002 个像素归属于底壳，静态图 04 有 7,111 个，线框图 06 有 347 个。图 05 的红色归因覆盖暗底面、线束和线束之间的间隙。线框图 06 显示线束根部的板件和线束后方的底部结构。底壳在视频第 60 帧只露出 3 个可归因像素，在第 90 帧露出 2,342 个。不同视角的遮挡使这些计数难以直接换算成底壳的切削量。

黑色回环在多个视频视角显得比参考细。v277 单独加粗时，四组局部采样 RMS 下降，视频十方位平均 IoU 也下降。v278 联动改变路径和半径后，第 180 帧右侧回环的最大采样偏差升到投影屏宽的 25.75%。下一轮以可见弧段和根部为依据，联合筛选路径与粗细，并用第 180 帧核对遮挡。当前交付版为 v292。[半径筛选](../v277-loop-radius-screen/README.md) · [路径筛选](../v278-loop-path-fit/README.md)

## 复现

从 v292 保存 FCStd 重建网格，使用 `tools/render_drone_object_ids.py` 和 v292 视频、静态两组 `cameras.json` 分别生成对象 ID。将 v292 对照目录和对象 ID 目录传给本目录的脚本。静态图缩放沿用 v292 的校准相机分辨率，逐图复核原分割规则下的 IoU。[网格和相机](../v292-brow-shoulder-inset/README.md) · [渲染流程](../../../../docs/drone-concept.md#编辑与复现)

```bash
python3 cad/drone-concept/comparison/v293-underbody-visibility/inspect_belly.py \
  --baseline cad/drone-concept/comparison/v292-brow-shoulder-inset \
  --still-ids "$drone_still_ids" --video-ids "$drone_video_ids" \
  --output "$drone_diagnostic_dir"
```
