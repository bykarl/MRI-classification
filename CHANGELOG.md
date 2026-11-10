# 项目改动日志

本日志用于追踪文件、配置和实现的改动，辅助定位问题。记录按时间顺序追加，时间统一为 Asia/Shanghai（UTC+08:00）。Git 保留具体差异；本日志补充改动原因、验证证据和回退线索。大型运行日志与输出另存持久存储，并在对应条目引用。

## 记录规则

- 每次项目文件变更均记录，按 `CHG-0001`、`CHG-0002` 依次编号。关联文件可合并为一条，后续修复另起条目。
- 标明文件的新增、修改、删除或重命名，以及修改原因；代码、参数、依赖和输入配方变化都要记录。
- 记录变更前的 Git HEAD、分支和工作区状态；没有提交时明确写“未提交”。后续可通过 `git log -- <文件路径>` 与 Git diff 查找提交和具体差异。
- 验证结果只记录实际完成的检查；未运行、失败或待验证均如实标注。
- 保留历史条目，更正通过新条目引用原编号；回退时同样记录，不覆盖用户其他修改。

## CHG-0001 — 建立改动日志及后续记录要求

- 时间：2026-11-08 15:02（Asia/Shanghai，UTC+08:00）。
- 执行者：Codex，依据用户“记录每次改动，方便出 bug 回溯”的要求。
- 分支：`karl`，跟踪 `origin/karl`。
- 基准提交：`7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。
- 修改前状态：工作区干净；仓库中未发现已有改动日志或 `AGENTS.md`。
- 提交状态：未提交、未推送。

### 修改内容与原因

| 文件 | 操作 | 具体变化及目的 |
|---|---|---|
| `CHANGELOG.md` | 新增 | 建立本日志、首条记录及后续条目模板，保留原因、验证和回退线索 |
| `AGENTS.md` | 新增 | 将逐次记录要求写入仓库协作规则，便于后续会话持续遵循；同时保留仅在 karl 工作、不直接推送 main 的用户要求 |

### 验证与范围

- 修改前已执行 `git status --short --branch`、`git log -1 --format='%H %s'`，核对分支、基准提交和干净工作区；已搜索现有日志及协作规则，未发现同类文件。
- 修改后执行 `git diff --check`，并读取两个新文件检查记录内容、编号、基准提交和必要字段；核对工作区仅新增这两个文件。
- 本次为文档变更，未运行代码测试、预处理、编码器或训练，未下载 MRI/权重，未修改已有数据与代码。
- 日志从本条开始正式启用。此前的同步记录在仓库外 `D:\finalProject\PROJECT_STATUS.md`，未复制入仓库；不将历史报告中的试跑冒记为本次执行。

### 风险、限制与回退

- 文档不改变现有程序行为；日志依赖后续修改者按协作规则维护，并非自动捕获每次文件写入的监控程序。
- 当前两文件均未提交。如需撤销本次变更，在确认文件没有后续修改后，移除这两个新增文件即可；若已经产生后续条目，保留历史并追加撤销说明，避免丢失记录。

## 后续条目模板

以下为模板，不代表已经执行的改动。新条目追加在文件末尾，编号连续递增。

```markdown
## CHG-0002 — 简述改动

- 时间：YYYY-MM-DD HH:mm（Asia/Shanghai，UTC+08:00）。
- 执行者与请求来源：
- 分支及上游：
- 基准提交：
- 修改前工作区状态：
- 提交状态：未提交 / 实际可核验的提交号。

### 修改内容与原因

| 文件 | 操作 | 具体变化及目的 |
|---|---|---|
| 相对路径 | 新增/修改/删除/重命名 | 原因及行为变化 |

### 验证与范围

- 实际命令、输入或检查方式：
- 结果及证据位置（必要时含哈希）：
- 未执行或尚待验证的内容：

### 风险、限制与回退

- 已知风险及未解决问题：
- 只撤销本次改动、保留其他修改的方法：
```

## CHG-0002 — 建立特征、冻结编码器适配与按人验证框架

- 时间：2026-11-08 15:08–15:35（Asia/Shanghai，UTC+08:00）。
- 执行者：Codex；用户明确要求开始完成 Ye Boyang 负责的任务，并确认 Drive、权重及首例 QC 输出尚未准备。
- 分支：karl，跟踪 origin/karl；基准提交：`7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。
- 修改前状态：AGENTS.md、CHANGELOG.md 为上一任务留下的未跟踪文件，其余工作区干净。保留 AGENTS.md 和本日志 CHG-0001，原 dataset_Mi 不改写。
- 提交状态：本轮全部修改未提交、未推送；没有修改 GitHub 远端。

### 修改内容与原因

| 文件 | 操作 | 具体变化及目的 |
|---|---|---|
| `.gitignore` | 新增 | 隔离 venv、缓存、临时产物、私人配置、MRI/权重/license |
| `pyproject.toml` | 新增 | src 包布局、核心依赖与 pytest 配置 |
| `envs/core.txt`、`envs/brainiac.txt`、`envs/brain_jepa.txt`、`envs/tested-core-windows-py312.txt` | 新增 | 区分核心测试环境、两套编码器候选环境及本机实际依赖；后两编码器环境未做真实运行验证 |
| `configs/paths.example.yaml`、`configs/pilot.yaml` | 新增 | 路径模板、固定版本、未确认权重/图谱/QC 门槛，不编造实际路径或哈希 |
| `configs/handoff.example.json`、`configs/validation.example.yaml` | 新增 | 逐阶段交接及正式验证门槛；默认 pending/null/未确认 |
| `manifests/pilot_subjects.csv`、`manifests/processing_status.csv` | 新增 | 从固定清单生成五例与 35 个 pending 阶段，保留空 person_id 与 training_ready=False |
| `schemas/t1_volume_names.json`、`schemas/fc77_names.json` | 新增 | 固定 82/77 名称和顺序；ICV 另存 |
| `schemas/roi_order.example.tsv`、`schemas/atlas_contract.example.json` | 新增 | 只提供字段和未确认模板，不捏造真实 450 ROI 或 gradient |
| `src/mri_pipeline/__init__.py`、`src/mri_pipeline/io.py` | 新增 | 包版本、哈希/路径/唯一键、排他写入、环境与实现指纹、组件及总清单 |
| `src/mri_pipeline/manifest.py` | 新增 | 从未修改的固定 inventory 生成试跑记录 |
| `src/mri_pipeline/structure.py` | 新增 | 按键读取原始体积 CSV 或 FreeSurfer stats，ICV 独立；兼容丘脑旧别名，歧义时停止 |
| `src/mri_pipeline/fmri.py` | 新增 | 显式 QC 掩码上的连续窗口选择、共享窗口切片、77 项 signed Fisher FC |
| `src/mri_pipeline/encoders.py` | 新增 | 固定作者代码/权重核验与冻结推理适配；阻止未确认的 Brain-JEPA 图谱、gradient、标准化和池化 |
| `src/mri_pipeline/features.py` | 新增 | 严格按 record_id 合并，拒绝混合 schema/配方/窗口/时序，正式身份/QC 门槛 |
| `src/mri_pipeline/models.py` | 新增 | 六模型、共享 b、offset MLP、OOF h 输入、训练内编码/ICV/缩放/g，按人嵌套验证和配对 bootstrap |
| `scripts/build_pilot.py`、`scripts/download_pilot.py` | 新增 | 清单生成及独立单例下载辅助；后者默认只显示计划，保留原下载器/清单固定哈希 |
| `scripts/preflight.py`、`scripts/run_features.py` | 新增 | 缺项报告、单例执行与成功/失败事件日志；不默认执行处理或训练 |
| `scripts/merge_features.py`、`scripts/report_status.py` | 新增 | 特征合并及从不可变运行事件生成新的状态报告 |
| `scripts/evaluate.py` | 新增 | 正式验证 CLI，要求身份/诊断/QC/训练标记与折数/方法决策均确认 |
| `scripts/package_code.py` | 新增 | 为未推送代码生成手工 Colab 包及逐文件快照哈希，排除忽略产物 |
| `notebooks/02_brainiac.ipynb`、`notebooks/03_brain_jepa.ipynb`、`notebooks/04_features_models.ipynb` | 新增 | 独立单例入口和核心接口；所有运行单元未执行，无伪造输出 |
| `tests/conftest.py`、`tests/test_features.py`、`tests/test_models.py`、`tests/test_cli.py` | 新增 | 明确标注的合成样本、负例、防泄漏、CLI 和代码包测试，不使用真实 MRI |
| `docs/RUNBOOK.md`、`docs/data_contract.md`、`docs/decisions.md`、`docs/IMPLEMENTATION_STATUS.md` | 新增 | 使用步骤、交接接口、作者来源/待决方法和实际验收边界 |
| `README.md` | 修改 | 保留原标题并补充入口导航、真实输入缺口及未推送状态 |
| `CHANGELOG.md` | 追加 | 本记录；保留 CHG-0001 |
| 仓库外 `D:\finalProject\PROJECT_STATUS.md` | 修改 | 在初次盘点上补充当前实现状态及真实运行缺口，不将新代码写成已完成实验 |

### 验证、故障与修正

- 在项目 `.venv` 安装核心测试依赖，未改动全局环境。首次 ensurepip 因系统临时目录权限失败；改用项目临时目录和宿主 pip 的 --python 目标安装完成。依赖联网安装在沙箱外审核允许后执行，范围仅项目 venv，无 MRI/权重下载；随后用 bundled wheel 给该 venv 补齐 pip。部分系统临时缓存清理产生权限警告，不影响已安装依赖或测试。
- 首轮测试 19 通过、1 失败，暴露通用分组启发式导致嵌套小样本类别分布不足；改为唯一 person_id 上分层再映射全部记录，保留同人全部访视在同折。随后扩展接口与代码包测试，最终 **26 项通过**。
- 最终测试：`.venv/Scripts/python.exe -m pytest -q --basetemp=.tmp/pytest-final-2`，结果 26 passed；只训练了标为 SYNTHETIC 的小型测试模型，没有正式分类训练。
- compileall 通过，三个 Notebook 代码单元语法检查通过、执行计数为空，CLI help 检查通过；配置 YAML、schema JSON 及 82/77 列数核对通过。
- 实际验证单例 plan_only，不下载；两个 preflight 按预期 blocked/退出码 2，core 环境与空模板下分别列出 10/16 个缺项。
- 合成端到端验证包括结构/FC → 数组/哈希 → 合并 → 状态 CSV；QC 未通过时记录 failed，不产生特征。代码包每份文件可按快照哈希校验，venv/缓存不入包。
- 原下载器/清单/subjects/cohort 字节与 HEAD 一致；清单 SHA-256 固定值匹配。git diff --check 无错误（README 的平台换行提醒不改变数据清单）。

### 限制、未决项与回退

- 未运行真实 BrainIAC/Brain-JEPA；未下载 MRI、配套 ZIP 或权重；未执行全队列预处理、正式分类、22 配置或任何付费操作。未提交、未推送。
- 用户确认实际 Drive、权重和首例 QC 尚未准备。精确 atlas/ROI/gradient、模板、时序标准化/池化、许可/预训练重叠及验证折数仍待核验。联合 U/R 选参、访视策略与 MLP 预算是明确记录的候选实现，正式入口默认阻止运行。
- 候选环境不等于真实模型兼容证明；合成测试只检验实现和隔离逻辑，不支持分类准确率或残差有效性结论。
- 回退时依据本表逐项撤销本次新增文件、只移除 README 的新增说明，并保留 dataset_Mi、AGENTS.md、CHG-0001、用户其他修改及历史日志；若已有后续改动，先核对差异再追加撤销记录，不能对整个目录执行清空或覆盖。

## CHG-0003 — VS Code Colab 授权连接与真实运行时诊断

- 时间：2026-11-08 16:47–18:14（Asia/Shanghai）。
- 执行者：Codex；用户要求通过已安装的 VS Code Colab 扩展继续配置，并亲自完成 Google 授权。
- 分支：karl；基准提交仍为 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；保留前序未提交改动，未提交/推送。

### 文件与操作

- 新增 `notebooks/00_runtime_check.ipynb`：只读取 Python、GPU 与约定目录的存在性，不读取凭据、不下载数据、不运行模型或训练。
- 在 VS Code 官方 Colab 扩展 0.9.7 中完成连接（Google 授权由用户本人操作），实际执行并保存诊断单元，execution_count=1。
- 本日志追加 CHG-0003；不改写 CHG-0001/0002。三个原有特征 Notebook 的字节与前次代码包一致，未覆盖或重装原先浏览器会话的配置。

### 实际结果及限制

- VS Code 新分配的 CPU 会话为 Python 3.13.18、解释器 `/usr/bin/python3`，未检测到 NVIDIA GPU；`/content/MRI-classification`、BrainIAC 独立解释器、作者代码以及挂载后的 FYP_MRI 路径均不存在。这是新会话的诊断，不说明用户原先网页 T4 会话或 Drive 文件被删除。
- 诊断 JSON 已保存在 Notebook 输出中，源单元语法检查通过。未为纯诊断文件重跑分类测试。
- 已在扩展界面选择新 Colab Server → GPU → T4 → 2026.07；提交分配请求时被自动审批拒绝，理由是分配新 T4 服务器可能占用额度或产生计费后果，既有授权未明确涵盖这次具体分配。没有成功申请新 T4，没有购买额度或订阅；等待用户对这项具体操作的批准，不通过其他路径绕过拦截。
- 用户此前截图显示 Drive 文件夹及私人配置已建立、独立 BrainIAC 环境安装检查完成、作者代码提交已固定；这些属于原浏览器会话的用户提供证据，不能当作 VS Code 新 CPU 会话已具备相同资产。
- 真实权重选择/哈希、模板、ROI/gradient 和队友 QC 交付仍未完成；没有新的 MRI、权重下载、推理或正式训练。

### 回退

- 如需撤销诊断文件，先保留已保存的实际输出或另存副本，再仅移除该新增 Notebook；保留原三个 Notebook、现有代码、Drive 备份及历史日志。连接的 CPU 服务器未执行删除，后续释放资源须按用户意图处理。

## CHG-0004 — 免费 T4 申请结果与运行时数量限制

- 时间：2026-11-08 18:31（Asia/Shanghai）；执行者 Codex。
- 分支 `karl`；基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；保留既有改动，未提交、未推送。
- 用户明确批准仅申请无需付款的 T4、2026.07；未授权购买额度或订阅。
- 更正/补充 CHG-0003：授权后继续官方扩展的 GPU → T4 → 2026.07 流程，服务器别名使用符合长度要求的 `FYP-T4`。实际分配返回 `Unable to assign server. You have too many, remove one to continue.`，没有成功分配新 T4，未购买额度或付款。
- `notebooks/00_runtime_check.ipynb` 在既有 VS Code CPU 会话再次执行并保存，execution_count=2；仍为 Python 3.13.18、无 NVIDIA GPU，项目目录、独立环境、作者代码和挂载后的 Drive 路径均不存在。未把该输出当成 T4 验证。
- 仅修改上述 Notebook 的真实运行输出/计数及本日志。已从本地文件读回确认输出，分支/HEAD/工作区已检查；未运行推理、训练或下载 MRI/权重。
- 下一步拟移除仅运行诊断的 VS Code CPU 会话，为免费 T4 腾出名额；该操作会丢弃该会话临时文件，因此尚未执行，需用户对具体移除操作确认。原浏览器 T4 不在拟移除范围，Drive 不删除。
- 回退：如需恢复第一次 CPU 诊断输出，可依 CHG-0003 的结果另存记录；不以重置仓库或清空目录方式回退。历史日志保留。运行时数量限制解除前，GPU 配置仍未完成。

## CHG-0005 — 释放 CPU 并成功连接免费 T4

- 时间：2026-11-08 18:32–18:39（Asia/Shanghai）；执行者 Codex；分支 `karl`；基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；未提交/推送。
- 用户明确批准移除仅运行诊断的 `Colab CPU`。通过官方扩展 Remove Server 选中该唯一 VS Code CPU 会话并移除，界面随后显示 No assigned Colab servers。未操作原浏览器 T4 或删除 Drive。
- 重开诊断 Notebook，按 GPU → T4 → 2026.07，别名 `FYP-T4` 申请。该服务器成功出现在资源列表并连接 Python 内核；未购买额度、订阅或付款。账号界面仍显示未订阅、零 compute units，免费资源不保证持续可用。
- `notebooks/00_runtime_check.ipynb` 保存了新 T4 的实际诊断，execution_count=1：Python 3.12.13，`Tesla T4, 15360 MiB`；项目目录、BrainIAC 独立解释器、作者代码及已挂载 Drive 均不存在。已从磁盘读回确认 JSON 输出。该记录替代当前 Notebook 中旧 CPU 输出，旧结果保留在 CHG-0003/0004。
- 官方 Mount Google Drive to Server 命令在编辑器追加了 `from google.colab import drive; drive.mount('/content/drive')` 单元；随后运行停在 `Permit FYP-T4 to access your Google Drive files?`。挂载单元是编辑器未保存的后续变化，当前磁盘文件仍是已保存的 T4 诊断。没有代用户点击隐私授权；需用户本人完成后继续并保存。
- 本次涉及诊断 Notebook 的真实运行输出及本日志；没有 MRI/权重下载、模型推理或训练。后续仍需代码迁入、独立依赖、固定作者代码及配置恢复，不能将 GPU 连接写成所有配置完成。
- 验证：实际 GPU 查询及本地 Notebook 输出核对；git diff --check。未为连接/日志变化重复运行分类测试。
- 回退：保留历史日志；恢复 CPU 仅能另申请新会话，已释放会话的临时状态不可恢复。不得自动移除新 T4 或清空 Drive；后续释放须按用户授权范围操作。

## CHG-0006 — Drive 挂载恢复与可复现配置入口

- 时间：2026-11-08 18:42 起（Asia/Shanghai）；执行者 Codex；分支 `karl`；基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；未提交/推送。
- 用户完成 Drive 授权后，原挂载单元留下 `ValueError: mount failed`；重新执行已有挂载单元后成功返回 `Mounted at /content/drive`。该成功输出已从本地 `notebooks/00_runtime_check.ipynb` 文件读回确认。没有代操作 Google 认证或隐私授权。
- 新增 `scripts/colab_setup.py`：校验传入代码包与 karl 快照、逐文件恢复但拒绝不同内容覆盖、从现有 Drive 备份恢复私人配置、建立独立 Python 3.12 环境、安装固定 BrainIAC/core 依赖、实际 CUDA 小矩阵检查、唯一环境日志、稀疏获取固定作者代码及 LICENSE。没有 MRI/权重下载或模型推理/训练入口，不分配服务器或处理付费。
- 新增忽略产物 `.tmp/01_authorized_colab_setup.ipynb`：携带已核验的原代码 ZIP 和配置脚本，通过 VS Code 连接现有 FYP-T4 内核执行。原包 SHA-256 仍为 `fc84003274d0c9ed679a63ecc2d60c694a066fddf050075a64f6a1693782ca74`；它是旧源快照，不冒充本次新增脚本/日志也已进入原包。临时 Notebook 携带的执行脚本保留一个未使用的 shutil 导入，持久脚本已去除该导入，行为相同。
- 修改 `docs/RUNBOOK.md`：补充已授权运行时的恢复流程、既有文件保护、独立依赖安装和验收边界。
- 当前实际进度：远端输出 `Code snapshot verified: 63 files`；独立依赖安装仍在运行，尚未记录为安装/CUDA/作者代码全部通过。后续结果另追加。
- 验证：配置脚本及临时 Notebook 源单元本地语法检查通过；代码 ZIP 本地 SHA-256 核验通过；未为配置文档变化重跑分类训练测试。
- 限制/回退：首例 QC、checkpoint 与模板哈希、输入配方和 Brain-JEPA 契约仍未齐备。新增脚本可单独撤销，文档仅撤销新增第 8 节；保留原代码包、私人配置和历史日志。安装的远端环境仅限 `/content/venvs/brainiac`，没有覆盖宿主环境；不能自动删除远端环境或 Drive 内容来回退。

## CHG-0007 — BrainIAC 独立环境验收及四项资产阻塞

- 时间：2026-11-08 18:50–18:53（Asia/Shanghai）；执行者 Codex；分支 `karl`；基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；未提交、未推送。
- 补充 CHG-0006 的完成结果：临时安装 Notebook 实际 execution_count=1、无 error 输出、运行约 3 分 33 秒；63 文件校验成功，Drive 私人配置恢复成功。独立环境为 torch 2.5.1+cu124、MONAI 1.3.2、NumPy 1.26.4，Tesla T4 的 CUDA 12.4 小矩阵检查 passed。稀疏作者代码固定 `ba60f45bed832ee0e5683c678caeaeefe2072f0d`，LICENSE 存在，指定作者文件无修改。
- 实际环境日志：`/content/drive/MyDrive/FYP_MRI/artifacts/logs/vscode_brainiac_environment_20261108_105029_1794135029483601079.txt`；文件名为 UTC 时间，未覆盖既有浏览器环境日志。
- 新增并实际执行 `notebooks/01_colab_preflight.ipynb`，保存 execution_count=1、无 error 输出；调用正式 preflight，接受预期退出码 2，确认源快照校验未失败，以唯一名称保存缺项 JSON。
- 实际缺项为 4 个：`paths.brainiac_checkpoint`、`brainiac.checkpoint_sha256`、`brainiac.template_sha256`、`brainiac.input_recipe_confirmed`。报告：`/content/drive/MyDrive/FYP_MRI/artifacts/reports/brainiac_preflight_20261108_105155_1794135115660813875.json`。这是资产/配方 blocked，不是推理通过。
- 修改 `docs/IMPLEMENTATION_STATUS.md` 和仓库外 `D:\finalProject\PROJECT_STATUS.md`：追加上述真实状态，明确首例 QC 和 Brain-JEPA 未完成，保留旧状态历史。RUNBOOK 新增流程已记 CHG-0006。本次仅配置验收，不更新 cohort/training_ready，也不执行 MRI/权重下载、推理或分类训练。
- 验证：从磁盘读回安装及预检 Notebook 的真实输出，两个 Notebook 均无 error；新增脚本/预检单元语法检查通过；git diff --check 无错误（仅已有 README 换行提醒）；分支/HEAD/工作区核对通过。02/03/04 真实特征 Notebook 未执行。
- 审计哈希：最终 `scripts/colab_setup.py` SHA-256 `fcc94464bb309e3658c0576458faef87828c75acc39e36dbd3d405b63c37133b`；已保存输出的 `.tmp/01_authorized_colab_setup.ipynb` SHA-256 `0f68aa680cd2aa0049f3219e1a31e9a8ddc6d4eaef7a8c3dbcd aa759ab764b99`（去掉此排版空格为完整哈希）。
- 回退：新增预检 Notebook 可单独撤销，状态文档只撤销本次追加节，历史日志仍保留；不要自动清空服务器/Drive、覆盖私人配置或重置整个仓库。免费 T4 会话仍连接，不能保证持续保留；持久环境版本日志和预检报告已写 Drive。缺少 checkpoint/模板及真实 QC 时，下一步为核定资产和交接，不启动模型训练。

CHG-0007 哈希格式补充：临时安装 Notebook 的连续 SHA-256 为 `0f68aa680cd2aa0049f3219e1a31e9a8ddc6d4eaef7a8c3dbcdaa759ab764b99`，以本行连续值供机器校验。

## CHG-0008 — 官方资产准备与 Brain-JEPA T4 普通 attention 适配

- 时间：2026-11-08 19:00 起（Asia/Shanghai）；执行者 Codex；分支 karl；基准 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；未提交/推送。用户明确要求继续做到需要队友 QC 交付的步骤；授权范围含此前已提出的官方权重获取核验，仍不训练、不批量下载参与者 MRI、不付费。
- 新增 `scripts/prepare_encoder_assets.py`：仅获取实际观察到的官方 BrainIAC.ckpt（362119240 字节）、作者参考模板、公开 gradient 与 JEPA 预训练 checkpoint（1513861285 字节）；流式下载、固定大小检查、SHA-256、模板 Git blob/gradient 固定哈希验证，不覆盖不同的已有文件。保留失败 partial 供排查；不静默删文件。加载测试明确标 SYNTHETIC_ONLY，不使用患者数据。
- 新增 `src/mri_pipeline/jepa_compat.py`、`envs/brain_jepa_t4.txt`；修改 `src/mri_pipeline/encoders.py`、`scripts/preflight.py`、`configs/pilot.yaml`：作者 FlashAttention 2.5.5 官方不支持 T4，而作者已有普通 attention 实现。通过精确 SHA-256 守卫，仅在内存中替换无条件 flash import；误调用 flash 直接报错，模型计算/参数名不改，作者原文件不改。配置需显式 `normal_no_flash` 才选择该路径；默认不自动确认科学输入配方。preflight 按所选后端检查实际依赖，普通 attention 不虚要求 timm/flash 训练依赖。
- 新增 `docs/ENCODER_INPUT_SPEC.md`：明确作者输入证据、BrainIAC 空间参考、JEPA 450×30 梯度/实际行序证据缺口、预训练 robust scaling 参数未公开核实、连续帧与作者下采样差别、池化与分支未定、许可来源和最小首例交接。未编造 450 行 ROI 表或把方法冲突视为已解决。
- 新增忽略产物 `.tmp/author_audit_20261108/`：固定版本作者代码、公开权重目录页面和小型 gradient；仅审计缓存，不是作者权重或患者 MRI。
- 新增忽略产物 `.tmp/03_encoder_assets.ipynb`：将 6 个运行时源码变更迁入已有 Colab 根目录；预先验证旧/新文件哈希，先备份原源码和 CODE_SNAPSHOT，再更新运行时源码哈希，不伪造 Git 提交。delta SHA-256 `02614d05d02cfc3ff38432a69c8636e8a9aef310a6ee567eff0c47178de1229e`，远端已输出 SOURCE DELTA VERIFIED。原快照备份位于 `/content/drive/MyDrive/FYP_MRI/artifacts/code_updates/asset_delta_1794136175325577452`。
- 实际验证：本地 26 项测试通过（`pytest -q --basetemp=.tmp/pytest-assets-1`），脚本/兼容模块/临时 Notebook 语法检查通过。公开 gradient 实测 450×30、有限值且哈希固定；BrainIAC 单文件 range 探测 206 返回 ZIP 魔数及正确文件名/大小。
- 当前下载/真实 checkpoint 加载/合成 forward 仍在 Colab 执行，不预写通过。新独立 JEPA 环境候选为 Python 3.12、torch 2.5.1、NumPy 1.26.4、PyYAML 6.0.2；不冒充作者原训练环境。
- 回退：先保留日志/配置版本，再仅撤销列出的新模块/脚本/说明和对应局部改动。运行时源码 before 副本已持久保存；不清空整个目录，不自动删除 Drive 权重或会话。真实输入配方/ROI/QC 未确认时不能运行正式特征或分类训练。

## CHG-0009 — 官方资产及合成兼容验收完成，停在真实交接/配方门槛

- 时间：2026-11-08 19:12–19:20（Asia/Shanghai）；执行者 Codex；分支 karl；基准 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；保留前序改动，未提交/推送。补充 CHG-0008 的实际结果。
- Colab 资产准备单元 execution_count=1、无 error、约 3 分 31 秒结束。子进程标准输出未直接进入 Notebook，因此没有仅凭空输出判成功；随后单独读取已生成的真实最终资产报告并核对两套 preflight。
- 新增并执行 `notebooks/01b_encoder_assets_check.ipynb`：从 Drive 最终报告读取实际资产尺寸/哈希、严格加载/合成前向结果；验证文件存在和尺寸、源快照校验未失败。execution_count=1，无 error，完整实际输出已保存本地。
- 新增 `manifests/encoder_assets.json`：从已保存的真实 Notebook 输出解析而来，含四个资产来源/路径/尺寸/SHA-256、合成结果、代码版本与许可未明记录；没有将权重或患者数据放入 Git。
- 实际资产 SHA-256：BrainIAC `f22bdbcae26823a9d9e8aee883c6f24386ba4617339c12269848b6666cc62693`；模板 `d8eba10e9528a5212b78fb1be477d5e8229751bfec5e1e1a648dc81ff83a622e`；JEPA 预训练 checkpoint `f1726142b96b4c809a90786b79b8029b77cef0aacc231d1a357940cbec9442ac`；gradient `c9bc667e49aae442e12607bee8be86c31c330f2844cf72e7c84b16de312ed007`。checkpoint 哈希为实际下载计算值，不冒充作者发布的独立校验签名。
- 实际报告：`/content/drive/MyDrive/FYP_MRI/artifacts/reports/encoder_assets_20261108_110935_1794136175552854375.json`；私人配置 before/after 备份在 `artifacts/configs/ye_boyang/assets_20261108_110935_1794136175552854375/`，最早备份未覆盖。
- BrainIAC 严格 backbone 加载，随机 96³ 输入有限输出 1×768；参考模板实测 170×206×162、1 mm、LAS。JEPA encoder 与 target_encoder 均严格加载，随机 450×160 输入有限 token 均 1×4500×768；gradient 450×30。所有检查标 SYNTHETIC_ONLY，不是患者推理、训练、准确率或残差效果证明。
- BrainIAC 最终 preflight 缺项只有 input_recipe_confirmed；JEPA 缺 checkpoint_key、atlas_contract、normalization、pooling、recipe_confirmed。权重、模板哈希和技术后端准备没有自动将两个确认标志改为 true。
- 新增 `configs/brain_jepa_pilot_candidate.yaml`：具体的 encoder/普通 attention/单窗口 sample-std/raw mean pooling 候选，明确 recipe_confirmed=false，不自动加载，不隐瞒与预训练 robust scaling/下采样差别。
- 新增 `docs/TEAMMATE_HANDOFF_REQUEST.md`：准备供用户转发的最小首例请求，未通过工具向队友发送。修改 `docs/ENCODER_INPUT_SPEC.md` 增补实际模板轴向/哈希和候选说明；`docs/RUNBOOK.md` 补充资产准备、已执行验收与配置版本恢复注意点；`docs/IMPLEMENTATION_STATUS.md`、`docs/decisions.md`、仓库外 `D:\finalProject\PROJECT_STATUS.md` 追加新事实并保留历史未准备状态的上下文。
- `scripts/prepare_encoder_assets.py` 后续仅加强失败子进程 stdout/stderr 输出，便于回溯；该错误日志改进仅在本地最终源文件，当前已成功执行的运行时仍是 CHG-0008 delta 中的版本，未伪称两个版本哈希一致。行为与成功报告不受影响。
- 验证：26 项本地回归通过已记 CHG-0008；本次新增/更新 Python/Notebook 语法、YAML false 门槛、资产 JSON、真实输出计数/无 error 检查通过。原下载器/cohort 与原 02/03/04 Notebook 字节仍与初始 ZIP 一致，未执行真实特征 Notebook。git diff --check 无错误，仅已有 README 平台换行提醒。
- 仍缺首例真实 QC、双方空间输入配方、精确 ROI/gradient 行序及 17→7 映射；JEPA robust 参数未公开核实，许可范围仍不明确。不能将这些写成“仅等数据就已全部解决”。在审阅候选和真实交接前停在门槛，不填造 ROI 表、不改 training_ready、不跑正式分类、不付费、不改远端。
- 回退：按本条文件逐项撤销新增/追加内容，保留历史日志及 Drive 原始 before/after/资产报告；不要清空工作区或 Drive。权重已持久保存，免费服务器仍连接但会话不保证持续；本次没有自动删除新 T4。

## CHG-0010 — 文件说明书与每日跨设备同步指南

- 时间：2026-11-08 19:21–19:30（Asia/Shanghai）；执行者 Codex；分支 karl；基准提交 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`；保留全部前序未提交改动，未提交/推送。
- 用户要求逐项说明文件夹/文件用途，并解释换设备时 GitHub、Colab 与 Drive 的保存关系；本次没有将询问是否需要上传当作自动推送授权。
- 新增根目录 `PROJECT_GUIDE.md`：列出 75 个当前项目文件的用途、状态和门槛，说明隐藏目录/依赖/缓存及临时审计材料的分类；说明仓库外 PROJECT_STATUS.md 不随 Git 自动同步、网页 Notebook 与 VS Code 本地 Notebook 的区别、Drive 实际资产/配置版本、日常 commit/push/clone/pull 流程及现有恢复入口限制。
- 修改 `README.md`：添加说明书导航；修正过时的“权重/gradient 尚未准备”摘要，准确区分资产/合成检查已完成与真实 QC/输入配方/分类仍未完成。
- 只读执行 `git ls-remote --heads origin refs/heads/karl refs/heads/main`，实际两远端分支均为基准 SHA；本地 HEAD 同值。工作区新增代码未提交、未推送；没有更新 main/karl 远端或 Git 索引。
- 明确保留的限制：当前 Colab 是原 63 文件快照及 6 文件增补，不是完整最新本地目录；Drive 源码 before 备份不是完整仓库；`.tmp` 旧 ZIP、临时 Notebook 与 colab_setup 的固定旧基准不能冒充任意新提交一键恢复。尚未验证“新设备+新运行时+未来最新提交”自动恢复，不给出虚假可用保证。
- 依据：实际文件清单、配置、CSV 表头、运行入口、Git 状态、已保存验收输出及 Google 官方 Colab FAQ/官方 VS Code 扩展文档；既有数据身份合并断言与当前用户约束的冲突在说明书中指出，没有自行解决或改写 dataset_Mi。
- 验证：程序核对当前 75 个非忽略项目文件的名称均在说明书中出现；Markdown 代码围栏、尾随空白和相对链接检查通过；git diff --check 无错误，仅已有 README 的平台换行提醒。纯文档修改未重跑模型测试、下载或训练。
- 回退：移除新增 PROJECT_GUIDE.md、撤销本次 README 导航及摘要改动；保留前序 README 改动、所有源码/数据/配置/结果及历史日志。未改变运行环境或删除缓存。

## CHG-0011 — 用户授权发布至 karl：提交前审阅与验证

- 时间：2026-11-08 19:30 起（Asia/Shanghai）；执行者 Codex；当前分支 karl、跟踪 origin/karl；基准 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。用户明确要求“将代码提交并推送 karl 分支”，不推送 main，不强推。
- 发布范围：保留并纳入此前已完成、尚未提交的 MRI 核心实现、执行入口、配置模板、环境清单、合成测试、来源/资产 manifest、验收 Notebook 输出和文档。原 dataset_Mi/.gitattributes 无改动；忽略的 .tmp、.venv、私人 *.local.yaml、权重/MRI/缓存不入提交。
- 本次修改 README.md：将“尚未提交”的过期发布说明改为 karl/Git/Drive 的长期使用说明。修改 PROJECT_GUIDE.md：明确旧 SHA/未上传状态是首次发布前历史快照，已获得本次发布授权，实际发布结果以远端提交为准；没有提前声称推送成功。本日志追加本条，保留 CHG-0001 至 CHG-0010。
- 安全/范围检查：75 个非忽略项目文件总计约 2.05 MB，最大文件是原有数据分发清单；新增源码无大文件。检查常见私钥/API/GitHub token 特征及被禁止的路径/扩展，发现数为 0；仅报告类别/文件名，不打印疑似秘密内容。
- 验证：`pytest -q --basetemp=.tmp/pytest-publish-1`，26 passed in 9.59s，均为 SYNTHETIC/程序验证；git diff --check 无错误（已有 README 换行提醒）；提交前只读核对远端 karl/main 均仍为基准 SHA，未发现并发更新。
- 当前 Git 未配置 user.name/user.email，已向用户请求这两项提交身份；不自造作者姓名/邮箱，不改全局配置。提交/推送需待身份明确后执行，本条不预写提交号或成功结果。
- 风险/限制仍保留：真实 QC/输入配方/ROI/正式验证未完成；GitHub 同步不包含 Drive 权重、环境本体或仓库外 PROJECT_STATUS.md。colab_setup/旧 ZIP 的固定旧基准限制已经在指南中明示。
- 回退：仅可针对本次 README/指南局部改动回退，保留前序实现和历史日志；如未来需撤销已发布代码，使用独立 revert 提交，不强推、重置或删除远端 main/karl 历史。

## CHG-0012 — 首次暂存后补充 EOF 格式检查

- 时间：2026-11-08 19:33（Asia/Shanghai）；执行者 Codex；分支 karl；基准仍为 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`，尚未提交/推送，提交身份待用户提供。
- 对 CHG-0011 的检查范围作补充：先前普通 git diff --check 未涵盖未跟踪的新文件。首次将 58 项变更暂存后，git diff --cached --check 发现其中 28 个新文本文件多余末尾空行；仅删除多余 EOF 空行、保留一个末尾换行，不改代码逻辑、参数或数据。
- 具体文件：`.gitignore`；`configs/paths.example.yaml`、`pilot.yaml`、`validation.example.yaml`；`envs/brain_jepa.txt`、`brainiac.txt`、`core.txt`；`pyproject.toml`；`scripts/build_pilot.py`、`download_pilot.py`、`evaluate.py`、`merge_features.py`、`package_code.py`、`preflight.py`、`report_status.py`、`run_features.py`；`src/mri_pipeline/__init__.py`、`encoders.py`、`features.py`、`fmri.py`、`io.py`、`manifest.py`、`models.py`、`structure.py`；`tests/conftest.py`、`test_cli.py`、`test_features.py`、`test_models.py`。
- 验证：所有受影响 Python 文件 AST 解析通过；此前 26 项功能回归通过，未因仅 EOF 空行调整重复训练/测试。将重新暂存并执行 cached diff 检查。原 dataset_Mi 与作者源文件未改动；Colab 既有快照按原实际哈希保留，不冒充本地格式整理后的新字节版本。
- 回退：如确需恢复格式，可给这些新增文件恢复原多余 EOF 空行，不能为格式回退撤销业务代码或清空目录。历史日志保留。

## CHG-0013 — 提交身份已补齐，继续发布 karl

- 时间：2026-11-08 19:54（Asia/Shanghai）；执行者 Codex；分支 karl；基准 `7bc3e6fc3c9685cc713ea4288705a63740ef2bd6`。沿用用户已明确授权的提交并推送 karl，不推送 main。
- 用户提供 GitHub 邮箱设置截图，实际显示账号的 noreply 邮箱。采用用户此前提供的姓名 Ye Boyang 和截图中的 GitHub 隐私邮箱，仅写入本仓库 `.git/config` 的 user.name/user.email；未更改全局配置或 GitHub 邮箱/隐私设置，也未使用其截图中的个人邮件地址。
- 重新检查：仍在 karl、HEAD 仍为基准、已暂存 58 项、工作树无未暂存修改、cached diff --check 通过。此前 26 项核心回归通过，秘密/大文件/忽略项审阅与 EOF 修正见 CHG-0011/0012，未因身份配置重跑训练。
- 本日志补充身份阻塞解除；将随本次源码提交，不预写自身 SHA。实际提交/推送结果以 Git 历史及远端核验为准。权重、MRI、私人路径配置、虚拟环境和缓存仍不入 Git。
- 回退：如需撤销仓库级作者配置，可仅移除本仓库的两项 identity 配置；不改全局或平台账号。发布后如需撤销源码，以独立 revert 提交处理，禁止为回退强推 main/karl。

## CHG-0014 — Li Yang 首例接收检查与空间信息收尾

- 时间：2026-11-09，最终真实 Colab 收尾运行时间 23:12（Asia/Shanghai，UTC+08:00）；执行者 Codex，范围为用户要求完成第一步、保留预处理工作到其独立分支。
- 分支：li-yang-preprocessing；基准提交 a911ab6b2120698fdf48f1936c7bf7c5c1a17a4a。通过 GitHub 工具读取当前分支，未使用本地 checkout；更新将携带 expected_sha，拒绝覆盖并发改动，不修改 main/karl，不强推。本条随本次源码提交，不预写自身提交号。
- 新增 scripts/close_first_record_intake.py：仅针对 sub-mindo304_ses-placebo，绑定原始 OpenNeuro 提交/annex SHA-256 和匹配 JSON；检查继承元数据、TR 和形状。保留原始文件，在 intake_v2 副本按原 coded sform 明确 pixdim/mm/sec/TR，停用不能无损表达原矩阵的 qform；实际验证原始和缩放后体素完全相同、世界 affine 保持、原始哈希不变，无重采样。
- 新增 notebooks/01_liyang_intake_check.ipynb：来自已执行的私人 Colab Notebook，保留实际文本输出，清除 Colab 账户元数据、下载 JavaScript 和内嵌预览；没有伪造执行结果。原完整预览/历史检查保留于报告包。新增 docs/STEP1_CLOSEOUT.md 和 reports/intake/sub-mindo304_step1_closeout.json（实际输出、路径转为项目相对路径）；AGENTS.md 补充双方分支归属。
- 依据与限制：原始 BOLD pixdim x=2 与 sform 3.4375、JSON VoxelSize=3 均保留审计。研究方案 FOV 220 mm / 64 矩阵支持 sform 间距；此为有依据的首例技术试跑策略，不是个体 DICOM/扫描作者确认，不扩展成全队列自动修复。原 T1 qform/sform 不同本身不证明损坏。
- 真实运行：初始严格 qform 写入因轻微非正交成分失败；改用保留完整 sform、qform_code=0 后，Notebook execution_count=10 实际通过（约 9.7 秒），最后摘要 execution_count=11。不把失败尝试或输入副本整理称为完成了 N4/脑提取/配准/FreeSurfer/去噪。
- 验证：所有共享 Notebook 代码单元 AST 解析通过，无 error 输出；最终脚本与实际执行 Notebook 函数前缀逐字节一致。报告 ZIP SHA-256 901aca7331c13778619675a86669c810407ff759892dbdb121b5c5812e887062；最终 T1 副本 SHA-256 8e6d3104d6171e3528aefe6288357f8cfee97724f0044232bac7c2fd3641dccb，BOLD 副本 a4bf9ceeccaab0978bc9f8927ddec63eff23ff5c436e9881c82004c66e31d747。未执行正式模型、训练或与本次无关的回归测试。
- SliceTiming 无可靠继承/逐例记录，原 slice_code=0，因此跳过 STC，不造参数；该 session 无场图，不声称完成实测场图 SDC。软件安装、持久计算检查点、模型模板配方、fMRI 去噪/QC 与确切 ROI 契约属于下一阶段要求；QC pending，training_ready=False，身份和诊断时点仍未验证。
- 保存/回退：代码及小型证据进入本分支，权重/MRI 不入 Git。原始和副本 MRI 仍在 Colab 临时磁盘，持久保留报告与可重建代码，不冒充已备份影像。若采用新空间策略，新增版本并保留原记录；若需撤销源码，用独立 revert 提交，不改写 main/karl 历史、不删除原始文件/私人 Drive 内容。

## CHG-0015 — Li Yang 2A 工具安装与首例资产检查，Drive 授权待完成

- 时间：2026-11-10（Asia/Shanghai）；执行者 Codex，依据用户“完成 2A”的请求。用户手动恢复 Google 登录后继续；不启动 2B/2C/2D 的实际影像预处理。
- 分支 li-yang-preprocessing；基准 fc31648b8cde9f048a0e8e8506b0e42c1da1daa3。通过 GitHub API 读取分支/日志，未使用本地 checkout；仅发布本分支，不更改 main/karl，以 expected_sha 防止覆盖并发修改。本条随本次提交，不预写自身 SHA。
- 新增 scripts/install_t1_tools.py、scripts/verify_t1_environment.py、scripts/persist_step2a.py 和 docs/STEP2A_STATUS.md；本日志追加 CHG-0015。脚本分别负责独立工具安装、固定首例资产恢复/工具与权重检查、用户授权挂载后显式项目文件的持久保存。没有上传 MRI/权重/账户信息。
- 实际 Colab 新 CPU 会话：2 logical CPUs、12.67 GiB RAM，host Python 3.13.18；昨日临时 MRI 不存在，Drive 未挂载。已安装独立 Python 3.10.22、SimpleITK 2.4.1、numpy 1.26.4、scipy 1.14.1、nibabel 5.3.2、scikit-image 0.24.0、matplotlib 3.9.4、torch 2.5.1+cpu 及官方 HD-BET 1.0 提交 3e3d2a5993e8288f2eae928744ffb496cfc7c651；安装四步均成功，约 23 秒。未替换宿主环境。
- 首次 CLI 验证失败：继承的 MPLBACKEND=module://matplotlib_inline.backend_inline 在独立环境不存在；设置 Agg 后再次运行。旧失败日志/JSON 保留为 attempt1，未写成第一次通过。后续脚本到达最终 JSON：原始及 intake_v2 首例 T1/BOLD 哈希核对、匹配 JSON 恢复、模板读取/哈希、legacy CLI/import 与官方 0.model 的 MD5、strict state_dict load 完成。具体 T1 ITK 读取状态仍以实际 verification.json 为准，不能仅凭脚本无异常推断几何兼容（脚本会记录并保留该类失败）。
- 权重实测 65,443,735 bytes；Zenodo MD5 46ed703cae7611c4f3a60d7b9d8fd666；SHA-256 6f75233753c4750672815e2b7a86db754995ae44b8f1cd77bccfc37becd2d83c。严格加载检查不含 forward/患者推理。
- 核查发现 BrainIAC 作者脚本引用的 HD_BET.hd_bet 不在检查的官方 legacy 包中；后续须显式使用已检查的 legacy CLI/run_hd_bet，不能声称原脚本原样可运行，不能静默换成 HD-BET 2.x。T1 候选顺序/模板保留，固定配准种子为拟增加的可复现设置，实际配准未执行，队友配方确认仍待完成。
- 持久保存尚未执行：当前页面停在 Google “Permit this notebook to access your Google Drive files?”。该授权会允许 notebook 代码读写 Drive，等待用户本人授权；persist_step2a.py 只完成本地 AST/语法审查，未冒称已复制/读回。MRI、模板、权重仍是临时磁盘资产，原 Notebook 保存不等于影像备份。
- 验证：三脚本 AST/py_compile 通过；安装源码 SHA-256 712c07fc59c480632fac36e74ec8e89bac242ce8eba3f300ebd8b24d8a3f77e7，修正后的验证源码 e45f23242670b57eb264525e10759210f523e8d41be3da287af2992fa4e1edde，持久保存源码 29d110a8a09e224ac1f937b7a8333cb1bf500d329ac91fca2e1eaa189cb3e22e。未运行 N4/配准/脑提取/FreeSurfer/fMRI 处理、模型 forward、正式训练或无关回归。
- 限制/回退：2A 整体仍待 Drive 授权与读回、T1 几何详细结果审阅及队友配方确认。FreeSurfer 安装/许可和 fMRI 工具/契约属于后续子阶段；QC pending、training_ready=False。可通过独立 revert 撤销本次新增代码/文档，保留历史日志及前序源码，不清空原始 MRI/Drive，不强推任何分支。

## CHG-0016 — 2A 持久保存验收，启动并修正首例 2B 候选预处理

- 时间：2026-11-10（Asia/Shanghai）；执行者 Codex；用户授权继续 2B。分支 li-yang-preprocessing，基准 76858889c0ece99b3ba55b3849cbfbd9a09168c9。GitHub API 工作，无本地 checkout；以 expected_sha 更新本分支，不改 main/karl，不强推。
- 新增 scripts/preprocess_first_t1.py、docs/T1_PILOT_RUNBOOK.md；更新 docs/STEP2A_STATUS.md 追加授权/持久读回实测，保留最初状态为历史快照；本日志追加 CHG-0016。代码是首例技术试跑，不自动设配方、QC 或训练 ready。
- 2A 补充实测：用户授权后旧 mount 调用曾失败；同一授权重试约 6.6 秒成功。persist_step2a.py 实际执行约 6.1 秒，25 files / 214,269,339 bytes 持久复制和 SHA-256 读回通过。完整验证 JSON 显示 T1 的 SimpleITK read 与 legacy CLI/template/权重检查均 pass；先前 CHG-0015 对读取细节未下结论，此处补齐。
- 2B 第一尝试 pilot_20261110T075350Z，源码 SHA f750b118813e0885b1f38d5dd5c4910eb8ae3ae2e0f52b9fc9008db48effb3a2：全分辨率无 mask N4 未完成，观测 Colab RAM 指示曾约 10.46/12.67 GB；运行约 5 分钟后为适配资源主动终止，returncode -15。已保留执行源码/参数/进程日志/stopped_attempt.json 并复制读回，不冒称发生 OOM 或影像损坏。
- 候选 N4 调整为官方 SimpleITK 示例的 Otsu 前景 mask（200 bins）、shrink=2 估计场，再在原始网格计算/应用 log-bias；最终输出保留原分辨率。明确区别于 BrainIAC 作者无 mask 全网格调用，保留候选配方/所有变更；不是原脚本原样复现，不属于数据增强。方法依据 https://simpleitk.readthedocs.io/en/master/link_N4BiasFieldCorrection_docs.html 。
- 第二尝试 pilot_lowmem_20261110T075859Z，源码 SHA d2a440542d123ba128534bd175f5f4b86f1203a870925336e6aaf64361ccfae7：N4 实际 62.186 秒完成并持久读回；配准初始化随后失败。SimpleITK 偏置场应用产生 64-bit float moving，而 fixed 是 32-bit；失败源码/日志/failure.json/N4 输出均保留。
- 修复为配准前显式 sitkFloat32 cast；新增 --resume-n4-from，核对前次 input/template 哈希、N4 配方版本/网格及 local/Drive 文件 SHA 后复用已完成 N4，不重算、不覆盖前次目录。续跑 pilot_resume_20261110T080241Z，源码 SHA 9b6962391e6642c056911f484783760527c01127544bc8c231d5201c0d62a529；实际日志证实 moving cast 前是 64-bit。
- 续跑实际完成 N4 复用与配准、均通过 Drive 读回；配准优化沿用作者框架，额外固定 seed=20261110，保存两方向变换和初始/最终对齐图。当前 HD-BET CPU fast tta=0 正在执行，已到真实影像 forward，尚未将其记为完成或 QC 通过。各阶段不可变目录、校验/失败留档、进度 PID/log 及输出表详见新增 runbook。
- 验证：脚本 AST/py_compile 通过；实际首例运行暴露并修复上述像素类型接口问题。CLI、权重严格加载与真实 N4/配准是已运行证据；HD-BET 最终输出/QC PNG/完整 handoff 的结果将另据实际输出追加，不预写。未运行编码器特征、96³ 转换、FreeSurfer、fMRI 处理、分类训练或无关回归。
- 范围/限制：单例技术预处理；身份与诊断时点仍待核实，配方需要队友审阅，qc_status=pending、training_ready=False。MRI、mask、偏置场、模板、权重和 PNG/大型日志保存在私人项目 Drive，不进入 Git；仅源码、说明和小型审计结果可发布。允许显式复用 N4，不声称支持全部阶段自动恢复。
- 回退：用独立 revert 只撤销本条涉及的源码/文档变更；保留 CHG-0015 及之前记录、实际历史运行和原始 MRI。禁止为回退清空 Drive、覆盖不同 checkpoint、重置或强推 main/karl。

## CHG-0017 — 首例 2B 完成、最终持久读回与 QC 证据交接

- 时间：2026-11-10（Asia/Shanghai）；执行者 Codex，继续完成用户已授权的 2B。分支 li-yang-preprocessing；基准 8951931a944cdc521d5f43c2adbd69a96ef4f2bb，GitHub API 工作，无本地 checkout。仅更新本分支，expected_sha 防并发覆盖，不改 main/karl，不强推。
- 新增 scripts/preview_t1_registration.py、scripts/export_t1_pilot_reports.py、docs/T1_PILOT_RESULTS.md；更新 docs/T1_PILOT_RUNBOOK.md 补充已完成结果及实际执行的两个工具。新增 reports/t1_pilot/sub-mindo304_ses-placebo/ 的 SUMMARY、handoff_pilot、三个 stage、run、N4 参数、final_readback 及 history 中的受控终止/类型失败 JSON；本日志追加 CHG-0017。图像/权重/ZIP/PNG 二进制不入 Git。
- 实际成功运行 pilot_resume_20261110T080241Z 于 2026-11-10T08:26:31Z（16:26:31 Asia/Shanghai）完成，进程 returncode=0。执行源码 SHA-256 9b6962391e6642c056911f484783760527c01127544bc8c231d5201c0d62a529，与已发布处理脚本一致。N4 原计算 62.186 s（续跑复用，本次不重算）、配准 14.140 s、HD-BET CPU fast tta=0 为 1398.175 s。阶段标记与最终 handoff 均由真实输出产生。
- 输出 T1 brain、binary brain mask、N4/偏置场/前景 mask、参考/初始及最终配准图、双向物理变换、参数/优化轨迹/软件版本/耗时/日志和四张 QC PNG。最终模板网格 170×206×162、1 mm、LAS。原始与 intake_v2 输入 SHA 未变；技术检查包括有限值、shape/affine、二值 mask、mask 内 brain=registered、mask 外为零。
- export_t1_pilot_reports.py 实际完成独立最终 Drive 读回：24 个文件逐项 SHA-256 一致。报告 ZIP 4,679,927 bytes、SHA-256 ff7ee984ca7556b3fb522970d17980283db7f997d3f8a4d7d30fbe2ff3ade618，包含实际记录/四张 QC PNG/历史尝试/诊断，不含 NIfTI、model/ckpt/权重。通过已显示的报告下载链接取回同字节报告，再核对 SHA、ZIP CRC 和成员路径/排除项；未重新运行预处理来生成“验证结果”。
- CPU forward 耗时较长；从 PyPI 临时运行只读 py-spy dump（不带 locals），先定位到作者网络末段 3D 卷积，随后到 mask resize/export。没有向目标发送控制信号、调整安全策略或改权重；诊断文本保留在报告/项目 Drive。与 CHG-0016 中主动停止首次 N4 的行为明确区分。
- Codex 实际查看 input/N4、三方向配准、六张轴位 mask 和九张三方向 mask 抽样视图：暂未见整体严重翻转/错位、大范围脱脑或大块颅骨残留。该结论仅是有限抽样的初步视觉检查，不是全体积专家 QC 或分割准确率；边缘皮层、小脑/下方覆盖和全部边界仍需团队复核。1190.342 ml 仅是该二值 mask 体积，不是 ICV、82 项 FreeSurfer 体积或 GT；没有计算 Dice/AUC。
- 验证范围：三个处理/导出/预览脚本 AST/py_compile 通过，新增文本 EOF/空白检查通过；预览和导出均有真实成功运行。新增公开源码与元数据检查，不发布 MRI/PNG、模型或凭据。未额外运行无关合成测试、编码器特征、正式训练、FreeSurfer 或 fMRI 处理。
- 剩余边界：2B 技术图像处理完成；input_recipe_confirmed=false、qc_status=pending、training_ready=false 保留。需队友输入配方接受及后续人工 QC 才能标 T1 正式 ready；身份/诊断时点也未验证。2C、2D 及整个 MRI branch 预处理未完成。
- 回退：用独立 revert 撤销本条新增/更新的说明、工具或小型记录；保留 CHG-0016、前序源码、实际各尝试和原始 MRI/私人 Drive。不删除历史数据、覆盖不同 checkpoint 或强推其他分支。


## CHG-0018 — 准备首例 FreeSurfer 分段执行和结构体积交接代码

- 时间：2026-11-10（Asia/Shanghai）；执行者 Codex；用户要求自行操作 Colab，先准备跑前工作。分支 li-yang-preprocessing；基准 e2938437a247fb46546ae0e724137cb0b54c4a65。通过 GitHub API 读取固定基准并创建新 tree，无本地 checkout；仅更新本分支，expected_sha 防并发覆盖，不改 main/karl，不强推。
- 新增 configs/freesurfer_pilot.json、scripts/freesurfer_pilot.py、scripts/freesurfer_volumes.py、scripts/freesurfer_qc.py、tests/test_freesurfer_preparation.py、docs/STEP2C_RUNBOOK.md。输入固定原生 intake_v2 T1 SHA，而非 2B 模板空间/去颅骨图。候选固定官方 FreeSurfer 8.2.0、FS_V8_XOPTS=0，Ubuntu22/24官方包及MD5；保守有效内存30GiB、磁盘40GiB门槛。安装需用户本人许可和显式接受，不提供或公开许可。
- 三段 autorecon1/2/3 单独执行、完整subject归档、Drive复制读回、不可变运行记录、按相同build/OS/config恢复已完成检查点至新run。QC叠图保持pending；导出68皮层+14皮层下原始mm³体积及独立eTIV/raw stats；不提前ICV校正/缩放。人工审核和全项目通用pipeline_id明确后才允许正式structure交接，training_ready仍false。
- 与固定karl接口a911ab6b2120698fdf48f1936c7bf7c5c1a17a4a核对82列顺序、stats读取及CSV门槛，schema SHA为5a2fffd7404afa7b7e8e6302d6c76593985317fd49d60128d0b9c747fc4b0c99。没有改动原schema或队友源码。
- 实际验证：本地执行 python -m unittest discover -s tests -p test_freesurfer_preparation.py -q，15项合成测试通过（2026-11-10复验0.022s），包括与现有读取器逐值一致、缺失/重复/别名/单位拒绝、低内存/许可/阶段/归档路径保护、不能自动QC通过及恢复原归档归属。语法检查通过。测试不含真实MRI、FreeSurfer安装或模型推理；本地临时peer源码仅用于验证，不作为本次新增文件发布。
- Colab只读资源检查于2026-11-10T09:44:06Z实际执行：2逻辑CPU、12.67GiB RAM、105.4GiB本地空闲、Ubuntu24.04.5、未检测nvidia-smi；Drive已挂载，native T1存在，/content/license.txt不存在。属于此刻打开会话，不推测用户其他会话；未对输入做新的哈希验收。运行前条件尚未齐备。
- 未执行：下载/安装完整FreeSurfer、autorecon、真实82体积/eTIV、QC图生成、编码器或分类。候选依赖、实际耗时与质量仍待实跑。Notebook将在后续单独提交固定引用本源码提交，避免以可变分支作为执行来源。
- 已检查发布白名单、EOF和语法；无本地git diff/status可报告。原始MRI、许可、权重、二进制图像和大日志不入Git。风险：Colab会话可中断，仅已完成阶段可归档恢复；资源门槛不保证运行成功；有限PNG不能替代完整体积/表面人工QC。
- 回退：独立revert本次新增文件并追加日志，保留历史、Drive原始影像及前序结果；不清空数据或强推其他分支。


## CHG-0019 — 新增固定源码快照的独立 2C Colab notebook

- 时间：2026-11-10（Asia/Shanghai）；执行者Codex；继续用户“准备跑前工作”要求。分支li-yang-preprocessing，基准d8bdfa7a125c9153943081f436eaf13966fea65d；GitHub API白名单新增notebooks/06_liyang_freesurfer_2c.ipynb及本日志。无本地checkout，不改main/karl，非强推。
- Notebook固定引用CHG-0018源码提交d8bdfa7a125c9153943081f436eaf13966fea65d，并逐文件验证SHA-256；资源检查、Drive输入哈希读回、个人许可上传、官方安装、隔离QC环境、新run初始化、三段计算、QC、draft导出/人工接受、状态/恢复分别独立。安装、初始化、各重建阶段、最终接受、恢复默认关闭；不自动Run all、不用可变分支下载可执行代码、不接受许可或编造审核。
- 原始首例与schema不变；输出仍原始82体积和独立eTIV，校正/缩放留给训练折内。个人许可不打印、不进入检查点或Git。
- 实际验证：15个代码格AST语法检查通过；JSON/cell字段及空输出/空执行计数核对。Notebook没有写入伪造执行输出；真实软件安装/重建仍未执行。源码包的15项测试见CHG-0018，不将其冒称本Notebook完整Colab运行。
- 限制：隔离QC环境和FreeSurfer完整安装需实机验证，Colab当前资源/个人许可仍有门槛；完整阶段归档仅在正常结束后生成。初始Notebook SHA-256 72090e230f126b7f2b82ed6c50fa7a286d71e669664cbd728beb40afd06ff280。
- 回退：独立revert本Notebook新增，保留已发布源码、历史日志和所有Drive输入/结果，不覆盖旧Notebook或强推。


## CHG-0020 — 实测 Colab 源码与输入核验、保存独立运行入口

- 时间：2026-11-10（Asia/Shanghai）；执行者Codex；继续用户“跑之前准备好”授权。分支li-yang-preprocessing，基准2367ee5855d2ab77b9b39d4abed29c0aa37175e4；仅本分支API白名单更新，expected_sha防并发，不改main/karl，不强推。
- 新增reports/freesurfer_preparation_status.json；更新docs/STEP2C_RUNBOOK.md追加实际准备结果并保留最初边界；追加本日志。真实影像、个人账号/许可、二进制截图不入Git。
- 在已有Colab notebook新增并实际执行准备专用格（仅P1/P2/P3源码，无install/init/recon）：固定d8bdfa7a125c9153943081f436eaf13966fea65d代码及5文件SHA核验通过；2026-11-10T09:49:32Z实际资源2核/12.6714GiB/105.399GiB空闲/Ubuntu24.04，资源门槛BLOCKED。Drive raw T1和native intake SHA分别89ea431...af73b5、8e6d310...64dccb，与固定完整哈希一致；准备JSON持久复制与SHA读回通过。格正常结束，观察耗时1.122s；不把此耗时当成重建耗时。
- Git远端回读确认CHG-0019 notebook字节与本地准备文件完全一致。通过Colab的Copy to Drive创建独立06_liyang_freesurfer_2c.ipynb副本并检查标题/内容；新副本尚未连接运行时，所有重建开关关闭。旧notebook的准备结果已保存；没有Run all或重跑2B。
- 实际已完成源码/资源/输入/保存核验；未完成FreeSurfer安装、隔离QC依赖安装、个人许可上传、autorecon和任何真实stats/QC。当前资源不足且许可缺失，不能称环境ready。当前检查只适用于所连会话，不推测用户其他算力。
- 验证：新增JSON可解析，文档/JSON EOF通过；本次纯记录更新未重复运行无关测试或训练。无本地checkout，不冒称git diff/status；对API发布文件白名单及保留基准tree进行了检查。
- 回退：独立revert本次审计/文档追加并保留历史日志、源代码及所有Drive文件；不删除原始影像/先前结果或强推。
