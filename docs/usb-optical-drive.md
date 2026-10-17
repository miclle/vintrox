# Raspberry Pi USB CD/DVD 光驱：安装、使用与供电排障

更新：2026-10-17。适用于当前 VINTROX 原型所用 Raspberry Pi 4B + Debian GNU/Linux 13 (Trixie)；其他 Raspberry Pi OS/Debian 版本需要复核软件包和设备权限。

> 本文区分用户报告的现场现象与尚未完成的工程验收。**辅助 USB 供电恢复读盘**不等于已完成 CD-DA 音频播放、竖装或整机供电验证。

## 1. 现场记录：USB DVD 光驱反复消失

- **环境**：Pi 4B、Debian 13，图形界面 `gnome-disks`，USB DVD 光驱。项目计划复用 MATSHITA DVD-R UJ-898，但本次尚未保存 `lsusb`、`lsblk` 或设备铭牌信息，不能据此断定测试光驱的具体硬件型号/桥接芯片。
- **故障表现**：Disks 设备列表中 `CD/DVD Drive` 周期性出现/消失，光驱转速也重复变化。
- **用户采取的措施**：将分叉 USB 线的**辅助供电插头**接入电源。
- **用户报告结果**：之后光驱可以正常读取光盘。辅助插头具体接在另一个 Pi USB 口还是独立 5V 电源、线材接法、测试介质、持续运行时长及电气数据**尚未记录**。
- **初步判断**：供电裕量不足与现象高度吻合；没有保存内核日志，尚未证明断连事件的具体错误码，也没有排除线材/转接板等因素对其他工况的影响。

Pi 4B 的 USB 外设 5V 总预算为 **1.2A（所有 USB 端口共享，不是每个口 1.2A）**。光驱电机启动或加速可能有较大瞬时需求，移动硬盘等外设也占用预算。`vcgencmd get_throttled` 返回 `0x0` 不足以证明**光驱端**没有瞬时压降；100W USB-C PD 适配器也不会自动突破 Pi 主机 USB 的总限流能力。

**电气警告**：不要在未知 Y 型线内部电源连接方式时，将两台独立 5V 电源直接并到一起。最终方案优先评估独立供电、具防反灌设计的 USB Hub／专用外设 5V 分路，测量启动电流、最低电压与反灌情况后再锁定供电结构。

## 2. 一次安装与可重复执行的工具脚本

仓库脚本：[`../scripts/usb-optical-drive.sh`](../scripts/usb-optical-drive.sh)。默认不会自动安装、挂载、播放或弹出光盘；**必须明确指定子命令**。安装仅安装缺失的包，不改配置文件、不会覆盖现有数据；重复运行不应引入额外修改。

```bash
# 在 VINTROX 仓库根目录，安装命令行工具
bash scripts/usb-optical-drive.sh setup

# 若需要 GNOME Disks、文件管理器 GVfs 光盘支持
bash scripts/usb-optical-drive.sh setup --with-gui

# 查看已识别的光驱、USB 与电源信息
bash scripts/usb-optical-drive.sh status

# 光驱出现/消失时查看内核最近 120 行日志
bash scripts/usb-optical-drive.sh logs
```

依赖：`eject`、`libcdio-utils`（提供 `cd-info`）、`cd-paranoia`、`mpv`、`usbutils`；GUI 可选 `gnome-disk-utility`、`gvfs`、`gvfs-backends`、`udisks2`。`setup` 使用 `apt-get`，仅支持基于 Debian 的系统。`sudo` 只用于装包、读取受限内核日志和挂载/卸载；播放及 GUI **不要用 sudo 运行**。

## 3. 检测光盘与使用命令

```bash
# 多个光驱时指定设备，或设置 VINTROX_OPTICAL_DEVICE=/dev/sr0
bash scripts/usb-optical-drive.sh --device /dev/sr0 disc-info

# 音乐 CD 的音轨目录（TOC）
bash scripts/usb-optical-drive.sh tracks

# 音乐 CD：不需要挂载
bash scripts/usb-optical-drive.sh play-cd

# 普通 DVD 影片：播放器/加密与区域码兼容性需另测
bash scripts/usb-optical-drive.sh play-dvd

# 数据 CD/DVD：只读挂载；第二次重复执行会发现既有挂载并跳过
bash scripts/usb-optical-drive.sh mount-data
ls -lah /mnt/vintrox-disc

# 卸载脚本专用挂载点；未挂载时会直接跳过
bash scripts/usb-optical-drive.sh unmount-data

# 退碟；吸入式光驱未必支持 close（收回托盘）
bash scripts/usb-optical-drive.sh eject
bash scripts/usb-optical-drive.sh close
```

- Linux 光驱通常是 `/dev/sr0`，但**不是固定保证**。脚本在仅发现一个 `/dev/srN` 时自动选择；多个时要求 `--device`，不猜测目标。
- **CD-DA 音乐 CD** 不按普通文件系统挂载，使用 `tracks` / `play-cd`。**数据 CD/DVD** 可以只读挂载；桌面自动挂载时脚本检测到已有挂载会跳过，原挂载位置不变。
- 使用 `mpv` 的 CD/DVD 播放命令，需要在登录用户的图形桌面终端或具备正确音频会话的环境执行。`mpv` 默认输出设备可能是 HDMI，不意味着 DAC/扬声器已联调。
- `mount-data` 默认挂载到 `/mnt/vintrox-disc`，可通过 `--mount-point /absolute/path` 指定。`unmount-data` 仅处理该路径上的光学设备挂载，**不会强制卸载其他设备**；如果数据光盘已由桌面挂载，请从文件管理器弹出/卸载。
- `eject` 可能因为光盘仍在使用或挂载而失败，应先退出播放器、卸载数据盘；`close` 对 UJ-898 这类吸入式设备不保证有效。

## 4. 图形桌面

在登录图形桌面的终端执行：

```bash
bash scripts/usb-optical-drive.sh gui
```

或者直接运行 `gnome-disks`。无盘或纯 CD-DA 介质在文件管理器中不一定显示为普通文件卷；GNOME Disks 更适合查看设备本身。数据 CD/DVD 可以用文件管理器浏览，音乐 CD 交给支持 CDDA 的播放器。SSH/TTY 无 `DISPLAY`/`WAYLAND_DISPLAY` 时无法直接弹出 GUI 窗口。

## 5. 排障与验收矩阵

| 现象 | 首选检查 | 说明 |
| --- | --- | --- |
| `Disks` 光驱反复出现/消失、马达反复起停 | `status`、`logs`，减少其他 USB 负载，比较辅助供电前后 | 优先排查光驱瞬时供电、转接板和线材 |
| `lsusb` 有桥接但没有 `/dev/sr0` | `logs`、线缆与桥接器，空盘/有盘对照 | 不把识别出 USB 桥接等同读盘成功 |
| `/dev/sr0` 存在但不能读取 CD-DA | `disc-info`、`tracks`，换已知正常的音乐 CD | 检查权限、盘片和 CDDA 支持 |
| 挂载数据光盘失败 | 确认介质不是音乐 CD、检查 `disc-info` | CD-DA 不应使用 `mount` |
| CD 能播放却无声 | 检查 mpv 输出设备和 ALSA/PipeWire | 本次不代表外部 DAC、RCA 或内置音响已验证 |
| `get_throttled=0x0` 但光驱仍掉线 | 测量光驱供电端最低电压/启动电流 | Pi 主板欠压标志无法覆盖所有外设支路 |

建议下一轮记录：`lsusb -t`、`lsblk`、`journalctl -k`、`vcgencmd get_throttled`、桥接器与 Y 线照片、每支电源的来源、空盘/数据盘/CD-DA 测试结果、连续工作时间、重复插退次数，以及移动硬盘并发读写下的情况。**这些数据尚未采集，不能勾选 T-01/T-04 整体验收**。

相关跟踪：[`validation.md`](validation.md) T-01/T-04、[`hardware.md`](hardware.md) 光驱与 Hub、[`power-system.md`](power-system.md) 5V 分路、[`roadmap.md`](roadmap.md) M1。

## 6. 命令参考

- [Debian 13：`cd-paranoia` 软件包](https://packages.debian.org/trixie/cd-paranoia)、[命令参数](https://manpages.debian.org/trixie/cd-paranoia/cd-paranoia.1.en.html)
- [Debian 13：`cd-info` 命令参数](https://manpages.debian.org/trixie/libcdio-utils/cd-info.1.en.html)
- [MPV 官方手册：光驱播放参数](https://mpv.io/manual/stable/)
- [Raspberry Pi 供电与 USB 限制](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
