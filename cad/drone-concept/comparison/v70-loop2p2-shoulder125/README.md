# v70 回环 2.2 mm + 后肩指数 1.25 候选

v70 从 v69 继承 2.2 mm `UnderbodyLoop0/1`，仅再将 `RearArmourCheekLeft/Right` 截面指数从 1.5 改为 1.25。四根支柱、中心座、外挂筒、屏幕侧控件、格栅和实测平面屏保持。

保存读回结果为 698 个对象、696 个可见对象、1010 个 STEP solids，实体有效闭合，保护支撑与正式 v61 相等；FCStd/STEP 哈希和证据见 [candidate-check.json](candidate-check.json)、[readback-verification.json](readback-verification.json)。

固定相机视频十方位平均 IoU 为 **85.551170%**，相对 v69 **−0.00215 个百分点**；静态七图为 **82.292743%**，相对 v69 **+0.03312 个百分点**。静态改善不足以抵消视频轻微退步，因此保留 v69 作为当前研究候选，正式入口仍保持 v61。该结果是屏幕空间外观诊断，不代表制造、装配、承力、声学、热、电气、打印或实物验收。
