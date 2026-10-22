# Drone 外形评审草模

2026-10-20 外挂筒移除修订（v4）：对照 [Alexander Shevchuk Drone 视频](../references/alexander-shevchuk-drone/video-cam.mp4)整圈视角，移除屏幕两旁的额外控件/格栅，补齐主壳侧壁、背盖及底部包覆，重建曲面喷口和叶片。按现有平面屏调整比例；背面大喷口保留低音单元占位。本轮继续对照用户补充的[近景图](../references/alexander-shevchuk-drone/closeup-2026-10-19.png)，调整前罩、提手、翼板、控制条和底部喷口；2026-10-20 按用户进一步明确的范围，删除左右外挂筒整套设计及专属弯曲线缆，共 28 个对象。对应 D-029/D-030、N-09～N-11 和 M4 外形探索。

**这是外观评审模型，未打印、未实物装配或声学测试，不是打印分件包。** 没有完成 Pi、光驱、原音箱、电池及电源的整机装配；359 个可见几何对象、462 个 STEP 实体用于分色、细节与占位，不代表打印件数量。

## 整体效果

![近景观察角度](../cad/drone-concept/renders/closeup.png)

![前左侧整体效果，展示红色翼板](../cad/drone-concept/renders/hero.png)

![后右侧整体效果及大喷口低音造型](../cad/drone-concept/renders/rear.png)

[正面](../cad/drone-concept/renders/front.png) · [右侧](../cad/drone-concept/renders/right.png)

![完整一圈八视角](../cad/drone-concept/renders/orbit-board.png)

[360° 转台视频](../cad/drone-concept/renders/turntable.mp4)：12 秒、96 个不同观察角度，由真实 CAD 网格渲染，未使用图像生成或补帧形变。

这些是保存 CAD 几何直接三角化后，用 Blender 5.1.1 / Cycles 渲染的图，不是实物照片或 AI 重绘。灯光、程序化漆面纹理及文字贴花只属于展示；纹理尚未还原参考中复杂的磨损、污渍和所有标识。灯带、仪表、屏幕表情、旋钮及附属模块均是外观示意，没有完成电路或软件。

## 文件与尺寸依据

- [FreeCAD 外形模型](../cad/drone-concept/vintrox-drone-concept.FCStd)：无零件分组，363 个对象（含参数、说明及隐藏占位）直接位于模型树顶层，显示名称全部为中文。
- [整体 STEP](../cad/drone-concept/vintrox-drone-concept.step)：只导出可见模型，不含隐藏 CD/低音占位。
- [几何清单](../cad/drone-concept/concept-manifest.json)、[独立读回结果](../cad/drone-concept/readback-verification.json)、[渲染来源绑定](../cad/drone-concept/renders/render-manifest.json)。

| 项目 | 当前输入/结果 | 状态 |
| --- | --- | --- |
| 屏幕本体 | 210 × 160 × 2mm | 用户测量口述；平面屏，背面排线板及插接净空尚未纳入本草模 |
| 可视区 | 200 × 150mm | 用户指定建模值；绿色表情仅为显示示意 |
| 可见总包络 | 约 346 × 334 × 397mm（宽×深×高，向上取整） | 从保存 CAD 读回，包含翼板、提手、天线、喷口、脚及外挂件；全部为草模派生尺寸，非加工规格 |
| 低音占位 | Ø88 × 40mm | 未选型的假设圆柱，顶层中文名“低音单元占位”，默认隐藏；不含安装耳、接线、振膜行程等净空 |
| 顶部槽与 CD | 槽约 124 × 4mm；隐藏 Ø120mm 圆盘 | 姿态与插入路径示意；未完成真实光驱、手部净空或导向验证 |

正面只保留屏幕框、前伸眉檐及下方红键/三旋钮，已去掉先前两侧竖向格栅、旋钮、文字和装饰螺钉。侧面采用封闭壳板、深色内衬和贴合轮廓的细灯带，机械圆环位于其外侧；上壳增加侧封板和后部连接面，底部增加托壳。侧扬声器与低音锥盆均为造型示意，不代表已有音箱装配通过。

大喷口由多截面光顺曲面外罩、根部连接环、背部封片、安装环、密封圈示意、分层口环及 24 片收口曲面叶片组成，每片另有加强条。近景修订将前罩改为大圆角连续下垂轮廓与细包边，翼板增加扫掠倾角及内侧色板，提手改为宽支臂与斜向包覆线，侧圆环增加口沿；左右外挂筒及其内衬、端箍、端盖、安装座、红色中心、青色指示灯、控制盒、拨钮和专属弯曲线缆已全部移除。下方控制条改为四红键、嵌入小红灯及三只带细齿旋钮；两个底部喷口各有 18 片收口叶片和加强筋。复杂磨损贴图、所有标识及参考中的曲面屏仍未完整复现，不把本轮修订描述成原作的逐细节复制。

低音占位与喷口外壳静态无体积相交；主壳侧壁及后盖的 24 个材料采样点均通过，喷口有 2 个光顺曲面及 24 片独立叶片。该检查针对上一版可见镂空与简陋喷口的回归，不证明整机气密或声学密封。实际单元、接线、固定件、分频、功放、桌面反射、强度或重心尚未验证。原终端草案保留在 `cad/terminal/`，本模型独立建立，不覆盖其导出和验证。

## 编辑与复现

使用 FreeCAD GUI 打开模型后，所有零件直接显示在模型树顶层，可按中文名称查找；低音圆柱和光盘占位默认隐藏。显示名为中文，内部脚本标识保持稳定；STEP 已按中文显示名重新导出。参数表区分屏幕输入与造型假设；**仅屏幕对象绑定参数表达式**，装甲与低音占位等由生成脚本重建，不宣称修改表格即可整机联动。

在 FreeCAD GUI 运行[生成宏](../tools/build-drone-concept.FCMacro)，调用[建模脚本](../tools/drone_concept.py)。先关闭已打开的 `vintrox_drone_refined`；宏会覆盖 `cad/drone-concept/` 同名草模及 STEP，不修改其他文档，也不会重新生成原终端。重新生成仍保持顶层零件及中文显示名；修改前先保留需要的版本。

从仓库根目录独立读回保存文件：

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Applications/FreeCAD.app/Contents/Resources/lib \
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/verify_drone_concept.py
```

验证器不保存 FCStd；检查屏幕尺寸、低音占位、平铺树结构、中文显示名、已删除外挂筒及关联部件不再生成、侧/背壳材料采样、曲面喷口及 STEP 数量/体积/包络，更新读回报告及清单包络。报告中的 `passed` 只表示这些静态检查通过。

生成宏同时将渲染网格写入系统临时目录，控制台打印 `meshfile`。将该实际路径代入：

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --threads 8 --python-exit-code 1 \
  --python tools/render_drone_concept.py -- \
  --meshes /实际临时目录/vintrox-drone-render-meshes.json \
  --output "$PWD/cad/drone-concept/renders" \
  --views closeup hero rear front right --turntable
```

[渲染脚本](../tools/render_drone_concept.py)核对网格绑定的 FCStd SHA-256 后再渲染。几何、颜色或可见性变化后须重新导出网格及全部视图。本轮包含实际几何变化，五幅静态图、八视角拼图及转台视频均从新的保存模型网格重渲染，并在清单中绑定文件哈希。无需安装项目 Python 依赖；建模/读回需要 FreeCAD，效果图需要 Blender，转台编码需要 FFmpeg。
