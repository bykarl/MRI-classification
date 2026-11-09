# 首例数据接收检查：已收尾（技术试跑）

对象：`sub-mindo304_ses-placebo`。本记录覆盖第一阶段的数据接收、来源核验和输入头信息策略，不表示已经完成影像预处理或人工 QC。

## 实际完成

- Colab CPU 环境已运行：2 个逻辑 CPU、12.67 GiB RAM，Python 3.13.18。未安装或验收完整 FreeSurfer/fMRIPrep 环境；不能将第一步称为预处理环境全部搭建完成。
- T1、BOLD 及匹配 JSON 的来源已核对到 OpenNeuro `ds007857` 的 `1.0.1`，固定提交 `0b11e8604142ebb9d335f57877238f3aad44e194`。两份 MRI 的大小和 SHA-256 与上游 git-annex 内容键一致，JSON 与上游逐字节一致。
- 全体素读取、有限值、图像维度和 BOLD TR 检查通过。T1 为 256×256×156；BOLD 为 64×64×43×240，TR 2 秒。
- 独立 `intake_v2` 输入副本实际保存并重新读取验证：未缩放、插值、重新采样或调整体素数组。原始 MRI 哈希不变；副本的原始和缩放后体素值均与原始完全一致，所采用的世界坐标 affine 保持不变。

## 三个问题的处理结论

### 1. 体素尺寸及 qform/sform

BOLD 的原始 pixdim 为 `[2, 3.4375, 3]`，编码 sform 的列范数为约 `[3.4375, 3.4375, 3]`。上游本身存在此冲突，不是本次传输损坏。原始 JSON 的非标准 `VoxelSize` 字段另写 `[3,3,3]`，同样保留并记录，不能据此重缩放数据。

本项目**首例技术试跑策略**采用原文件已有的有效 coded sform：NiBabel 默认即优先使用非零 sform；MiND 研究方案给出的静息态 FOV 220×220 mm，结合本文件 64×64 矩阵，推得 3.4375 mm 面内间距，与 sform 相符。这是有来源支撑的项目输入选择，**不是从个体 DICOM 得到的独立确认**，不推广为全队列自动修复规则。

副本中根据该 sform 统一 pixdim，空间单位标记 mm，保留 sform 的数值和编码。原矩阵有轻微非正交成分，qform 无法无损容纳；因此在副本中将 qform_code 设为 0，使用唯一有效 sform，未强行正交化或近似矩阵。T1 的原 qform/sform 不同并不单独证明错误；同样保留其既有 sform 空间解释，原有两种矩阵存入审计 JSON。

### 2. 单位与 TR

BOLD 原头部空间和时间单位未知。按上述协议/坐标证据在输入副本中明确 mm；按原始逐例 JSON 及协议明确秒、TR 2 秒。原始文件和 JSON 不覆盖，副本记录新的哈希和采用依据。

### 3. SliceTiming 与场图

已检查上游数据集根目录、受试者和 session 的 JSON 继承位置、逐例 BOLD JSON 和 NIfTI slice_code。未找到可靠 SliceTiming，slice_code=0，**本次跳过切片时间校正**；不从 GE 型号、43 层或通用交错顺序猜测时间。

本 session 只有 anat/func，没有场图采集；因此不声称执行场图驱动的畸变校正。JSON 中有相位编码方向和读出时间并不等于有场图。未来若选择 fieldmap-less 方法，须另立方法版本，不能冒充实测场图校正。

## 真实执行证据及恢复

- `reports/intake/sub-mindo304_step1_closeout.json`：实际 Colab 执行导出的记录，路径已转为项目相对形式；不包含原始 MRI。
- `notebooks/01_liyang_intake_check.ipynb`：已执行的检查 Notebook 副本，保留真实文本输出；去除浏览器下载 JavaScript、Colab 账户元数据和内嵌图像输出。原始预览仍在报告包和私人 Drive Notebook 中。
- `scripts/close_first_record_intake.py`：收尾逻辑，调用方式为导入后执行 `close_step1(Path('/content/FYP_MRI_LiYang'))`；依赖首轮检查生成的 `input_check_with_geometry.json` 与本地两份原始 MRI/JSON。只支持该首例，其他病例必须重新核验。
- 持久报告包保留 initial_snapshot，并追加最终 closeout；原来的 review_required 检查历史未删除。原始/副本 MRI 当前仍在 Colab 临时磁盘，**并未声称已持久备份影像**。会话回收后按 Notebook 的固定来源重新取得并生成副本；第二阶段长计算开始前必须落实持久检查点存储。

两次严格 qform 写入检查失败后，采用 sform-only 的无近似策略；最终实际执行通过。未将失败尝试记录成通过。

## 第二阶段仍需执行的工作

安装和验收处理工具；与特征负责人确认 BrainIAC 模板及输入配方；锁定 fMRI 去噪/QC 参数及 Brain-JEPA 确切图谱/顺序，再运行 N4、脑提取、配准、FreeSurfer、功能预处理。不存在已完成的 brain mask、配准 QC、82 项体积或 ROI 时序交接。

状态：**第一步技术接收已完成并保留限制；预处理未完成，QC pending，training_ready=False。** 自然人身份和诊断时点核查仍不由本次影像头信息整理代替。

## 依据

- [原始数据集](https://github.com/OpenNeuroDatasets/ds007857/tree/0b11e8604142ebb9d335f57877238f3aad44e194)
- [MiND 研究方案：Resting State](https://doi.org/10.1186/s12883-019-1294-6)
- [NiBabel：Choosing the image affine](https://nipy.org/nibabel/nifti_images.html#choosing-the-image-affine)
- [fMRIPrep：按元数据决定切片时间校正](https://fmriprep.org/en/stable/workflows.html)
