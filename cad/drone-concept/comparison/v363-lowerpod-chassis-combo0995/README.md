# v363 小喷口外壳与底盘组合筛选

v363 以 v345 为基线，在同一保存真实 CAD 中组合 v359 的左右 `LowerPod_1`、`LowerPod_001` 局部 XY `0.995` 倍缩放和 v361 的 `BottomChassis` Y 向 `0.995` 倍缩放。平面实测屏幕、四根支柱、外挂筒、屏幕侧控件和格栅保持。

| 比较集 | v345 | v363 |
| --- | ---: | ---: |
| 视频十方位 | 86.2414280% | 86.2438527% |
| 静态七图 | 82.7168109% | 82.7175722% |
| 拼图十格 | 89.9819783% | 89.9825419% |

三组指标均高于 v345 和两个单变量候选，v363 作为当前研究候选保留，但增量很小，仍不能宣称达到 90% 整圈目标或主要部件 5% 投影偏差目标。比较使用真实 CAD、固定相机、半透明叠加和轮廓差异图，没有图像变形、逐件配准或省略可见零件。

保存读回确认三个变更对象有效闭合，698 个对象闭合，696 个可见对象，STEP 为 853 个有效闭合实体；底盘与主壳、腹板、小喷口和底部回环接合保持。颜色和可见性从 v345 恢复。

候选目录仅保留摘要、哈希、相机配置和比较报告，可再生的大型 FCStd、STEP、网格和 PNG 已清理。

从普通 Git 检出的 v345 恢复 v363 彩色 FCStd 时，在仓库根目录运行以下命令。补丁占 267 KiB。恢复文件已与原保存文件逐字节核对。

```sh
research_dir=$(mktemp -d)
cp cad/drone-concept/comparison/v345-small-pod-y-minus1p0-cable/candidate.FCStd "$research_dir/"
gzip -dc cad/drone-concept/comparison/v363-lowerpod-chassis-combo0995/from-v345.patch.gz | (cd "$research_dir" && git apply --binary -)
shasum -a 256 "$research_dir/candidate.FCStd"
```

预期 SHA-256 为 `2372bc6788487af2dc3de7e49eb6b34dfdfe7b835b523e0e44e9f466c948308b`。
