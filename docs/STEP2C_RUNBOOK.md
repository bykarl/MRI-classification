# 2C 操作教程：首例 FreeSurfer 体积提取

## 本次准备到什么程度

### 2026-11-10 跑前实测补充

独立 notebook 已保存；Git 中发布时所有执行计数与输出为空。旧的首例 notebook 另行执行了 P1/P2/P3 对应的**准备代码**：固定源码下载与 SHA、当前资源检查、Drive 中 raw/native T1 逐文件 SHA 核验均实际执行，输入哈希通过，准备报告已复制至 `freesurfer_pilot/preparation/` 并读回一致。没有运行个人许可上传、安装、初始化或 autorecon。

当前打开会话实测 2 CPU、12.67 GiB 有效内存、约105.4 GiB空闲磁盘、Ubuntu24.04，低于本候选30GiB内存门槛；检查时没有个人许可。**源码/输入准备完成不等于运行环境已就绪**。检查的是这个会话，不能推断其他用户会话的资源。小型公开审计记录见 `reports/freesurfer_preparation_status.json`。

已准备：固定首例/输入哈希、软件来源与包校验、资源预检、三个独立计算入口、每段完整 subject 检查点、断线恢复、QC 图生成、82 项原始体积和 eTIV 导出，以及与 karl 读取代码一致的交接格式。

**尚未在 Colab 安装或运行 FreeSurfer，没有真实 FreeSurfer 分割、体积、ICV 或运行时间结果。** 本地 15 项测试仅用明确标记的 SYNTHETIC 数据，检查解析/接口和防误运行逻辑。正式 notebook 的执行计数/输出均为空。后续真实病例验证仍必须做。

## 先看两个必要条件

1. **资源。** 这份候选固定 FreeSurfer 8.2.0，支持 Ubuntu 22.04/24.04 amd64，以 `FS_V8_XOPTS=0` 使用官方保留的传统 recon-all 行为。官方给 8.x 的系统要求是 32 GB+；本准备采用保守的 **有效内存至少 30 GiB（约 32 GB 机器）和本地空闲磁盘至少 40 GiB** 门槛。之前 12.7 GB 的 Colab 会话会被挡住，不能当作已经具备运行条件。显卡不能补足系统 RAM。这里没有购买资源、切换套餐或分配新 GPU。
2. **个人 license.txt。** 用户自行阅读官方许可并注册获取文件；不能由脚本代填申请、同意条款或生成假许可。Notebook 只在你主动上传后将其放到 `/content/license.txt`，不打印内容、不上传 Git、不进入 subject 归档。每个新会话可能需重新上传。

内存要求是本候选的保守安排，不声称传统模式的绝对最低内存是 30 GiB，也不保证满足数字就一定跑通。官方说明新 8.x 快速流程的部分内存峰值可很高；本方案明确关闭该流程，不能引用其约两小时基准来承诺本方案耗时。软件版本/模式在后续全部病例中应保持一致，不静默换版本。

## 输入固定为何物

- 病例/session：`sub-mindo304_ses-placebo`。
- 直接读取已备份到 Drive 的 **原分辨率 intake_v2 T1**：256×256×156，约 1 mm；它只做过第一阶段记录的 header 整理，体素值与原始影像相同。
- 不是 2B 的 N4 图、模板空间图、HD-BET 去颅骨图，也不是 96³ 编码器张量。FreeSurfer 使用独立的高分辨率原生处理链，内部完成自身校正/分割/重建。
- 同时核对原始 T1 SHA-256 `89ea431ba0e912d1b73643a4ce691dbe13ad54da394b645942e4e12dceaf73b5` 与 native intake T1 `8e6d3104d6171e3528aefe6288357f8cfee97724f0044232bac7c2fd3641dccb`。无需重新下载整套 MRI。

当前输入路径在 `MyDrive/FYP_MRI_LiYang`。如果你换了 Google 账号或挂载了另一个 Drive，缺失检查会停止，不会以其他病例替代。

## Notebook 的顺序

使用 `notebooks/06_liyang_freesurfer_2c.ipynb`，从上往下逐格操作，**不要直接 Run all**。

1. **读取固定代码快照、检查资源**：只取小型公开代码，先检查 OS、CPU、RAM、磁盘。失败则到此停止，不会下载 FreeSurfer 的约 8–9 GB 安装包。
2. **挂载 Drive、核对输入**：Google 授权由你自己完成；代码只核对项目中已有的两份 T1 文件。
3. **上传个人 license.txt**：先通过官方表单取得。上传框不要选择 MRI 或其他文件。
4. **明确启用安装**：你阅读并接受官方软件许可后，把对应布尔变量设为 True，再执行安装格。它下载与 Ubuntu 版本匹配的官方 DEB，核对官网 MD5，记录下载后 SHA-256，通过系统包管理器安装；不通过解包 DEB 来假装完成安装。实际版本、关键共享库和 fsaverage 缺失会在启动前报错。没有自动运行网站上的可变热补丁脚本；若 vendor 安装出现依赖/已知版本问题，先根据输出复核，不直接反复跑重建。
5. **初始化首例**：记录新的 run ID、输入哈希、配置、源码快照和实际 FreeSurfer/OS 指纹。
6. **C1 / autorecon1**：输入转换、内部校正、配准、去颅骨等前段。成功后保存完整 subject 的第一份归档与读回哈希。
7. **C2 / autorecon2**：分割和主要皮层表面重建。通常最耗时；等本格正常结束、检查点写回成功再继续。
8. **C3 / autorecon3**：皮层分区及统计。成功后核对三个真实 stats 文件并保存第三份完整归档。
9. **生成 QC 图**：实际读取 norm、aseg 和 aparc+aseg，输出三方向抽样叠图，保持 `pending`。颜色图是模型预测，不是 GT。
10. **导出 draft**：保存 82 项未做 ICV 校正的 mm³ 体积、单独 eTIV、原始 stats、QC 和待审核交接文件。
11. **人工审核后才正式交接**：查看完整体积和左右 white/pial 表面、Talairach 配准等；按模板写真实审核人/检查项。与特征方确认本软件配方及全项目通用 pipeline_id 后，才可显式运行 finalize。为下周技术汇报保留 draft/pending 是允许的，不需要虚填 pass。

每格的代码只在你点击运行后执行；本次没有代你启动这些计算。软件安装和 FreeSurfer 重建与 ChatGPT 的五小时额度不是同一个计时系统，但 Colab 本身会有会话/资源限制，不能保证单个长阶段永不中断，也不提供规避其限制的保活操作。

## 保存与恢复

- 计算目录：`/content/FYP_MRI_LiYang/freesurfer_pilot/runs/<RUN_ID>/`。
- 持久目录：`MyDrive/FYP_MRI_LiYang/freesurfer_pilot/runs/<RUN_ID>/`。
- 每段正常结束才创建 `autoreconN.subject.tar.gz` 与 `autoreconN.completed.json`；复制后读回校验 SHA。完整 subject 归档可能较大，Drive 需有足够剩余空间。软件安装树/个人 license 不进入这些归档。
- Notebook 中断但运行时仍在：先看 status 和对应 `.log`，不要重复点初始化或删除 `IsRunning`。失败/中断标记不会被程序静默抹掉。
- 运行时重置：重新执行代码/环境准备、挂载和个人许可格；选择已完成的 source run 和阶段，通过 restore 格恢复到 **新的 run ID**。恢复要求相同 FreeSurfer build、OS、配置及匹配归档哈希；归档路径经过安全检查。
- 恢复 C1 检查点后继续 C2/C3；恢复 C2 后继续 C3。中断阶段未完成的进度不承诺保留。没有任何成功检查点时，需新建 run 重做第一段。

## 实际交付格式

`structure/draft/t1_volumes_raw.csv` 按 `schemas/t1_volume_names.json` 顺序，包含：

- 68 项皮层灰质体积（每侧 34 区）；14 项皮层下体积（每侧 7 区）。
- `record_id`、`icv_mm3`、`icv_method`、`freesurfer_version`、`qc_status`。
- ICV 方法固定记录为 `FreeSurfer_eTIV_talairach_MNI305`，从 `aseg.stats` 的独立 eTIV Measure 行提取。它是基于 atlas 配准的估计量，不是把 2B 脑 mask 的体积拿来替代。

原始 `lh.aparc.stats`、`rh.aparc.stats`、`aseg.stats` 一并保留。导出器检查列名/位置、重复或缺失脑区、丘脑旧别名冲突、有限正值和 eTIV 的 mm³ 单位；不在全队列提前做 ICV 校正/缩放，这些由特征与训练方在训练折内完成。

draft 的 `handoff.structure.pending.json`/CSV 不能通过 karl 的正式入口，这是预期行为。真正审核后，`structure/accepted/handoff.json` 与 CSV 才标结构阶段 ready/pass，保留审核记录和文件哈希；`training_ready` 仍为 False，正式身份/诊断对应与其他模态尚需验证。这里的结构交接可以先于 fMRI 完成，不要求三个阶段同时就绪。

## 来源和复现边界

- 固定 karl 接口提交：`a911ab6b2120698fdf48f1936c7bf7c5c1a17a4a`；沿用其 82 列 schema 和 CSV 读取约定，不改 karl/main。
- [官方安装包、MD5、系统要求](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads)
- [8.x 安装说明与 FS_V8_XOPTS 旧流程开关](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads/rel8notes)
- [官方 recon-all 阶段划分](https://surfer.nmr.mgh.harvard.edu/fswiki/recon-all)
- [个人许可申请与条款](https://surfer.nmr.mgh.harvard.edu/registration.html)
- [eTIV 定义及 aseg.stats 格式](https://surfer.nmr.mgh.harvard.edu/fswiki/eTIV)

完整 FreeSurfer 软件、真实分割、库依赖、耗时与结果质量均尚未实跑验收。当前通过的是准备代码/解析与恢复保护测试，不能写成“2C 已完成”或“已得到 82 个真实体积”。若将来改变软件版本、模式、OS 或输入空间，需新配方和新的处理记录，不与原批次静默混合。
