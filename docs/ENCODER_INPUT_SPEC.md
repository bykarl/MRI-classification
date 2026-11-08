# 编码器输入证据与首例交接要求

核对日期：2026-11-08。本文区分作者实现、项目候选方法和真实 QC 验收；不代替双方对预处理配方的确认。历史试跑资料不可用，不把截图当可运行代码。

## BrainIAC：已核实的作者输入

- 代码固定 `ba60f45bed832ee0e5683c678caeaeefe2072f0d`。
- [quickstart](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/src/quickstart.ipynb) 指定 `BrainIAC.ckpt`。权重目录另有 `vit_mci.ckpt` 等下游头，本项目不使用它们替代冻结编码器。
- [空间预处理脚本](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/src/preprocessing/mri_preprocess_3d_simple.py) 的顺序是 N4 → 把参考模板重采样到 1 mm → Euler3D 刚体配准 → HD-BET（fast，tta=0）。配准用 Mattes MI、随机 1% 采样及多分辨率。该脚本不是本项目已验收流水线；未执行它，不能假设其随机性、插值及异常处理已经满足项目 QC。
- 作者参考文件为 `src/preprocessing/atlases/temp_head.nii.gz`，固定 Git blob `24ec2d4f133c871002f0a57d3cb3dbdb74e9c93b`。这只确定源文件，不证明队友输出已使用该模板；交接须记录模板实际 SHA-256、空间、方向、体素、变换及配准图。
- 参考模板已实际获取，SHA-256 `d8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e`；实测 170×206×162、1 mm、LAS 轴向。不能仅凭重定向后仍显示 1 mm 就视为编码器张量顺序一致：当前适配器不自动执行 RAS/LAS 重定向，双方须约定保存顺序并核验实际图像与模板覆盖。
- 模型侧按作者验证变换处理单例 3D 脑提取 NIfTI：单通道、trilinear resize 到 96³、非零体素强度标准化。冻结 ViT-B 的作者第一 token 输出为 768 维；不使用 MCI 分类 logits，也不额外推断 token 的语义。
- 82 项体积与 ICV 走保留高分辨率的 FreeSurfer 处理链，不从 96³ 编码器输入计算体积。已做的步骤要逐项记录，避免重复 N4/配准/脑提取。
- 保留作者 [Research-Only LICENSE](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/LICENSE) 与 Tak et al. 2026 引用；权重不进项目 Git。

## Brain-JEPA：已核实与仍需确认的边界

- 代码固定 `b1dfa93eb331d1e70476446b06fc8a1ac3c92345`。[作者预训练目录](https://drive.google.com/drive/folders/1LPcOxSpzaGfyCzqHtlMiDfaSCtEjYSfB) 的文件为 `jepa-ep300.pth.tar`；不是下游 NC/MCI 分类头。
- [数据实现](https://github.com/Eric-LRL/Brain-JEPA/blob/b1dfa93eb331d1e70476446b06fc8a1ac3c92345/src/datasets/ukbiobank_scale.py) 拼接 Tian S3 3T 的 50 行皮层下时序，再拼 Schaefer17n400p 的 400 行皮层时序。代码保留各 CSV 的原行序，仓库没有给出这两份输入 CSV 的完整 label_name 表。因此仍须逐行核对实际 ROI 名称/标签、左右顺序、图谱版本/空间/分辨率与 gradient 的行对应，不能只看 ROI 个数或自行按数字排序。
- [公开 gradient](https://github.com/Eric-LRL/Brain-JEPA/blob/b1dfa93eb331d1e70476446b06fc8a1ac3c92345/data/gradient_mapping_450.csv) 实测为 450×30，有限值；SHA-256 `c9bc667e49aae442e12607bee8be86c31c330f2844cf72e7c84b16de312ed007`。模型按输入文件的全部 30 列建立映射；不要擅自截成三列。450 行本身不证明与新图谱顺序一致。
- 作者 [预训练配置](https://github.com/Eric-LRL/Brain-JEPA/blob/b1dfa93eb331d1e70476446b06fc8a1ac3c92345/configs/ukb_vitb_ep300.yaml) 是 450×160、patch 16、`add_w=mapping`，`downsample=true`、`use_standatdization=false`（沿用作者拼写）。该设置走预训练群体的 ROI median/IQR scaling，并进行时间采样。公开仓库/当前检查的预训练目录未找到 `normalization_params_train.npz`；不能在整个本项目队列上重新估计后缓存。
- 本项目连续 160 帧窗口与作者的下采样不同，应明确作为项目输入方案记录，保存完整时序及连续原始帧索引，不把删帧后不连续片段拼接成窗口。
- 单样本全张量 mean/sample-std 标准化是作者提供的另一条代码路径，但不是上述预训练配置的同义替换。若采用，须与冻结权重配方、ROI 契约和项目分析方案共同确认，并使用新的配方版本；当前配置保留未确认状态。
- 作者下游实现同时支持第一 token 和全 token 平均（全局平均还可接额外 LayerNorm）。本项目不套用下游分类头；需要明确提取 encoder/target_encoder 哪一分支，以及池化规则。不将技术上可运行当作方法已锁定。
- 原始模型无条件 import FlashAttention 2.5.5；[该版本硬件说明](https://github.com/Dao-AILab/flash-attention/tree/v2.5.5) 不支持 T4。项目 `jepa_compat.py` 只在内存中移除这条强制 import 并为误调用 flash 路径设置报错，使用原有 `attn_mode=normal`；作者原文件不改动，SHA-256 固定核验。该方案采用独立最小推理环境，不等同于复现作者 A100 训练环境或证明两 attention 后端逐位一致。
- 固定作者提交的根目录没有 LICENSE。保留 Dong et al., NeurIPS 2024 / arXiv:2409.19407 引用，记录许可尚未明确；不擅自标成 MIT，不在项目 Git 分发作者源码或权重。

## 首例交接即可推进的工作

首选 `sub-mindo304_ses-placebo`，双方先核对实际 session；如果该例 QC 不通过，保留失败记录并换例，不将其预设为合格。最小 T1 交接可以先于 FreeSurfer 和 fMRI 完成：

1. 已通过人工 QC 的预处理 T1 NIfTI、brain mask、配准变换和 QC 图。
2. 扫描 ID/session、原始输入 SHA-256、源空间/方向/体素/形状、实际模板 SHA-256；各处理软件版本及参数、处理顺序、QC 审核人和结论。
3. 按 `configs/handoff.example.json` 建立 `handoff.json`，各文件写相对路径与实际哈希。只有实际通过 QC 的阶段标 ready/pass；其他阶段保留 pending。

随后分别交付：82 项原始脑区体积与 ICV/FreeSurfer 版本；完整 `[T,450]` ROI 时序、逐列 ROI 顺序/网络映射、头动/去噪记录、连续 160 帧窗口及原始索引。FC77 与 Brain-JEPA 使用同一窗口，77 项的 Schaefer17→7 映射仍需逐 ROI 明确，不能替换为另一套未核验的 400 区图谱。

T1 的输入配方需双方确认后，才可设 `input_recipe_confirmed=true`。Brain-JEPA 仍需图谱/行序、标准化、时间采样及池化/分支的联合确认，不能由权重下载或合成 smoke test 自动设 `recipe_confirmed=true`。小规模技术试跑不产生可信分类性能或残差有效性结论。

## 可供双方审阅的 Brain-JEPA 技术试跑候选

候选为：冻结 `encoder` 分支、作者普通 attention、同 FC 的连续 160 帧、单窗口全张量 sample-std 标准化、raw token 平均得到 768 维。它避免在本项目全队列拟合缩放器；但与作者预训练 robust scaling/下采样设置存在明确差别，不能据此声称忠实复现预训练输入或性能。

该候选记录在 `configs/brain_jepa_pilot_candidate.yaml`，`recipe_confirmed=false`、图谱契约未填；不是自动运行的默认正式方案。若能获得与预训练一致的 ROI robust 参数及确切行序，应先复核配方并新建版本。若双方选择另一分支/池化，同样先锁定并记录，禁止根据外层留出标签挑选。
