# 实现与验收状态

更新：2026-11-08，分支 karl，基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。新增代码未提交、未推送；旧 AGENTS.md 和 CHG-0001 保留。以下为本轮实际完成状态，不将合成测试算作 MRI 实验。

| 模块 | 已有实现/验证 | 尚缺的真实证据 |
|---|---|---|
| 首批清单 | 五例固定配对，从原清单/participants/subjects 核对生成；35 条 pending 阶段 | 原始 MRI 本体和新 QC；训练标记仍全 False |
| 数据取用 | 新辅助脚本默认只显示单例计划，显式 execute 才调用未修改的固定下载器/完整清单 | 本轮未下载配套 ZIP 或 MRI |
| BrainIAC | 固定作者版本、严格加载、96³ 验证变换、显式 ID/哈希/维度/耗时、独立 Notebook | 真实权重/模板、目标环境验证和队友首例 QC 输入；未做真实推理 |
| Brain-JEPA | 顺序/atlas/gradient/归一化/池化配置门槛、严格加载 encoder 分支、冻结 token 表征接口、独立 Notebook | 精确图谱与映射、gradient、权重及许可、Python/CUDA 环境和真实时序；未做真实推理 |
| 结构指标 | 原始 82 体积 CSV 或 FreeSurfer stats 输入，ICV 单独保存，丘脑名称兼容检查 | 队友真实分割、ICV 方法与 QC |
| 功能指标 | 连续 160 帧检查、最低平均 FD 选窗、77 项 signed Fisher 汇总 | 双方锁定的 QC 参数、真实窗口和 450 ROI 的确切映射 |
| 特征合并 | 一对一按 record_id 连接；哈希/配方/顺序/窗口/时序来源检查；保留身份/QC/训练状态 | 同例真实四分量对齐和持久存储重启恢复验证 |
| D/S/Z/F/U/R | 六模型、offset BCE 小 MLP、L2 logistic、多输出 ridge、共享 b 与按人交叉拟合、路径概率平均 | 真实队列上验证；MLP 预算、访视策略及联合选参等仍待确认 |
| 验证框架 | 按自然人分层嵌套 CV、训练内变换、inner 阈值、outer 留出、配对 bootstrap、分折人名单审计 | 自然人/诊断时点确认、正式 QC、最终折数/repeats/调参决策；未运行正式训练或 22 配置 |
| 使用与日志 | 三个 Notebook、命令行、手工 Colab 代码包/文件指纹、单步成功/失败日志与状态报告 | 共享 Drive 路径；用户确认尚未准备 |

## 本轮验证

- **26 项 pytest 通过**：包含固定清单/未提升就绪标记、时间连续性、FC 边集合及符号/重排不变性、零方差/缺映射拒绝、哈希与覆盖保护、按 ID 合并、混合配方与跨模态窗口/ROI 拒绝、FreeSurfer/CSV 接口、Brain-JEPA 输入门槛、按人隔离、held-out 人不能改变其 b/g/变换、训练内 ICV 校正、零修正严格退化为 b、合成嵌套验证、重复预测的按人 bootstrap，以及 CLI 成功/失败和手工代码包校验。
- 首轮 19 通过、1 失败，发现通用分组启发式在小样本嵌套内层可能造成类别人数过少；已改为唯一自然人上精确分层，再映射全部访视。后续新增接口测试，最终 26 通过。
- 命令：`.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/pytest-final-2`；本机测试 Python 3.12.14，具体依赖见 `envs/tested-core-windows-py312.txt`。
- `compileall` 通过；三个 Notebook 的代码单元可解析、执行计数均为 null、输出为空。Notebook 没有在真实 Colab/MRI 上执行。
- 各执行类 CLI 的 `--help` 可用；build_pilot 已实际生成固定清单，未再次覆盖。
- 两编码器 preflight 均按预期返回 blocked/退出码 2：在本轮 core 环境与空路径模板下，分别列出 10/16 个缺项；未宣称候选 CUDA 环境可用。
- 单例下载辅助脚本只执行 plan_only，显示 sub-mindo304 的两份 MRI 和配套 ZIP 大小，没有发生 MRI 下载。
- 原 dataset_Mi 下载器、清单、subjects/cohort 的实际字节与 Git HEAD 一致，且原数据目录无修改；清单 SHA-256 为 `8c36e85113f3a5b5e853b471f664397c74ed79eca71e014cd198aa82076da0a2`。

## 下一次真实运行前

1. 双方确定 ARTIFACT_ROOT、首例交接和精确空间/图谱要求；预处理参数不虚填。
2. 准备并核验真实 checkpoint/模板/gradient，记录实际哈希、来源和许可；按 Notebook 选择独立环境。
3. 先用 sub-mindo304 的真实 T1+QC 通过 BrainIAC 单例入口，检查输出及持久存储恢复，再接同例功能分支并扩展 3–5 例。
4. 真实特征、QC、身份与诊断对应齐备前，不运行正式验证；小样本不报告可信准确率或残差有效性。

运行方法见 RUNBOOK.md；逐次改动记录见 CHANGELOG.md 的 CHG-0002。

## 2026-11-08：VS Code Colab 配置实测更新

- 已连接获授权的免费 T4 / 2026.07；实际 Python 3.12.13、Tesla T4 15360 MiB。Google Drive 经用户本人授权后重试挂载成功。
- 已校验并恢复原 63 文件源快照及 Drive 私人配置。独立 `/content/venvs/brainiac` 实际导入检查：torch 2.5.1+cu124、MONAI 1.3.2、NumPy 1.26.4；CUDA 小矩阵运算通过。该检查不使用 MRI 或模型权重。
- BrainIAC 稀疏作者代码固定为 `ba60f45bed832ee0e5683c678caeaeefe2072f0d`，保留 LICENSE。项目远端未更改。
- 环境记录：`/content/drive/MyDrive/FYP_MRI/artifacts/logs/vscode_brainiac_environment_20261108_105029_1794135029483601079.txt`。
- 实际预检：`notebooks/01_colab_preflight.ipynb` 已执行并保存，报告为 blocked；剩余 4 项：权重路径、checkpoint_sha256、template_sha256、input_recipe_confirmed。报告保存到 `/content/drive/MyDrive/FYP_MRI/artifacts/reports/brainiac_preflight_20261108_105155_1794135115660813875.json`。
- 新增可复现环境恢复脚本 `scripts/colab_setup.py`，说明见 RUNBOOK 第 8 节。临时传输/安装 Notebook 在忽略目录 `.tmp/01_authorized_colab_setup.ipynb` 中，保存实际成功输出；不上传 Git。源快照未包含后续新增的配置脚本和诊断文件，不能当作最新 Git 提交。
- 首例真实 QC、权重与精确空间输入配方仍缺；Brain-JEPA 独立环境及 ROI/gradient/权重兼容验证仍未完成。没有新 MRI/权重下载、模型推理或正式训练。上述状态更新补充早先“Notebook 未执行”的记录；02/03/04 特征 Notebook 仍未执行。

## 2026-11-08：权重与兼容检查已完成，进入首例交接边界

- 已获取正确官方预训练文件 BrainIAC.ckpt（362119240 字节）和 jepa-ep300.pth.tar（1513861285 字节），以及作者参考模板与 450×30 gradient。均存于 Drive FYP_MRI/weights，实际 SHA-256、来源、尺寸和真实验证输出见 `manifests/encoder_assets.json`；不将权重提交 Git。
- BrainIAC 严格 backbone 加载和随机 96³ 输入检查通过，有限输出 1×768。Brain-JEPA encoder/target_encoder 两分支均严格加载，通过随机 450×160 输入检查，有限 token 形状均为 1×4500×768。明确为 SYNTHETIC_ONLY，不是历史两例恢复、患者特征或分类结果。
- JEPA 独立最小推理环境使用 Python 3.12/torch 2.5.1+cu124。原 FlashAttention 2.5.5 不支持 T4；项目以精确作者源文件哈希守卫，仅替换内存中的强制 import，并运行作者已有 normal attention。作者原文件不改动，不能称为复现 A100 原训练环境。
- 实际最终资产报告：`/content/drive/MyDrive/FYP_MRI/artifacts/reports/encoder_assets_20261108_110935_1794136175552854375.json`，包含 JEPA 环境 freeze；私人配置 before/after 已版本化备份，原先浏览器配置备份未覆盖。
- `notebooks/01b_encoder_assets_check.ipynb` 已执行保存，验证两个严格加载结果、实际文件尺寸及项目源码快照校验，并运行两套预检。BrainIAC 仅缺 input_recipe_confirmed；JEPA 缺 checkpoint_key/atlas_contract/normalization/pooling/recipe_confirmed，未虚填放行。
- `docs/ENCODER_INPUT_SPEC.md` 与 `docs/TEAMMATE_HANDOFF_REQUEST.md` 给出真实输入证据、模板哈希/方向、最小首例交接和可转发说明。`configs/brain_jepa_pilot_candidate.yaml` 是明确标未确认的技术候选，不自动加载，保留与作者 robust scaling/时间下采样的差别。
- 首例真实 QC 和双方输入配方确认尚未完成；完整 ROI 行序、Schaefer17→7 映射、未公开核实的预训练 robust 参数及 JEPA 许可范围仍有证据缺口。没有患者 MRI 下载、真实特征提取、分类训练、付费或 GitHub 远端修改。
