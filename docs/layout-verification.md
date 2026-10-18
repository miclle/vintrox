# CAD 布局文件验证

本工具用于已有 VINTROX 原生布局文档的保存读回，不生成模型，也不代表实物装配或整机验收通过。

## 输入与环境

- 使用安装好的 FreeCAD 自带 Python 和库；当前命令在 macOS、FreeCAD 1.1.4 下验证。
- 将本地布局包放在仓库 `cad/` 下，包含 `vintrox-layout.FCStd` 和 `vintrox-layout.step`。模型、预览和既有报告由其自身交付流程维护，本工具不自动创建输入文件。
- FCStd 使用原生 `Parameters` 参数表和 `Enclosure`、`Hardware`、`Details` 分组，以及 `CableLane` 预留区。第三版另检查 `DisplayClearance` 可视区净空、顶部槽口对齐/无木壳堵塞及含底座/控件的总包络。静态判定实现位于 [layout_checks.py](../tools/layout_checks.py)，不依赖 CAD 生成器或 GUI 宏。

## 只读复核与报告输出

在仓库根目录执行：

```sh
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_layout.py
```

[验证器](../tools/verify_layout.py) 默认只打印本次 JSON 结果，不写 FCStd、STEP、预览或现有报告。检查静态干涉/内腔/后部线束区，并将 FCStd 的实体与 STEP 一一匹配：比较世界坐标中不依赖三角网格的几何包围盒、体积及两个方向的布尔差集，不依赖 STEP 实体顺序。长度容差为 0.000001mm，各方向残余体积容差为 0.000001mm³；这是几何计算判据，不是加工公差。实体数量和总体积相同不足以通过。

默认布局的十一项参数联动（含屏幕/排线板尺寸、木壳圆角、黑框内嵌和底座高）、四档深度及故意干涉探针通过 `--exercise` 启用；该选项单独使用也只打印结果。更新正式报告时必须显式指定输出路径：

```sh
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_layout.py \
  --exercise --output cad/layout-validation.json
```

正式路径 `cad/layout-validation.json` 必须同时指定 `--exercise`，且所有检查成功后才写入。再次默认复核不清空正式报告的探针和版本对照证据；检查失败也不覆盖原报告。输出均是本次新执行的证据，不合并旧结果，`parametric_exercise_executed` 标明是否执行探针，`step_geometry_comparison` 记录逐实体对照。

生成/刷新布局会使旧证据失去适用性，需重新读回。自定义布局不保证适用默认探针或初版包络对照，可用默认复核加 `--output` 写到其他 JSON 路径，保留其验证范围，不能当作默认布局完整探针通过。

## 回归验证

[回归测试](../tests/test_layout_verifier.py) 使用真实 FreeCAD 几何及临时副本：

- 3 项几何回归无需本地布局包：同体积同包围盒的形状变化被拒绝、STEP 实体顺序可变化、重复实体不能代替缺失实体。
- 5 项保存读回回归需要本地 `cad/` 下的 FCStd、STEP 及含完整探针证据的 `layout-validation.json`：默认复核保留报告/模型/预览、显式完整输出后再次复核、正式路径拒绝未执行探针的输出、独立路径记录局部结果、STEP 平移被拒绝且失败不覆盖报告/不遗留读回文档。
- 缺少本地布局包时，5 项集成回归明确跳过，不表示集成验证通过。测试不修改原布局包；几何反例在内存或临时副本中构造。

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  -m unittest discover -s tests -p test_layout_verifier.py -v
```

2026-10-18 在本地既有布局包与 FreeCAD 1.1.4 下执行，8 项全部通过；没有布局包时的预期结果为 3 项通过、5 项跳过。尺寸信息与实物验收继续统一记录在 [测量与验证清单](validation.md)。
