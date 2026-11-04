# FreeCAD 原生显示核验（2026-11-04）

正式 v61、v69 显示副本、v73 嘴部候选分别通过独立 FreeCAD 1.1.4 原生 GUI 只读打开，保存轴测、正面、背面、右侧共 12 张原生截图，见[视图板](native-display-board.png)、[核验记录](native-display-verification.json)和[目视记录](visual-review.json)。没有保存、重建或修改模型；三份文件打开关闭后的 SHA-256 均保持。

每份 696 个可见对象与名字／可见性契约一致；原生保存色有 70 组 RGB，网格浮点色有 74 组，最大通道差 0.001960814，不超过半个 8 位色阶加浮点容差。颜色组数因量化合并而不同，不能把两者混为同一精度。正式 v61 使用[名字与颜色契约](formal-palette-contract.json)，它来自 v69 的相同对象名单和色表，**不声称是正式模型的几何网格**。v69 显示副本的文档／BRep 与原候选一致，由既有 display-restoration.json 证明。

旧进程 RPC 拒绝连接、CUA 无窗口，以及离屏 OpenGL 失败属于历史失败证据；本次使用 Cocoa 原生 GUI、safe mode 与独立临时用户／系统配置，绕开旧进程。没有关闭或改动旧进程。缺少 3DconnexionNavlib 的启动提示未阻止本次打开和截图。

复现使用 `tools/verify_drone_native_display.FCMacro`。配置 JSON 包含 `output` 与 `models` 数组，每项含 `name`、`model`、`mesh`（几何网格或仅名字／色表契约）；必须在独立 GUI 进程运行，因为宏结束会关闭其自身主窗口：

```sh
VINTROX_NATIVE_AUDIT_CONFIG=/tmp/vintrox-native-audit-config.json QT_QPA_PLATFORM=cocoa /Applications/FreeCAD.app/Contents/Resources/bin/freecad --safe-mode --user-cfg /tmp/vintrox-audit-user.cfg --system-cfg /tmp/vintrox-audit-system.cfg tools/verify_drone_native_display.FCMacro
```

该证据证明这三份指定哈希模型的原生打开、保存可见性、色表及四视图显示；不能推广到所有历史候选或所有隐藏面。整机 90% 与完整主要部件轮廓 5% 目标仍未完成，不代表曲面屏光学、制造、装配、电气或实物验收。
