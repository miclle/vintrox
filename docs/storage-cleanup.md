# Drone 模型与历史产物清理

## 普通 Git 交付

当前正式 CAD 保留在 v339 交付目录与主模型路径。历史候选 CAD 仅保留文字报告、参数和对照证据。

现行模型的派生网格从保存 FCStd 在临时目录重建。原生显示与固定相机记录随当前交付归档。[当前交付](../cad/drone-concept/comparison/v339-small-pod-y-minus0p5/README.md)

v164 成为历史基线后，工作树移除其压缩网格分卷，已发布提交仍可追溯。v155、v161、v163 的旧 FCStd、STEP 和派生网格已在此前迁移中移出主分支历史。历史相机、对照、读回报告和试验参数仍可查阅。

## 2026-11-28 发布历史清理

`main` 已重写为精简历史，移除了历史中旧 Drone FCStd/STEP 文件，只在当前 v339 交付目录和主模型路径保留 4 个正式 CAD 文件。旧分阶段参数、报告和脚本仍可按目录检索，部分旧报告中的模型或图片路径仅用于追溯当时的输入和输出。原提交号也可能只在清理前的 bundle 或本机会话引用中可查。

当前 v339 的 FCStd、STEP、九视角预览、转台、三组逐视角渲染与对照、颜色核验、真实参考图片和视频均可用普通 Git 检出。正式交付检查为 `python3 tools/verify_drone_current_delivery.py`。主分支和 `migration/no-github-lfs` 可达对象扫描均仅发现当前 v339 STEP 超过 50 MiB。两条远端分支都已同步到清理后的普通 Git 历史。[正式交付](../cad/drone-concept/comparison/v339-small-pod-y-minus0p5/README.md)

## 2026-11-28 迁移分支同步

`migration/no-github-lfs` 原本仍保留 v259 CAD。已先保存本机 bundle，再将该分支同步到清理后的 v339 主线。

## 2026-11-24 保留范围

- v155 接替 v154 后，从本地 `main` 历史清出 v154 的 FCStd、STEP 和压缩网格，沿用 v154 的相机、叠加与验证记录。本机恢复包及提交映射位于 `v154-retirement.9dICmQ/`。在独立仓库导入增量恢复包后，从本机 LFS 缓存取回重放输入。[v154 评审记录](../cad/drone-concept/comparison/v154-handle-petal-combination/README.md) · [v155 当前模型](../cad/drone-concept/comparison/v155-rear-belly-relief/README.md)

- v154 成为当前评审版本后，从本地 `main` 历史清出 v151 的 FCStd、STEP 和压缩网格。v151 的相机、对照图和验证记录可继续查阅。本机清理报告 `v151-retirement.kAA28P/` 保存增量恢复包、提交映射和旧对象清单。恢复时在包含包所需基准提交的独立仓库导入恢复包，并从本机 LFS 缓存取出文件。[v151 记录](../cad/drone-concept/comparison/v151-handle-arm-tilt/README.md) · [v154 当前模型](../cad/drone-concept/comparison/v154-handle-petal-combination/README.md)

- v151 接替正式入口后，从本地 `main` 历史清出 v140 的 FCStd、STEP 和压缩网格。v140 的三组相机、对照和验证记录随仓库保留。本机清理报告 `v140-retirement.4jjuVY/` 包含恢复包、提交映射及旧对象清单。恢复时在独立仓库导入恢复包，并从本机 LFS 缓存取出文件。[v140 历史记录](../cad/drone-concept/comparison/v140-shoulder-petal-pod/README.md) · [v151 正式模型](../cad/drone-concept/comparison/v151-handle-arm-tilt/README.md)

- 正式入口保留当前版本的 FCStd、STEP、九视角预览、转台，以及当前交付校验所用的相机、网格和逐图对照。原始参考素材及 terminal 布局资料继续可用。[正式入口](drone-concept.md)
- 旧试验保留参数、分析报告、代表性对照板和复建工具。旧 FCStd、STEP、中间网格和可重建的逐帧图从本地 `main` 历史清出，涵盖 v121 和 v122 落选候选。旧文档中的附件链接用于追溯历史证据，复建需要相应版本的输入和工具。
- 本地主工作区已对齐重写后的 `origin/main`。原始主线通过 bundle 保存在本机临时目录以便回滚，Codex 会话引用和迁移分支仍可能保留旧对象。当前交付通过 `python3 tools/verify_drone_current_delivery.py` 校验。
- v130 接替正式入口后，从本地 `main` 历史清出 v120 的 FCStd、STEP、网格和可重建逐帧图。v120 的相机、对照板、读回报告及几何参数保留。清理报告目录中的 `v120-retirement.*` 保存 Git 恢复包和清单，恢复 LFS 文件还需本机对象缓存。[v120 基线](../cad/drone-concept/comparison/v120-barrel-rear-cap/README.md) · [v130 正式模型](../cad/drone-concept/comparison/v130-underbody-loop-path/README.md)
- v140 接替正式入口后，从本地 `main` 历史清出 v130 的 FCStd、STEP 和压缩网格。v130 的相机、叠加、对照板、读回报告和参数随仓库保留。本机清理报告 `v130-retirement.9OzTSn/` 包含已校验的 `pre-cleanup.bundle`、提交映射及旧对象清单。恢复时在独立仓库导入恢复包，然后从清理前的提交和本机 LFS 缓存取出文件。[v130 历史对照](../cad/drone-concept/comparison/v130-underbody-loop-path/README.md) · [v140 正式模型](../cad/drone-concept/comparison/v140-shoulder-petal-pod/README.md)

## 2026-10-31 清理记录

按用户要求，工作区只保留当前正式 Drone 模型、当前预览及必要校验依赖；旧试件、旧图片、大型中间网格和本地自动备份已清理。最新 v63 屏幕外框研究包作为最近一轮研究上下文保留，它未替换正式模型。原 terminal 布局资料和第三方参考原图保持。

### 当时的入口

- 正式模型：`cad/drone-concept/vintrox-drone-concept.FCStd`，包含最近的颜色恢复；STEP 和当前预览保持原样。
- 最新研究：`cad/drone-concept/comparison/v63-screen-bezel-study-3/`。
- v61 固定角度对比及现有 `verify_drone_delivery.py` 实际读取的文件保留；少量旧图仍是该校验的依赖。
- 小型研究报告、参数、相机、源脚本与失败结论保留。历史文档中指向已删除模型、图片或网格的链接仅表示当时的证据位置，不能再当作本地可用资源；需要复现实验时重新生成。

### 当时的 Git 与会话边界

用户授权停止正在上传历史大文件的推送，清理本地 Git 历史；本轮不向远端强制推送。清理后的本地历史与远端不再一致，后续同步需单独确认；普通拉取或合并旧历史可能重新引入大文件。

本地历史清理保留当前文件快照与文本提交历史，移除旧 CAD、图片、视频、网格及已删除产物的历史对象，并仅保留当前快照需要的 LFS 对象。不改写会话记录，不清理其他项目或 `/private/tmp`。`refs/codex/turn-diffs/` 的两个会话差异快照仍保留，用于保护现有会话；它们引用的旧普通 Git 对象仍会占用空间，因此不宣称本地所有历史二进制副本都已清空。

### 当时的验证范围

清理前现有交付脚本已报告颜色恢复后的 FCStd 哈希与旧几何、预览和评审报告不一致。本轮保持其输入及原有错误集合，不将清理描述为模型、渲染或实物验收通过。保留文件逐一进行 SHA-256 前后核对，Git 对象完整性另行检查。

详细删除清单、清理前后检查结果与空间统计保存在本机清理报告目录；它们不包含已删除的大文件副本。
