# Drone 模型与历史产物清理

## 普通 Git 交付

正式模型、STEP、报告、预览及历史对照证据随普通 Git 检出。v193 的派生网格从保存 FCStd 在临时目录重建。原生显示和固定相机复跑记录随当前交付归档。[当前交付](../cad/drone-concept/comparison/v193-lowerpod-rib-rails-bezel/README.md)

v164 成为历史基线后，工作树移除其压缩网格分卷，已发布提交仍可追溯。v155、v161、v163 的旧 FCStd、STEP 和派生网格已在此前迁移中移出主分支历史。历史相机、对照、读回报告和试验参数仍可查阅。

## 2026-11-24 保留范围

## 2026-11-27 Drone 历史 CAD 清理

提交 `24e3f39f` 从当前快照移除了 112 个已落选 Drone 候选的 FCStd、STEP 和几何副本，覆盖 v164、v173、v193、v198、v204、v207–v242、v250、v257 及 v260–v268 筛选目录。v259 正式候选包、顶层正式 FCStd/STEP、固定相机渲染、叠加差异、报告和可复现脚本继续保留。

本地精简历史已清除这些已从当前快照移除的二进制对象。历史重写只针对 Drone 比较目录中的落选 CAD/STEP 和压缩网格，不使用 GitHub LFS。远端分支同步后以分支 SHA、对象库大文件扫描和 `tools/verify_drone_current_delivery.py` 共同验收。

旧研究文档中指向已清理候选 CAD 的链接只保留参数、报告和结论语义。需要复现时从保存的正式 v259 FCStd、脚本和相机配置重建临时候选，不把已删除的历史二进制当作当前交付依赖。

- v155 接替 v154 后，从本地 `main` 历史清出 v154 的 FCStd、STEP 和压缩网格，沿用 v154 的相机、叠加与验证记录。本机恢复包及提交映射位于 `v154-retirement.9dICmQ/`。在独立仓库导入增量恢复包后，从本机 LFS 缓存取回重放输入。[v154 评审记录](../cad/drone-concept/comparison/v154-handle-petal-combination/README.md) · [v155 当前模型](../cad/drone-concept/comparison/v155-rear-belly-relief/README.md)

- v154 成为当前评审版本后，从本地 `main` 历史清出 v151 的 FCStd、STEP 和压缩网格。v151 的相机、对照图和验证记录可继续查阅。本机清理报告 `v151-retirement.kAA28P/` 保存增量恢复包、提交映射和旧对象清单。恢复时在包含包所需基准提交的独立仓库导入恢复包，并从本机 LFS 缓存取出文件。[v151 记录](../cad/drone-concept/comparison/v151-handle-arm-tilt/README.md) · [v154 当前模型](../cad/drone-concept/comparison/v154-handle-petal-combination/README.md)

- v151 接替正式入口后，从本地 `main` 历史清出 v140 的 FCStd、STEP 和压缩网格。v140 的三组相机、对照和验证记录随仓库保留。本机清理报告 `v140-retirement.4jjuVY/` 包含恢复包、提交映射及旧对象清单。恢复时在独立仓库导入恢复包，并从本机 LFS 缓存取出文件。[v140 历史记录](../cad/drone-concept/comparison/v140-shoulder-petal-pod/README.md) · [v151 正式模型](../cad/drone-concept/comparison/v151-handle-arm-tilt/README.md)

- 正式入口保留当前版本的 FCStd、STEP、九视角预览、转台，以及当前交付校验所用的相机、网格和逐图对照。原始参考素材及 terminal 布局资料继续可用。[正式入口](drone-concept.md)
- 旧试验保留参数、分析报告、代表性对照板和复建工具。旧 FCStd、STEP、中间网格和可重建的逐帧图从本地 `main` 历史清出，涵盖 v121 和 v122 落选候选。旧文档中的附件链接用于追溯历史证据，复建需要相应版本的输入和工具。
- 本地分支已重写。旧 LFS 对象仍由远端跟踪历史和 Codex 会话快照引用，缓存随这些引用保留。当前交付通过 `python3 tools/verify_drone_delivery.py --output /tmp/vintrox-delivery.json` 校验。
- v130 接替正式入口后，从本地 `main` 历史清出 v120 的 FCStd、STEP、网格和可重建逐帧图。v120 的相机、对照板、读回报告及几何参数保留。清理报告目录中的 `v120-retirement.*` 保存 Git 恢复包和清单，恢复 LFS 文件还需本机对象缓存。[v120 基线](../cad/drone-concept/comparison/v120-barrel-rear-cap/README.md) · [v130 正式模型](../cad/drone-concept/comparison/v130-underbody-loop-path/README.md)
- v140 接替正式入口后，从本地 `main` 历史清出 v130 的 FCStd、STEP 和压缩网格。v130 的相机、叠加、对照板、读回报告和参数随仓库保留。本机清理报告 `v130-retirement.9OzTSn/` 包含已校验的 `pre-cleanup.bundle`、提交映射及旧对象清单。恢复时在独立仓库导入恢复包，然后从清理前的提交和本机 LFS 缓存取出文件。[v130 历史对照](../cad/drone-concept/comparison/v130-underbody-loop-path/README.md) · [v140 正式模型](../cad/drone-concept/comparison/v140-shoulder-petal-pod/README.md)

## 2026-10-31 清理记录

按用户要求，工作区只保留当前正式 Drone 模型、当前预览及必要校验依赖；旧试件、旧图片、大型中间网格和本地自动备份已清理。最新 v63 屏幕外框研究包作为最近一轮研究上下文保留，它未替换正式模型。原 terminal 布局资料和第三方参考原图保持。

## 当前入口

- 正式模型：`cad/drone-concept/vintrox-drone-concept.FCStd`，包含最近的颜色恢复；STEP 和当前预览保持原样。
- 最新研究：`cad/drone-concept/comparison/v63-screen-bezel-study-3/`。
- v61 固定角度对比及现有 `verify_drone_delivery.py` 实际读取的文件保留；少量旧图仍是该校验的依赖。
- 小型研究报告、参数、相机、源脚本与失败结论保留。历史文档中指向已删除模型、图片或网格的链接仅表示当时的证据位置，不能再当作本地可用资源；需要复现实验时重新生成。

## Git 与会话边界

用户授权停止正在上传历史大文件的推送，清理本地 Git 历史；本轮不向远端强制推送。清理后的本地历史与远端不再一致，后续同步需单独确认；普通拉取或合并旧历史可能重新引入大文件。

本地历史清理保留当前文件快照与文本提交历史，移除旧 CAD、图片、视频、网格及已删除产物的历史对象，并仅保留当前快照需要的 LFS 对象。不改写会话记录，不清理其他项目或 `/private/tmp`。`refs/codex/turn-diffs/` 的两个会话差异快照仍保留，用于保护现有会话；它们引用的旧普通 Git 对象仍会占用空间，因此不宣称本地所有历史二进制副本都已清空。

## 验证范围

清理前现有交付脚本已报告颜色恢复后的 FCStd 哈希与旧几何、预览和评审报告不一致。本轮保持其输入及原有错误集合，不将清理描述为模型、渲染或实物验收通过。保留文件逐一进行 SHA-256 前后核对，Git 对象完整性另行检查。

详细删除清单、清理前后检查结果与空间统计保存在本机清理报告目录；它们不包含已删除的大文件副本。
