# MRI 项目文件说明与换设备指南

核对日期：2026-11-08。根据本机实际文件、Git 工作区、GitHub 分支提交和已保存的 Colab 验收输出编写。本文初稿为首次发布前的盘点；用户随后已授权提交并推送 `karl`。以下示例本身不会执行操作，实际发布结果以当前远端 `karl` 和 Git 提交历史为准，不能把初次盘点的旧 SHA 当作永久最新版本。

## 1. 先回答：代码到底保存在哪里？

**建议把 GitHub 的 `karl` 分支作为代码同步入口，把 Google Drive 作为权重和结果的持久存储；Colab 负责运行。三者不能互相替代。**

| 位置 | 现在实际保存的内容 | 换设备时如何使用 |
|---|---|---|
| 本机 `D:\finalProject\MRI-classification` | 最新开发代码、说明、配置模板、测试、本地 Notebook 及保存的验收输出 | 尚未推送的修改不会自动出现在另一台电脑 |
| GitHub `bykarl/MRI-classification` 的 `karl` | 已提交且成功推送的源码/文档版本；首次发布前的旧基准见下节历史快照 | 另一台设备 clone/pull，并核对最新远端提交；本地未推送的修改不会同步 |
| Colab `/content/MRI-classification` | 当前运行时的原 63 文件代码快照及 6 个文件的已核验源码增补 | 仅是运行副本，不是完整最新本地开发目录；会话消失后不能靠它恢复项目 |
| Colab `/content/venvs/brainiac`、`/content/venvs/brain_jepa` | 两套独立 Python 环境及安装的依赖 | 属于临时运行时，新的运行时需要重建，不能把“曾装成功”当作新会话已安装 |
| Drive `/content/drive/MyDrive/FYP_MRI` | 两套权重、参考模板、gradient、环境记录、报告、私人配置版本备份及部分源码修改前备份 | 使用同一 Google 账号重新挂载后读取；没有把所有最新项目源码自动保存进去 |
| 最早网页 Colab Notebook | 该网页 Notebook 的代码单元/输出 | 不等于当前 VS Code 全部文件。VS Code 中保存的本地 `.ipynb` 不会因此自动上传 GitHub/Drive |

Google 官方说明：Notebook 文件与运行它的虚拟机、安装库及临时文件不是同一份存储；运行时可能被回收。见 [Colab FAQ](https://research.google.com/colaboratory/faq.html)。

### 首次发布前只读核对的 Git 状态（历史快照）

- 本地分支：`karl`，跟踪 `origin/karl`。
- 本地 HEAD、GitHub `karl`、GitHub `main` 均为 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。
- 远端核对命令：`git ls-remote --heads origin refs/heads/karl refs/heads/main`。
- `README.md` 有未提交修改；新增的代码、配置、文档、Notebook 等目录仍为未跟踪状态。这表示文件已保存在本机，但还没有进入 Git 提交，更没有上传 GitHub。
- 本文及后续修改也只有在完成提交/推送后才会出现在另一台设备；上述提交号是本次盘点时的快照，后续以实际 `git log` 和 `CHANGELOG.md` 为准。

## 2. 总目录：哪些属于仓库？

```text
D:\finalProject\
├── PROJECT_STATUS.md             本机项目背景/进度历史；在仓库外
└── MRI-classification\           实际 Git 仓库、日常工作目录
    ├── PROJECT_GUIDE.md          本说明书
    ├── README.md                 简短项目入口
    ├── AGENTS.md                 协作、分支、日志规则
    ├── CHANGELOG.md              每次改动、验证和回退记录
    ├── pyproject.toml            Python 项目与测试配置
    ├── .gitattributes            固定数据清单的字节/换行规则
    ├── .gitignore                不应提交的文件规则
    ├── configs\                 路径、试跑、交接、验证配置
    ├── dataset_Mi\              原有数据索引、分发清单和历史审计
    ├── docs\                    操作说明、接口、方法与交接说明
    ├── envs\                    依赖版本清单
    ├── manifests\               技术试跑名单、状态模板和实际资产清单
    ├── notebooks\               按阶段使用的 Notebook
    ├── schemas\                 列名、顺序和图谱契约规范
    ├── scripts\                 可执行的操作入口
    ├── src\mri_pipeline\        核心计算与模型实现
    ├── tests\                   合成/负例验证
    ├── .git\                    Git 内部记录
    ├── .venv\                   本机测试环境，忽略
    ├── .tmp\                    临时审计/传输/试验材料，忽略
    └── .pytest_cache\           测试缓存，忽略
```

**仓库外的 `D:\finalProject\PROJECT_STATUS.md` 不会被本仓库的 `git add` 收进去。** 本说明书的当前状态摘要、仓库内 `docs/IMPLEMENTATION_STATUS.md` 与 `CHANGELOG.md` 可随代码同步。若要带走仓库外的完整历史，请另行复制；不要以为推送仓库就已同步父目录。

下面逐项说明项目文件。`.git`、环境、第三方安装包和自动缓存按用途归类，不枚举其中成千上万个机器生成文件；它们不是项目源代码。

## 3. 根目录文件

| 文件 | 用途与使用方式 |
|---|---|
| `PROJECT_GUIDE.md` | 第一次接手、换电脑时先看；包含文件地图、保存位置和同步流程 |
| `README.md` | 简短导航和当前状态摘要，不代替完整进度或验收报告 |
| `AGENTS.md` | 要求在 `karl` 工作、保留已有修改、每次改动追加日志；不是授权自动推送或训练 |
| `CHANGELOG.md` | 追溯改了什么、为何改、实际运行过什么、有哪些限制、如何回退；旧记录不静默改写 |
| `pyproject.toml` | 包名、Python 版本要求、核心依赖、`src` 包发现规则和 pytest 配置 |
| `.gitignore` | 排除环境、缓存、私人配置、原始 MRI、模型权重等；不是自动备份机制，也不会把已跟踪文件自动移出 Git |
| `.gitattributes` | 对 `dataset_Mi/**` 禁用平台换行转换，保持固定清单字节及哈希稳定 |

## 4. `configs/`：配置、模板和未确认的方案

| 文件 | 做什么 | 当前边界 |
|---|---|---|
| `paths.example.yaml` | 代码、数据、结果、作者仓库和权重路径模板 | `null` 是待填字段，不是可运行路径；复制为私人 `paths.local.yaml` 后填本人的实际路径 |
| `pilot.yaml` | 数据基准/清单哈希、试跑特征版本、两编码器设置与 fMRI QC 参数模板 | 默认配方确认标志关闭；不要直接改为 true 绕过验收 |
| `brain_jepa_pilot_candidate.yaml` | 可供审阅的 JEPA 技术试跑候选：encoder、普通 attention、单窗口标准化、raw mean pooling | 不自动加载；与作者预训练 robust scaling/下采样存在差别，`recipe_confirmed=false` |
| `handoff.example.json` | 队友单例交接格式：T1/体积/fMRI 各阶段的状态、QC、文件及哈希 | 使用真实文件、审核人和结论填写；未完成阶段继续 pending |
| `validation.example.yaml` | 正式嵌套验证的折数、重复次数、模型预算和方法决策模板 | 当前不用于 3–5 例技术试跑；不默认启动正式训练 |

`paths.local.yaml`、`pilot.local.yaml`、`validation.local.yaml` 属于各运行环境的私人配置，不应提交 Git。目前本机仓库没有实际 `*.local.yaml`；它们在 Colab 中，Drive 有备份。另一台设备的本地路径可以不同，不能盲目复制 Windows 盘符。

## 5. `dataset_Mi/`：数据索引，不能当成已下载的 MRI 或已验收队列

保留原目录不改动。当前保留 209 个公开 ID、406 份 T1 和 208 份 BOLD；MRI 本体主要在 Releases，克隆仓库不会自动下载。公开 ID 不自动等于独立自然人。

| 文件 | 用途与注意点 |
|---|---|
| `README.md` | 原有数据分发说明、数量、目录和下载方法；有历史身份合并断言，见下方冲突提醒 |
| `GUIDE.md` | 原有整理/配对/QC 限制说明；不是新流程验收证明 |
| `download_dataset.py` | 当前正式下载器，按固定清单核验大小和哈希；不能与历史 Release 旧下载器混用，没有 `--subject`/`--ids` 参数 |
| `dataset_manifest.json` | 固定分发清单：各文件的来源、大小、路径和哈希，下载/恢复的依据 |
| `subjects.csv` | 209 个保留 ID 的人口学、标签、扫描数和影像路径索引；含 MoCA 不表示主实验可使用 MoCA |
| `cohort.csv` | 56 条初筛候选，**不是最终训练名单**；`training_ready` 尚未通过正式验收 |
| `ids/CN.txt` | 当前保留的 CN 公开 ID 列表 |
| `ids/MCI.txt` | 当前保留的 MCI 公开 ID 列表 |
| `rawdata/participants.tsv` | 本分发子集的参与者元数据表，不是患者级身份映射证明 |
| `rawdata/participants.json` | 对参与者表字段的解释 |
| `rawdata/dataset_description.json` | 数据集来源、描述、许可/引用等元数据 |
| `qc/all_candidates.csv` | 既有配对/运动/QC 候选及排除原因表；历史初筛记录，不能当作本轮已完成预处理 |
| `qc/subject_review.csv` | 按公开 ID 汇总的审阅状态、运动指标和待核查项 |
| `qc/file_audit.csv` | 既有逐影像完整性/几何/头信息检查；其中 `exists=True` 是历史审计，不代表当前设备存在影像 |
| `provenance/removed_ids.csv` | 历史删除→保留 ID 映射，仅供追溯；不是本轮重新证实的自然人对应关系 |
| `provenance/selection.json` | 当时来源、选择规则、数量变化和证据限制 |

**已知来源冲突仍保留：** `dataset_Mi/README.md`、`GUIDE.md`、`provenance/selection.json` 的历史内容称相同数字、不同前缀曾按“用户确认”合并；当前用户要求未获证据前不据数字合并，也不认定 209 个 ID 均为独立自然人。本轮没有修改既有分发、追加合并或把冲突宣布解决；正式按人分组前仍须核查。

未来按清单下载后，`rawdata/sub-*/ses-*/anat|func/` 和 `qc/motion/` 才会出现对应实际文件；当前说明不是批量下载授权。

## 6. `docs/`：长说明和交接依据

| 文件 | 什么时候看 |
|---|---|
| `RUNBOOK.md` | 操作入口、环境、特征执行、验证门槛、Colab 恢复和资产验收流程 |
| `IMPLEMENTATION_STATUS.md` | 区分代码已实现、合成测试通过、真实环境检查通过、真实数据尚未完成；后附更新会补充早期状态 |
| `data_contract.md` | 队友交付的目录、`handoff.json`、82 体积/ICV、ROI 时序/窗口、输出字段与严格连接规则 |
| `decisions.md` | 已保留方案、候选实现、未决方法与来源冲突；不要把候选配置当作双方已批准 |
| `ENCODER_INPUT_SPEC.md` | BrainIAC/JEPA 作者输入证据、模板、梯度、归一化/池化/ROI 待决项和 T4 兼容边界 |
| `TEAMMATE_HANDOFF_REQUEST.md` | 已整理的最小首例交接请求，可由你转发；并未自动发送给队友 |

已提交报告和协作规范仍分别用于确认研究方案、接口/本周安排；本仓库文件确认实际实现。它们未出现在当前仓库文件清单中，克隆不会自动带回原 PDF/协作规范。

## 7. `envs/`：环境依赖版本

| 文件 | 用途与状态 |
|---|---|
| `core.txt` | NumPy/SciPy/scikit-learn/YAML 等核心特征、分类和测试依赖 |
| `tested-core-windows-py312.txt` | 本机 Python 3.12 核心测试环境的实际依赖记录；不是 Colab GPU 环境 |
| `brainiac.txt` | BrainIAC 冻结推理依赖；本次独立 T4 环境导入、严格加载和随机输入检查通过 |
| `brain_jepa.txt` | 作者原训练环境依赖参考；含 FlashAttention 2.5.5，不能直接当作 T4 可用安装单 |
| `brain_jepa_t4.txt` | 项目独立最小 JEPA 普通 attention 推理环境；实际加载和随机输入检查通过，不冒充 A100 原训练环境 |

不要把本机 `.venv` 复制到另一台设备当可移植安装包，也不要把所有依赖都装进同一个 Notebook 宿主解释器。环境清单用于重建；版本清单不是已经安装的环境本体。

## 8. `manifests/`：名单、状态和资产记录

| 文件 | 用途 |
|---|---|
| `pilot_subjects.csv` | 固定五例技术试跑候选及路径；身份/QC 未确认，不能用作正式分类队列 |
| `processing_status.csv` | 5 例×7 阶段的初始 pending 状态模板；不是随运行自动更新的实时进度表 |
| `encoder_assets.json` | 本次真实获取的两权重/模板/gradient 的来源、大小、SHA-256，严格加载和合成检查结果及代码版本 |

实时状态要从真实运行事件用 `scripts/report_status.py` 生成新报告，不把模板中的 pending 手工改成成功来冒充运行。

## 9. `notebooks/`：交互入口，不要无差别 Run All

| 文件 | 内容 | 实际执行状态 |
|---|---|---|
| `00_runtime_check.ipynb` | Python/GPU/目录检查；后由官方扩展追加 Drive 挂载单元 | 已执行，保存 T4 与挂载输出；挂载单元可能要求本人授权 |
| `01_colab_preflight.ipynb` | 环境配置后的 BrainIAC 缺项检查及唯一报告生成 | 已执行；保存的是当时权重准备前的 4 项缺项，属于历史状态 |
| `01b_encoder_assets_check.ipynb` | 读取最终资产报告，验证两个编码器合成检查并运行当前两套预检 | 已执行；最新验收入口，仍报告真实配方门槛 |
| `02_brainiac.ipynb` | 真实单例 T1 冻结特征提取入口 | 尚未执行真实 MRI，需已验收交接与配置 |
| `03_brain_jepa.ipynb` | 真实单例 ROI/梯度/权重/配方检查及 JEPA 提取入口 | 尚未执行真实 fMRI，仍有配方与 ROI 门槛 |
| `04_features_models.ipynb` | 特征合并和后续模型接口说明 | 真实特征/分类未执行，不能拿当前五例报告可信准确率 |

Notebook 在 VS Code 中按 Ctrl+S 保存到本地文件后，仍需 Git commit/push 才会同步另一台电脑。保存输出前检查是否有私人路径/敏感信息；目前保存的验收输出不含患者影像或真实患者特征。

## 10. `schemas/`：列名和对应顺序

| 文件 | 用途 |
|---|---|
| `t1_volume_names.json` | 固定 82 项 T1 体积输出列名和顺序；ICV 另存 |
| `fc77_names.json` | 固定 77 项功能连接汇总名称和顺序 |
| `roi_order.example.tsv` | ROI 顺序表的字段模板；目前只有表头，不是已核验的 450 行图谱 |
| `atlas_contract.example.json` | 图谱名称/空间/哈希、ROI 标签顺序、gradient 哈希的契约模板；`confirmed=false`，不能据此启动真实 JEPA |

## 11. `scripts/`：日常执行入口

| 文件 | 做什么 | 是否会产生外部/计算操作 |
|---|---|---|
| `build_pilot.py` | 从保留的固定数据索引生成五例候选清单 | 写本地清单；不下载或训练 |
| `download_pilot.py` | 针对一条真实 record_id 的独立下载辅助，复用当前固定清单 | 默认只展示计划；只有显式 `--execute` 才下载，不能误认为原下载器拥有该参数 |
| `preflight.py` | 检查路径、依赖、权重/配方字段及源码快照 | 不安装、不下载、不推理；blocked 退出码 2 是预期门槛 |
| `colab_setup.py` | 原有代码 ZIP 恢复、私人配置恢复、BrainIAC 独立依赖及固定作者代码准备 | 安装依赖/获取作者代码并写日志；针对既定 ZIP/旧基准，不是任意新提交的一键恢复器 |
| `prepare_encoder_assets.py` | 获取两套官方权重、参考模板/gradient，准备 JEPA 环境、严格加载及随机输入检查、配置版本备份 | 有依赖/权重下载和合成前向；不下载参与者 MRI、不训练，不自动确认真实输入配方 |
| `run_features.py` | 执行单例 brainiac/structure/fc/jepa 阶段，校验 handoff/QC/哈希并写成功或失败事件 | 具备真实输入后会进行相应计算/推理；必须显式选择阶段 |
| `merge_features.py` | 按 record_id 严格连接特征，检查来源、配方、窗口和缺失 | 写新汇总特征，不凭行号拼接 |
| `report_status.py` | 从不可变运行事件生成新的状态 CSV | 写新状态报告，不覆盖初始模板冒充进度 |
| `evaluate.py` | 正式按自然人分组的嵌套验证入口 | 会训练分类器/残差相关模型；当前技术试跑不启动 |
| `package_code.py` | 打包 Git 跟踪及未忽略的新源码，附分支/基准和逐文件哈希 | 写 ZIP；不提交/推送，生成包不代表 GitHub 已更新 |

## 12. `src/mri_pipeline/`：核心实现

| 文件 | 职责 |
|---|---|
| `__init__.py` | 包入口；导入时不自动下载、推理或训练 |
| `io.py` | 配置/CSV/JSON 读写、哈希、路径越界保护、有限数值检查、环境记录和不覆盖式特征保存 |
| `manifest.py` | 从固定数据清单建立 pilot 记录，不擅自补自然人身份或 QC |
| `structure.py` | 读取 FreeSurfer stats 或约定体积 CSV，输出 82 原始体积和单独 ICV，不做全队列校正 |
| `fmri.py` | 在明确 QC 掩码上选择连续窗口、校验 ROI 表、计算 signed Fisher FC77；不替双方决定头动阈值 |
| `encoders.py` | 冻结 BrainIAC/JEPA 适配、严格权重/源码/输入门槛、转换、提取及运行信息 |
| `jepa_compat.py` | 对精确哈希匹配的作者模型只在内存替换强制 flash import，保留 normal attention 原运算及原作者文件 |
| `features.py` | 按记录键连接、拒绝混合配方/窗口/错位数据，核验正式队列资格 |
| `models.py` | D/S/Z/F/U/R、共享基础 b、岭回归 g、残差/修正 MLP、训练内变换、按人交叉拟合及嵌套验证；尚无真实分类结果 |

这里有算法代码不表示实验已经完成。当前程序测试及编码器随机输入检查不能代替真实空间 QC、身份核查或外层验证。

## 13. `tests/`：程序验证，不是论文结果

| 文件 | 验证内容 |
|---|---|
| `conftest.py` | 显式 SYNTHETIC 的假数据、ROI 表等测试夹具，不使用真实 MRI |
| `test_features.py` | 连续帧、FC、体积、哈希/交接、特征错位/配方混用及正式资格门槛等 |
| `test_models.py` | 按人留出、训练内拟合、ICV、offset MLP、嵌套验证隔离与按人配对 bootstrap 等 |
| `test_cli.py` | 合成端到端 CLI、失败日志、打包与快照校验 |

最近一次核心回归为 26 项通过；两编码器的真实权重严格加载/随机输入检查是另外的 Colab 技术验收。二者均不代表有 CN/MCI 准确率结果。

## 14. 隐藏目录与临时材料：不应上传 GitHub

| 目录/文件 | 当前内容与用途 | 换设备怎么办 |
|---|---|---|
| `.git/` | 本地 Git 历史、索引、分支/远端配置等内部文件 | 正常 clone 自动建立，不手工复制/编辑内部文件 |
| `.venv/` | 本机 Windows Python 3.12 核心测试环境 | 按依赖清单重建；不提交 |
| `.pytest_cache/`、各处 `__pycache__/` | 测试缓存和 Python 字节码 | 自动生成，不作为项目成果或备份 |
| `.tmp/mri-colab-code.zip` | 最早的 63 文件手工传输包，SHA-256 `fc84003274d0c9ed679a63ecc2d60c694a066fddf050075a64f6a1693782ca74` | **已落后于当前源码**，不要用它替代最新 karl 或盲目覆盖新目录 |
| `.tmp/01_authorized_colab_setup.ipynb` | 本次独立环境安装用的临时 Notebook，内嵌旧 ZIP 和当时脚本，保存成功输出 | 不自动进入 Git/Drive；需要历史材料时单独备份，不作为日常最新代码入口 |
| `.tmp/03_encoder_assets.ipynb` | 本次已执行的 6 文件源码增补及资产准备临时 Notebook | 保留审计用途，不自动同步；持久脚本和真实验收已另存仓库文件/Drive |
| `.tmp/author_audit_20261108/` | 下载的公开作者源文件、权重目录页面、梯度 CSV 等核查材料 | 忽略的临时审计缓存；关键结论/来源/哈希已写入 docs 和 manifest |
| `.tmp/pytest-*/` | 多轮测试创建的 SYNTHETIC 输入/输出和解包副本 | 不上传，不当作真实患者结果 |

本文未删除任何这些目录。旧版本/缓存不要与实际项目工作目录混淆，也不要未经检查整目录清空。

## 15. Google Drive 实际保存了什么？

Colab 挂载后的根目录：`/content/drive/MyDrive/FYP_MRI`。在 Drive 网页里对应“我的云端硬盘 → FYP_MRI”。

```text
FYP_MRI/
├── data/
│   └── dataset_Mi/                预留数据根目录；存在不等于已有 MRI
├── weights/
│   ├── brainiac/BrainIAC.ckpt     官方冻结编码器权重
│   ├── reference/brainiac_temp_head.nii.gz
│   └── brain_jepa/
│       ├── jepa-ep300.pth.tar     官方预训练 checkpoint
│       └── gradient_mapping_450.csv
└── artifacts/
    ├── logs/                      环境版本/运行记录
    ├── reports/                   预检及最终资产报告
    ├── configs/ye_boyang/         私人配置的不同版本
    └── code_updates/              本次源码增补前副本和快照元数据
```

以上是已有证据确认的路径；不是对 Drive 所有文件的实时完整盘点。未来真实特征、QC 交接会按 `data_contract.md` 写入新子目录，不把预留目录存在视为有数据。

关键版本：

- 最早私人配置：`artifacts/configs/ye_boyang/paths.local.yaml`、`pilot.local.yaml`，其中当时 checkpoint 仍为空。
- 权重填好后的配置：`artifacts/configs/ye_boyang/assets_20261108_110935_1794136175552854375/after_paths.local.yaml`、`after_pilot.local.yaml`；同目录保留 before 版本。恢复时选对版本，不要用最早空配置覆盖它们。
- 最终资产报告：`artifacts/reports/encoder_assets_20261108_110935_1794136175552854375.json`，含实际权重/模板/gradient 哈希、合成验收和 JEPA 环境 freeze。
- 原 BrainIAC 环境记录及 VS Code 新环境记录分别保留，不当成同一运行时。
- `artifacts/code_updates/asset_delta_1794136175325577452/` 只备份本次 6 文件修改前源码及快照元数据，**不是完整最新项目源码备份**。

权重已实际保存约 1.9 GB（十进制总量，另有小型模板/报告），不需要每换一台电脑就重新从作者网站下载。新 Colab 环境可读取同一 Drive 文件，仍应核验其哈希。

## 16. 换设备的日常工作流程

### 今天离开这台电脑前

1. 保存当前 VS Code 文件，确认输出/报告已写 Drive；只在 `/content` 的文件不能当作持久备份。
2. 查看 `git status`，确认分支为 `karl`；把源码、模板、依赖、文档、测试和小型来源清单纳入提交。
3. 检查拟提交文件，排除权重、MRI、私人配置、令牌/密钥、环境与缓存；不能把所有 Drive 内容上传 GitHub。
4. 在你明确决定上传后，commit 并 push 到 `origin/karl`，确认 GitHub 页面出现新提交。只 commit 不 push，另一台电脑仍拿不到。
5. 把下一步/阻塞写在 `CHANGELOG.md` 和实现状态中。`PROJECT_GUIDE.md` 是盘点快照，不会实时自动更新所有状态。

初稿编写时尚未执行第 4 步；当时询问“是否需要上传”不等同于推送授权。之后用户已明确授权提交并推送 `karl`；是否发布成功应核对实际远端提交，不能仅凭授权或本说明书判断。

### 另一台电脑第一次接手

下面是将来首次上传完成后的命令示意，不是本次已执行记录：

```powershell
git clone --branch karl https://github.com/bykarl/MRI-classification.git
cd MRI-classification
git branch --show-current
git log -1 --oneline
git status --short
```

应看到 `karl` 和刚推送的新提交。新电脑不必使用同一 Windows 盘符；打开本机实际克隆目录，先读本说明书、`CHANGELOG.md` 最新条目及 `docs/IMPLEMENTATION_STATUS.md`。

如果该电脑已有克隆，先确认没有未保存/未提交修改，再同步：

```powershell
git switch karl
git status --short
git pull --ff-only origin karl
```

有本地修改或分支分叉时先处理差异，不用 `reset --hard`、强推或直接覆盖目录。每天结束在 A 设备 push、开始在 B 设备 pull，可减少两边同时修改造成的冲突。

### 继续使用 Colab

1. 在另一设备登录你自己的同一 Google 账号；队友继续使用他自己的账号/环境。
2. 使用官方 Colab 扩展打开本地 Notebook、选择正确的已有 T4 会话；不要把 Auto Connect 自动给出的 CPU 当作原 T4。参考 [官方扩展说明](https://github.com/googlecolab/colab-vscode)。
3. 如果原服务器仍在，先检查 GPU、`/content/MRI-classification`、两个解释器和 Drive 是否存在，核对当前源码版本；不要直接 Run All 重新安装/下载。
4. 如果是新服务器，原 `/content` 和环境不能假定仍在。仅在无需付款的前提下准备 T4/2026.07，重新挂载 Drive、放入正确 karl 源码、重建两个环境并恢复**最新**私人配置，再预检。
5. Drive 授权由本人完成。路径模板中实际目录不存在时先核查挂载，不要在 `/content/drive` 下创建看似 Drive 的普通本地目录冒充持久存储。
6. 权重继续用 Drive 中的既有文件，验证哈希后复用；收到真实交接后才运行特征入口。

**当前自动恢复入口有版本限制：** `colab_setup.py` 为旧 ZIP 和旧基准编写，包含基准提交断言；`.tmp` 临时 Notebook 也嵌入旧包。不能在未来推送新提交后把它们当作任意最新版 karl 的一键恢复命令，否则会被哈希/基准检查拦住。当前日常源代码同步由 Git 完成，运行环境恢复按 RUNBOOK 的版本化流程核查；尚未验证“全新电脑+全新服务器+最新提交”的一键恢复。不要用删除目录/跳过断言绕过版本保护。

### 当天结束后

- 将必要结果写到 Drive 的新版本目录，日志/哈希随结果保存，不只留在 Colab 临时盘。
- 保存本地 Notebook 和代码，检查并提交/推送 `karl`；不能把 Colab 运行成功当作 GitHub 已更新。
- 不自动更新 `main`；不把 3–5 例技术输出当正式分类结论；不把未确认状态改为 training_ready。

## 17. 现在做到哪一步，下一步是什么？

- 已完成：本地核心实现、26 项核心测试、两套官方权重/模板/gradient、独立 T4 环境、严格权重加载与随机输入检查、来源/哈希/配置备份。
- 尚未完成：本轮首例真实预处理 QC/交接、真实特征提取、完整特征合并与正式分类/验证。
- BrainIAC 最终预检仅缺 `input_recipe_confirmed`；需要队友提供实际 T1、mask、变换、QC 图和处理记录，双方确认模板/方向/配方。
- Brain-JEPA 仍缺分支/图谱契约/标准化/池化/总配方确认；预训练 robust 参数、精确 ROI 行序/17→7 映射和许可范围有证据缺口，不能声称只要拿到任意 450 ROI 就完成。
- 换设备前先确认代码已同步到 `karl`，以免丢失开发进度；实验推进则先收同一例合格 T1，不必等整队列或全部 fMRI。

本说明书不会触发下载、训练、购买或推送。所有项目改动仍应在 `CHANGELOG.md` 留下可回溯记录。
