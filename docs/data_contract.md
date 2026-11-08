# 单例输入与特征交接 v0.1

本文件将 2026-11-07 协作规范转为当前代码接口；分工与待定方法仍须双方确认。原始 MRI、82 项体积和完整 ROI 时序由预处理方交付。以下模板中的 pending/null 不可直接改成 ready/pass 来绕过缺项。

## 单例键和目录

使用 `record_id=participant_id_session_id`，当前如 `sub-mindo304_ses-placebo`。自然人 ID 另行核查；未知 person_id 留空，禁止正式验证。多 run 时必须扩展唯一键。

每例放在 `ARTIFACT_ROOT/derivatives/{pipeline_id}/{record_id}/`，根目录含 `handoff.json`。按 `configs/handoff.example.json` 填写：各阶段分别记录 status、qc_status、qc_reviewer 和具名 files；每份文件给出相对此例目录的路径及实际 SHA-256。程序验证哈希，不允许越界路径。

- `t1` 阶段：processed_t1、brain_mask、transform、qc_image；另给出已确认模板 SHA-256。交接 NIfTI，附空间、方向、尺寸、体素和处理步骤等 QC 说明。模型侧 resize/标准化由适配器完成。
- `structure` 阶段：首选在 files 中给出 `volumes_csv`（已约定的 t1_volumes_raw.csv），按 record_id 一行，列名遵循 `schemas/t1_volume_names.json`，另含 icv_mm3、icv_method、freesurfer_version、qc_status。也可交付 lh_aparc、rh_aparc、aseg 原始统计文件和手动核验的 ICV/版本字段，由适配器读取；原始 stats 仍应保留供追溯。输出 82 项原始 mm3 体积，ICV 单独保留。CSV 与 handoff 同名字段冲突时停止。训练内拟合 ICV 回归，不能提前全队列校正。
- `fmri` 阶段：roi_timeseries、roi_order、motion、window、qc_image。时序为完整 `[T,450]` NPY，不先对全项目人群拟合缩放参数；同一窗口用于 FC 和 Brain-JEPA。

## ROI 与窗口

`roi_order.tsv` 字段见 `schemas/roi_order.example.tsv`。column_index 从 0 连续排列，atlas_label 必须在最终合并图谱中唯一；若来自不同图谱，可采用带图谱前缀的唯一标签，但必须与确切编码器顺序表一致。400 个 cortical、50 个 subcortical。hemisphere 为 L/R。

皮层 network7 固定为 Vis、SomMot、DorsAttn、SalVentAttn、Limbic、Cont、Default。它们是本项目 schema 名称，不表示已经完成作者 Schaefer17 到 7 网络的映射。皮层下 parent_structure 为 thalamus、caudate、putamen、pallidum、hippocampus、amygdala、accumbens，合并左右用于 FC。完整的 ROI、映射、图谱、空间及 gradient 哈希由双方核对。

`window.json` 使用以下字段（实际索引由 QC 生成）：

```json
{
  "row_start": 0,
  "row_end_exclusive": 160,
  "start_frame": 0,
  "end_frame_exclusive": 160,
  "frame_indices": [],
  "tr_sec": 2.0,
  "discarded_initial_frames": null,
  "qc_rule_id": null
}
```

这是不可执行的字段示意：frame_indices 必须填满实际连续 160 个原始帧索引。row_start/end 是完整交付时序的行范围，start_frame/end 是原始扫描时间轴。若已丢初始帧，两套索引可能不同，须保留映射。可以用 `mri_pipeline.fmri.select_window(fd, acceptable_mask, original_frame_indices)` 在**已锁定的 QC 布尔掩码**上选最低平均 FD 窗口；并列取最早，不拼帧、不补零。函数不会替双方决定 FD 阈值。

## 特征输出

`features/{feature_set_id}/{record_id}/` 保存 `s_t1_raw.npy`、`s_fmri.npy`、`z_t1.npy`、`z_fmri.npy`。每个组件另有同名 JSON（如 z_t1.json），用于逐模态交付时独立校验，避免并发改写同一清单；四个联合组件通过合并后生成汇总 `features.json`。单组件或单模态临时合并只使用组件 JSON，不提前生成不完整的总清单。这是对原协作规范的显式增补，不改变四个数组名。

每个 JSON 包含 record_id、pipeline_id、feature_set_id、源文件与哈希、handoff 哈希、names、recipe、输出哈希、数值/维度和环境。s_t1_raw 另记 ICV，fMRI 两组件必须有相同 window_id（window.json 的 SHA-256）。同一分量跨例的 names/recipe/pipeline_id 必须一致；切换权重、图谱、去噪、归一化或池化时更换版本标识。标签、MoCA 不进入影像数组。

合并按 record_id 一对一连接，重复 ID、缺分量、改动后的数组、混合权重配方、NaN/Inf、零方差 ROI 或窗口不一致会报错，不静默补零。人口学缺失在训练路径内拟合填补，教育代码为类别。

## 状态与验收

初始 `manifests/processing_status.csv` 为待办模板，不代表实时运行结果。每次 `run_features.py` 在 ARTIFACT_ROOT/logs 生成独立成功/失败 JSON，记录开始/完成时间与耗时；用 `report_status.py` 生成新的状态 CSV，不覆盖历史源表。程序成功和 QC 通过分开记录，下载成功不提升 training_ready。

阶段 ready 依赖实际文件哈希、QC 审核和成功执行；身份与诊断时点仍未确认的试跑记录可以验收技术步骤，但不能进入正式分组分类。
