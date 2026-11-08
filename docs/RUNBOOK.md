# Ye Boyang 的 MRI 运行说明

本轮新增的是代码与技术验证，不是已经完成的影像实验。先用 sub-mindo304 跑通真实 T1；其 QC/元数据阻塞时记录原因再考虑 sub-mindo379。队友按 data_contract.md 逐步交付，哪个分支先 ready 就先对接。

## 1. 本地开发和测试

正式工作目录 `D:\finalProject\MRI-classification`，分支 karl。旧 `MRI-classification-karl` 是无 Git 元数据的源文件副本，不作为开发目录。检查 `git status --short --branch` 后工作，保留用户已有修改。

已在项目 `.venv` 安装核心/测试环境，未修改全局环境。新电脑可执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r envs/core.txt
.\.venv\Scripts\python.exe -m pytest -q
```

本机若系统临时目录不可写，先把 TEMP/TMP 指向本项目已建立的 `.tmp` 再安装/测试。本机 Python 3.12 测试只覆盖核心数值与合成样本，不代表作者 CUDA 环境已验证。

`manifests/pilot_subjects.csv` 已从原固定清单生成五例。不要重新运行 build_pilot.py 覆盖它；该脚本遇到同名文件会停止。初始 processing_status 为 35 个 pending 阶段；不把旧 motion_pass 当作新 QC。

## 2. Colab 代码与存储

本地新增代码尚未提交/推送。若现在测试 Colab，先打包手动上传：

```powershell
.\.venv\Scripts\python.exe scripts/package_code.py --output .tmp/mri-colab-code.zip
```

代码包仅包含 Git 已跟踪及未忽略的新源文件，不含 .venv、MRI、权重或个人配置。它附带 CODE_SNAPSHOT.json，记录分支、基准提交及每份文件哈希，明确标记未提交快照。上传 Colab 后解压到 `/content`，得到 `/content/MRI-classification`；preflight 会校验快照，即使包内没有 .git 也可检查来源。后续若用户安排将代码推到 karl，才可直接克隆含这些文件的远端版本。打包脚本不推送代码。

ARTIFACT_ROOT 必须指向你实际可写的持久 Drive 目录，DATA_ROOT 放数据，CODE_ROOT 放代码。先在运行机器本地计算，复制结果时校验哈希；不直接由两人并发写同一个结果。Drive 的实际挂载/共享路径尚未确定，模板没有编造路径。

复制 `configs/paths.example.yaml` 为 `configs/paths.local.yaml`，复制 pilot.yaml 为 pilot.local.yaml，填真实路径及配方。*.local.yaml 被 Git 忽略；不将私人配置、权重、MRI、license 和令牌提交。

## 3. 取得首例数据（显式可选）

当前克隆只有清单和配套表，影像未下载。原下载器参数无 --subject/--ids。新增辅助脚本的默认模式只显示计划：

```bash
python scripts/download_pilot.py --record-id sub-mindo304_ses-placebo
```

只有用户实际决定取用该例时才运行：

```bash
python scripts/download_pilot.py --record-id sub-mindo304_ses-placebo --output /content/mri_data/dataset_Mi --execute
```

它调用未修改的当前下载器，保留原完整清单与固定哈希，先还原清单允许的配套文件（含 JSON/旧运动表，需下载配套 ZIP），再只下载这一例的 T1/BOLD，逐文件验证。不精简/改写原清单，不调用历史 Release 旧下载器，不改变 QC 状态。无需重复下载队友已按同一清单核验并交付的文件。本轮只检查计划，未执行下载。

## 4. BrainIAC 首例

打开 `notebooks/02_brainiac.ipynb`。安装独立的候选环境前先确认 Python/CUDA 兼容性；`envs/brainiac.txt` 并未在真实权重上验证。

将作者代码单独放在 third_party（忽略目录）并检出固定提交：

```bash
git clone https://github.com/AIM-KannLab/BrainIAC.git third_party/BrainIAC
git -C third_party/BrainIAC checkout ba60f45bed832ee0e5683c678caeaeefe2072f0d
```

权重从作者 README 的 Dropbox 入口另取，保留许可/引用并记录 SHA-256。代码不会自动下载权重。与队友锁定模板和预处理步骤，再填写 checkpoint_sha256、template_sha256、input_recipe_confirmed。设置 handoff 的 t1 阶段实际文件/哈希/QC，不用报告截图代替输入。

```bash
python scripts/preflight.py --paths configs/paths.local.yaml --config configs/pilot.local.yaml --encoder brainiac
python scripts/run_features.py brainiac --paths configs/paths.local.yaml --config configs/pilot.local.yaml --handoff /actual/path/handoff.json --device cuda
```

preflight 缺项时以退出码 2 列出阻塞。它通过只表示配置可继续检查；模型会再次核查作者 Git HEAD、代码改动、权重 SHA、图像数值与 affine、严格权重加载和实际输出。输出预期按当前作者模型为 768；实际不符则报错。日志区分前向耗时与加载/变换/前向总耗时，失败也保存。

## 5. 结构测量、FC 和 Brain-JEPA

结构提取只读取队友 FreeSurfer stats 与 ICV，不运行 FreeSurfer：

```bash
python scripts/run_features.py structure --paths configs/paths.local.yaml --config configs/pilot.local.yaml --handoff /actual/path/handoff.json
python scripts/run_features.py fc --paths configs/paths.local.yaml --config configs/pilot.local.yaml --handoff /actual/path/handoff.json
```

FC 只读完整 `[T,450]` 时序中的已验收连续 160 帧；输出 77 项 signed Fisher 汇总和每项边数量。它不执行预处理或从旧运动表虚构通过规则。

Brain-JEPA 使用 `notebooks/03_brain_jepa.ipynb` 和独立环境。作者旧 torch/flash-attn pins 可能不支持默认 Colab 的 Python/CUDA；先准备兼容的独立解释器（候选 Python 3.10），不要在 BrainIAC 环境上混装。检出作者 `b1dfa93eb331d1e70476446b06fc8a1ac3c92345`，保留其来源与引用，另取真实预训练 checkpoint。当前没有许可、权重或环境已验证的保证。

填实 `schemas/atlas_contract.example.json` 的私人副本，包括精确 450 labels、atlas/空间/哈希、roi_order 和 gradient 哈希；example.tsv 没有真实 ROI 行，不能用于提取。明确 checkpoint_key、归一化及池化，确认与权重匹配后再把 recipe_confirmed 设为 true。

```bash
python scripts/preflight.py --paths configs/paths.local.yaml --config configs/pilot.local.yaml --encoder brain_jepa
python scripts/run_features.py jepa --paths configs/paths.local.yaml --config configs/pilot.local.yaml --handoff /actual/path/handoff.json --device cuda
```

禁止将分类 logits 冒作深度向量，也不能只因 450 个 ROI 相同就宣称图谱兼容。正式分析若需项目队列级标准化，必须放到训练范围内；当前提取接口拒绝全队列拟合的 robust 参数。

## 6. 合并、持久保存与汇报

`feature_set_id` 或 pipeline 配方有变化时使用新版本，重跑不覆盖旧分量。各阶段产生独立组件 JSON；合并后生成汇总 features.json：

```bash
python scripts/merge_features.py --manifest manifests/pilot_subjects.csv --feature-root /actual/artifacts/features/pilot_v1 --output /actual/artifacts/reports/pilot_features.npz
python scripts/report_status.py --logs /actual/artifacts/logs --output /actual/artifacts/reports/processing_status.csv
```

只有一个组件准备好时可用 `--components z_t1` 检查首例；传入 manifest 必须仅列已选择、实际具备全部所需组件的记录，不能把缺失的另外四例静默跳过。人口学、label、身份与训练标记分别保存。确认输出复制到持久存储且哈希一致，重启能加载再扩展 3–5 例。阶段汇报使用真实 QC、实际维度、对齐和耗时；功能分支阻塞就保留准确异常，不报告小样本可信分类性能。

## 7. 正式模型接口（当前禁止用 pilot 运行）

模型代码见 src/mri_pipeline/models.py：D/S L2 logistic、Z/F 小 MLP、U/R 固定基础 logit 加 MLP 修正；g 为多输出 ridge，逆变换回冻结坐标后求残差。每个 nuisance 路径独立拟合人口学编码/填补、ICV 校正和缩放；h 训练输入按人留出。U/R 同一 b、初始化与预算。每条路径预测概率再平均。

`scripts/evaluate.py` 仅接受全部身份/诊断/QC 确认且 training_ready=True 的数据。先审阅 decisions.md，明确取用访视、联合选参、折数与预算，再填写 validation 私人配置（默认 false/null）。例子仅说明接口，**本轮未运行正式验证**：

```bash
python scripts/evaluate.py --data /actual/approved/cohort_features.npz --config configs/validation.local.yaml --output /actual/artifacts/evaluation/run_unique_id
```

它输出外层留出概率、内层选出的阈值、分折/交叉拟合人名单、配置/数据哈希、指标和固定预测的按人配对 bootstrap 区间。输出目录必须全新。22 项实验配置尚待全队列 QC 后组织，没有一键默认展开训练。

## 8. 已授权的 VS Code Colab 环境恢复

`scripts/colab_setup.py` 只配置已经分配的 Python 3.12 运行时，不申请服务器、不购买额度、不下载 MRI 或权重。先由本人完成 Drive 授权，确认 `/content/drive/MyDrive/FYP_MRI` 已真实挂载，并已有 `artifacts/configs/ye_boyang/paths.local.yaml` 和 `pilot.local.yaml` 备份。

将本地核验过的源代码 ZIP 和本脚本传入 Colab 后，在 Notebook 中通过 `subprocess.run` 调用：

```python
subprocess.run([
    sys.executable, '/content/colab_setup.py',
    '--package', '/content/mri-colab-code.zip',
    '--sha256', '填写本次代码包实际SHA256',
], check=True)
```

脚本校验 `karl` 快照和逐文件哈希，恢复私人配置，建立 `/content/venvs/brainiac`，使用宿主 pip 的 `--python` 安装固定依赖；不覆盖 Notebook 宿主环境。接着检查真实 CUDA 小矩阵运算，并稀疏获取固定 BrainIAC 作者提交及许可证。环境版本记录以唯一文件写到 Drive 的 `artifacts/logs`。本机 `.tmp/01_authorized_colab_setup.ipynb` 是本次实际传输用的临时 Notebook，内嵌已核验代码包，不提交 Git。

遇到已有不同文件、不同配置、部分环境或不同作者版本时停止，先检查差异；不要清空目录重来。环境检查成功仍须另做 checkpoint/模板哈希、输入配方和真实首例 QC 验收。Brain-JEPA 的环境与输入契约独立处理。

## 9. 已执行的官方资产准备与交接边界

`scripts/prepare_encoder_assets.py` 在已经授权且挂载 Drive 的 Python 3.12 Colab 内运行；只获取已确认的两个预训练 checkpoint、作者参考模板和 gradient，文件名/大小固定，不拉取参与者 MRI，不训练。它会建立独立 `brain_jepa` 环境，严格加载官方权重，并用随机张量检查维度/有限值；这不是项目真实特征提取。普通 attention 的兼容逻辑见 `src/mri_pipeline/jepa_compat.py` 与 `docs/ENCODER_INPUT_SPEC.md`。

本次运行前，临时 `.tmp/03_encoder_assets.ipynb` 先把 6 个已审计源文件变更迁入远端根目录，校验 before/after 哈希并备份源码/快照；不是在旧源快照上默默改文件。后续从新代码包运行时应包含新增模块、环境文件和更新后的 preflight，不混用旧代码 ZIP 与新入口。

实际权重/模板/gradient 的来源、大小、哈希和 synthetic 检查见 `manifests/encoder_assets.json`。读取 Drive 原报告并执行最终预检的入口是 `notebooks/01b_encoder_assets_check.ipynb`，已保存实际输出。资产配置 before/after 版本位于 Drive `artifacts/configs/ye_boyang/assets_<UTC时间标识>/`；恢复时核对要使用的版本，不能用最早的空 checkpoint 配置覆盖已经填好的配置。

当前不要解除 QC/配方门槛。把 `docs/TEAMMATE_HANDOFF_REQUEST.md` 交给预处理同学审阅，先收同一例已通过 QC 的 T1；`configs/brain_jepa_pilot_candidate.yaml` 只是明确未确认、不会自动加载的候选。真实数据验收后才使用 02/03 特征 Notebook。图谱/ROI、标准化与时间采样的差别及许可缺口仍需处理。
