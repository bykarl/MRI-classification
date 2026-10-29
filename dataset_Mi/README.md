# MiND 团队数据集

**状态：完整数据已发布。全部 769 个附件均通过服务端 SHA-256 校验；可还原全部 3,512 个原文件，本地原文件内容保持不变。**

正式发布后访问：https://github.com/bykarl/MRI-classification/releases/tag/mind-ds007857-v1.0.1-team-20261028

# 完整 MiND 团队数据下载说明

本 Release 分发本项目的 `dataset_Mi` 文件夹，包含已选取的 CN/MCI T1 和静息态 BOLD，以及现有参数、标签、质控、脚本和依赖。**它不是上游 OpenNeuro ds007857 的全部模态和全部参与者。**

- 原始 MRI：764 份 `.nii.gz`，每份作为独立 Release 附件，文件内容不改写。
- 其他原有文件：`dataset_Mi_support.zip`，用于保留原目录结构和全部配套文件。
- `dataset_manifest.json`：每份原文件的目录、大小、SHA-256 和下载位置。
- `SHA256SUMS.txt`：Release 附件的校验值。
- 数据来源：OpenNeuro ds007857，版本 1.0.1；源数据声明 CC0。请引用上游数据集及相关研究；配套第三方软件遵循其自带许可。

## 推荐操作

1. 安装 Python 3.8 或更新版本。
2. 下载本 Release 的 `download_dataset.py`。
3. 在保存脚本的位置打开终端，执行：

```powershell
python download_dataset.py --output D:\MRI_project\dataset_Mi
```

macOS/Linux 示例：

```bash
python3 download_dataset.py --output ./dataset_Mi
```

脚本只使用 Python 标准库，自动下载配套资料及全部 MRI，还原原始受试者/session 目录，逐文件校验 SHA-256。再次运行会跳过内容一致的已有文件；如果目标位置存在不同内容的同名文件，会停止而不覆盖。

需要约 21 GB 的完整数据空间，以及配套压缩包缓存空间；建议至少预留 25 GB。下载失败后可再次执行同一命令。不要使用 GitHub 的 “Source code (zip)” 代替本数据集，它只包含 Git 仓库里的说明和下载脚本。

也可以单独下载某人的 MRI 附件；请按清单对应的目录放置，并配对其本人的 JSON 和标签。

## 质量状态

文件完整不等于已完成研究质控。当前头动筛查为初步结果，空间信息和扫描仪批次等问题仍需复核。下载后先阅读 `GUIDE.md` 及 `_work/qc/review_20261027/REVIEW.md`；不要把初步候选当成最终训练就绪队列。
