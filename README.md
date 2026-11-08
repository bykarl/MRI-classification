# MRI-classification

MRI 研究代码在 `karl` 分支开发。原有 `dataset_Mi/` 保留，MRI 本体仍需按固定清单单独获取。

当前已提供单例特征入口、77 项 FC、严格特征连接、D/S/Z/F/U/R 模型和按自然人嵌套验证代码。两套官方预训练权重、参考模板与 gradient 已保存到 Drive，严格加载及随机输入技术检查通过；**真实首例 QC/输入配方、ROI 契约和正式分类验证仍未完成**。随机输入检查不代表真实患者实验结果。

- [项目文件说明与换设备指南](PROJECT_GUIDE.md)：逐项文件用途、GitHub/Colab/Drive 保存区别及每日同步步骤。
- [运行说明](docs/RUNBOOK.md)：本地测试、Colab 单例步骤及配置。
- [交接接口](docs/data_contract.md)：队友交付的文件、字段与校验。
- [决策与待确认项](docs/decisions.md)：输入配方、图谱、QC 和验证规则。
- [实现状态](docs/IMPLEMENTATION_STATUS.md)：代码验证与真实运行分开记录。
- [改动日志](CHANGELOG.md)：逐次改动、验证和回退线索。

代码通过 `karl` 分支同步，权重、私人配置和结果存放于各自持久存储。换设备前保存并提交/推送，另一设备开始前拉取；Colab 临时运行副本不代替 Git 备份。首次发布前的盘点见项目指南，实际发布结果以 Git 提交历史和远端 `karl` 为准。不要直接推送 `main`。
