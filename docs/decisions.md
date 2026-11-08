# 方法、输入配方与待决事项

日期：2026-11-08。主依据为提交版报告及 2026-11-07 协作规范。下列“候选实现”不代表双方已批准科学方案变更。

## 已保留的方案

- 人口学为年龄、性别、教育类别，主模型不使用 MoCA。82 个结构体积+ICV、77 项 signed Fisher FC、两个冻结编码器。
- D/S/Z/F/U/R，U/R 共用 b，匹配 h 结构、初始化、优化预算；R 使用无诊断监督的岭回归 g。h 使用按人留出交叉拟合输入，预测时按折路径平均概率。
- 主分析 UHP 配对候选；正式队列取决于身份、诊断时间与 QC。不同公开 ID 不凭相同数字追加合并。历史清理冲突保留在仓库外 PROJECT_STATUS.md，未重写原数据。
- 独立环境、持久存储、按 record_id 合并及版本/哈希留痕；本地开发仅 karl，不直接推送 main。

## 作者代码核对基线

BrainIAC：`ba60f45bed832ee0e5683c678caeaeefe2072f0d`。已核对 [model.py](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/src/model.py)、[dataset.py](https://github.com/AIM-KannLab/BrainIAC/blob/ba60f45bed832ee0e5683c678caeaeefe2072f0d/src/dataset.py)、quickstart/get_brainiac_features/load_brainiac。适配器调用作者模型，使用作者验证变换，提取 `features[0][:,0]`；仅将其称为 author_first_token，不假设其 token 语义。作者严格加载 backbone；项目额外核查 checkpoint 哈希。保留作者 Research-Only LICENSE 与 Tak et al. 2026 引用（doi:10.1038/s41593-026-02202-6）。未将作者代码或权重复制进本仓库。

Brain-JEPA：`b1dfa93eb331d1e70476446b06fc8a1ac3c92345`。已核对 [数据接口](https://github.com/Eric-LRL/Brain-JEPA/blob/b1dfa93eb331d1e70476446b06fc8a1ac3c92345/src/datasets/ukbiobank_scale.py)、[模型](https://github.com/Eric-LRL/Brain-JEPA/blob/b1dfa93eb331d1e70476446b06fc8a1ac3c92345/src/models/vision_transformer.py)、helper 和下游模型。作者按 50 Tian S3 + 400 Schaefer17n400p 排列，需要 gradient，450×160/patch16；示例下采样不等同于本项目连续帧规则。适配器不调用作者会捕获并吞掉 checkpoint 错误的训练恢复函数，使用 strict=True 加载指定 encoder/target_encoder；只提取 token 表征，不使用分类 logits。保留 Dong et al. NeurIPS 2024 引用（arXiv:2409.19407）；代码及所选权重许可范围仍待确认。

## 阻塞真实提取的待定项

1. ARTIFACT_ROOT、两人的共享/私人 Drive 路径；用户确认尚未准备。
2. 权重实际文件、SHA-256、checkpoint 分支与下载条款；本轮未下载。
3. BrainIAC 具体配准模板、空间配方和预处理 QC；96³ 只是模型张量尺寸。
4. Brain-JEPA 具体图谱文件/空间/哈希、ROI 顺序、Schaefer17/7 映射、450 行 gradient 的来源和哈希。
5. 时间标准化和池化。代码支持单例全张量 sample-std 标准化，或来源为 external_pretraining 的冻结 ROI robust 参数；后者不得用全项目队列估计后缓存。两种均需真实权重匹配确认，不默认选用。
6. FD 定义/阈值、初始帧、滤波、aCompCor、邻帧处理等由双方基于 QC 锁定。无 GSR 主路线不变。
7. 首例真实输入、ICV 方法/FreeSurfer 版本、人工 QC 和身份/诊断时点证据。
8. 编码器预训练队列与本研究样本是否存在重叠；目前未完成独立核查。

FreeSurfer 原始统计的丘脑名称采用当前官方 LUT 的 Left/Right-Thalamus，兼容旧 Thalamus-Proper 别名；两者同时出现则拒绝以免重复计数。固定输出列仍只有左右各一项。依据：[FreeSurfer 官方 LUT](https://github.com/freesurfer/freesurfer/blob/dev/distribution/FreeSurferColorLUT.txt)，本轮只读核查了标签 10/49；具体分割版本仍须由交付方记录。

## 代码实现中需要正式分析前确认的细节

- 按自然人分层：先在唯一 person_id 上做分层划分，再映射全部记录，不按扫描行数近似平衡；同人标签冲突时停止，先明确访视策略。
- 多记录人的指标先平均其留出概率，再按人计算。训练阶段目前仍按记录计算损失/类别权重；若最终保留多次访视，需先锁定访视取用或权重规则，不能将此实现直接当作已定的纵向分析方案。
- 候选验证实现：D/S/Z/F 各自以 inner AUC 选择参数；U/R 用同一个候选的平均 inner U/R AUC 联合选参，保证共用 b 且匹配 h。该联合选参规则是待确认的实现提案，配置 `paired_selection_rule` 及 `decision_confirmed` 默认未设置，正式入口会阻止运行。
- h 采用一层 tanh MLP、全批 Adam、加权 BCE、固定训练轮数；未用外层数据 early stopping。候选宽度/轮数/正则和预算需在正式分析前锁定，不宣称它们已优化。
- g 先对训练路径 z 标准化，预测后逆变换回原始冻结特征坐标，再计算残差。h 的缩放只在其交叉拟合训练输入上拟合。
- 分类阈值仅由 inner 留出预测选 balanced accuracy 最优值；outer 留出仅评估。区间按人、类别分层、配对重采样固定预测，并把 repeats 保持在同一人内；不包含完整重训不确定性。
- folds/repeats 默认留空，不根据当前 3–5 例生成分类结论；22 配置未自动展开运行。

## 仍未达成的事实

真实模型加载、T1/功能输入兼容、全队列 QC、正式特征提取及分类结果均未验证。合成测试只验证软件行为。旧试跑资料用户确认不可用；新代码不标作恢复旧运行。

## 2026-11-08：当前阻塞项更新（补充前述历史盘点）

- 私人 Drive、两套实际预训练权重/哈希、BrainIAC 参考模板与 JEPA gradient 已准备；两个编码器严格加载与随机张量检查通过。实际资产证据见 `manifests/encoder_assets.json` 和已保存输出的 `notebooks/01b_encoder_assets_check.ipynb`。先前“路径/权重未准备”是历史状态，不再是当前阻塞。
- 仍须获得真实首例 QC 并共同确认输入配方；Brain-JEPA 预训练 robust 参数未在公开文件中核实，具体 450 行 label_name/图谱对应、Schaefer17→7 网络映射和许可范围未解决。候选单窗口标准化/encoder/raw mean pooling 已具体写入独立配置文件但未自动采用；作者原配置与候选的差别见 `docs/ENCODER_INPUT_SPEC.md`。
- 普通 attention 的 T4 技术适配只替换强制 flash import；实测两个分支可严格加载及前向，但不宣称与 FlashAttention 后端逐位一致，不把技术可运行当作输入科学有效性证明。
