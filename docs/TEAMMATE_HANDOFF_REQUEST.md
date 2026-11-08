# 首例交接说明（供 Ye Boyang 转发，未自动发送）

我这边已准备好两套官方预训练权重和独立环境，并通过了严格参数加载及随机输入技术检查；尚未使用项目 MRI，也没有训练或分类结果。

请优先交付同一例的 T1，不需要等全队列或全部 fMRI 做完。首选 `sub-mindo304`，session 先核对；当前清单使用 `sub-mindo304_ses-placebo`。如 QC 不通过，请保留失败结论，我们再换例。

最小交付：

1. 预处理 T1 NIfTI、脑 mask、配准变换、配准/脑提取 QC 图。
2. 原始文件与结果哈希、实际 session、图像方向/尺寸/体素、模板哈希、软件版本和实际处理参数；注明人工 QC 审核人及结论。
3. 按 `configs/handoff.example.json` 填 `handoff.json`，只把实际通过 QC 的 T1 阶段标为 ready/pass，其他阶段保留 pending。

BrainIAC 作者参考模板已准备：170×206×162、1 mm、LAS；SHA-256：

`d8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e`

先一起确认是否采用该模板及实际保存轴向。作者示例为 N4、刚体配准、HD-BET；已做过的步骤不要重复。96³ resize 和模型侧非零强度标准化由我这边完成；FreeSurfer 体积继续保留高分辨率处理链。

fMRI 后续交付完整 ROI 时序、逐列 ROI 名称/顺序、头动与去噪记录、QC 图和连续 160 帧的原始索引。Brain-JEPA 作者顺序为 Tian S3 3T 50 个皮层下区在前、Schaefer17n400p 400 个皮层区在后；梯度文件是 450×30。请先核对具体图谱和标签顺序，不要只按 450 个 ROI 或自行按编号重排。

标准化、分支/池化和 Schaefer17→7 网络映射仍需我们共同确认。详细证据与候选方案见 `docs/ENCODER_INPUT_SPEC.md`；权重加载成功不代表输入配方或真实 QC 已通过。
