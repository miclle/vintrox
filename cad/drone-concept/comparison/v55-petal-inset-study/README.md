# v55 喷口叶片凹槽窗口研究

本轮只调整 12 件 `NozzlePetalInset` 的可见角度窗口，从上一轮的较宽窗口收窄为 **4.4°–18.1°**。主叶片、喷口外罩、后壳、凹舱阴影和四根支柱保持。暗色边缘继续解释为凹舱遮挡与光照，不据此生成连续筒状喷口壁。

- 当前 FCStd：`e64613e11be81eb528a9d0863266a8ade031bf306e40eb9865d28601d57998eb`
- 当前 STEP：`4ec4e4a1f5d3262fcc2a2d435e0f5b4e3d9addb30f4ed67fd920837543eb4583`
- 视频十方位平均轮廓 IoU：`85.1341303491%`
- 七张静态图平均轮廓 IoU：`82.0448342009%`
- 对象归属清单：[`../object-ids-v56/object-id-manifest.json`](../object-ids-v56/object-id-manifest.json)
- 差异归属结果：[`../object-ids-v56/contour-attribution.json`](../object-ids-v56/contour-attribution.json)
- 视频叠加：[`../iteration-90/comparison-board.png`](../iteration-90/comparison-board.png)
- 静态叠加：[`../stills-61/comparison-board.png`](../stills-61/comparison-board.png)
- 交付绑定：[`../delivery-verification-v55-petal-inset-window.json`](../delivery-verification-v55-petal-inset-window.json)

v55 的整圈数值与 v54 基本持平，因此这是一轮局部细节修订，不包装成整体轮廓提升。完整的固定相机、参考帧、遮罩方法和限制仍以两个 `comparison-report.json` 为准；外观比较不代表打印、装配、声学、热或电气验收。
