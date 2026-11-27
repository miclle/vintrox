# 终端CAD包验证

对应现有[vintrox-terminal 终端草案](terminal-model.md)，输入包位于`cad/terminal/`；使用本页的终端验证工具与报告。新 [Drone 外形草模](drone-concept.md)有独立包和读回记录，本页验证不覆盖新设计。

## 保存读回

从仓库根目录执行（已在macOS、FreeCAD 1.1.4环境验证）：

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_terminal.py
```

默认只读FCStd、STEP、STL、清单和预览，打印本次结果，结束时关闭读取文档；不保存模型或覆盖原报告。正式报告更新必须显式运行完整参数探针：

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_terminal.py \
  --exercise --output cad/terminal/terminal-validation.json
```

正式路径不接受缺少`--exercise`的输出；所有检查成功才写入，不合并旧证据。

## 检查范围

- FCStd重开后重计算，检查原生对象错误和56个实体有效性（35个打印件、14个硬件占位、7个显示/接口/螺钉头示意）。
- 逐对检查打印件与硬件占位的体积相交，无碰撞豁免；阈值0.01mm³，允许面接触。共享验证函数在刷新导出前和保存读回时均检查硬件未超出本体，报告`hardware_outside_body`记录越界实体；完整可视区无打印件遮挡、顶部槽口中心与光驱对齐且无打印件堵塞、后部线束预留区域无打印件/硬件侵入；该区域上界跟随后斜肩，见模型说明。标准接口/螺钉头是示意，不计入机械干涉判定。
- 总装STEP与FCStd实体逐个匹配世界坐标包围盒与双向布尔差集，允许STEP改变实体顺序。长度阈值1e-6mm，双向残余体积阈值1e-6mm³。单独计算体积可能受修剪曲面数值积分影响，不以单独体积相等代替形状匹配；报告另记最大独立体积积分差。
- 35对分件STEP/STL与源实体核对。STEP检查转换到建议摆放方向、底面/最小XY归零后的几何；STL检查一个封闭连通实体、包围盒误差<0.15mm、双精度累计体积相对误差<0.3%。这些是三角离散与几何判断阈值，均非加工公差。
- JSON与CSV分件清单均逐行核对模型编号、名称、标签、顺序/数量、打印包围盒和假设状态；拒绝非有限尺寸，CSV不再仅计算哈希。目录不允许缺失或多余导出；记录所有CAD、清单及预览SHA-256，核对读回前后输入文件未变化。
- `--exercise`在内存中分别修改屏宽+10、屏高+10、深度+5、托架间隙+0.1、脚高+1及排线板厚+0.2mm，验证几何重算及预期尺寸联动。斜面版另检查前斜肩进深+2、后缘下降+0.5、侧凹深+0.2、格栅端点高差+1、控制区斜面高+1和底盘切角+1mm；检查草图顶点或对应拉伸尺寸的实际联动，总计12项。另将硬盘Y设138、单箱厚设65、本体深度设150mm，要求检出冲突；每次恢复默认，未保存改动。

完整探针对默认版另核对屏幕、驱动板、SSK的用户尺寸/指定估算；普通只读检查允许已刷新后的其他参数。当前无打印、紧固件、插头/弯线、完整拆装路径、热性能、声学或电气实测。孔同源和实体封闭不证明安装可靠；假设256mm立方空间下包围盒可容纳也不证明切片/打印通过。

## 回归验证

当前10项回归包括：4项STEP几何匹配反例；CSV合法数值格式、错误表头、缺行/多行/重复/错序/错误身份或尺寸/非有限值、读回拒绝损坏CSV且不写输入；以及硬件六向越界检测、`PiZ=250`时刷新在覆盖任何导出前拒绝。

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python \
  -m unittest discover -s tests -p test_terminal_verifier.py -v
```

测试使用内存几何、保存模型只读副本和临时CSV/导出文件夹，不修改交付模型；检查读回失败或刷新被拒绝时原文件保持不变。结果与具体文件读回证据分开记录。
