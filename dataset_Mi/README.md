# MiND 去重数据集

已按确认的身份规则完成整理：`mindo###` 与 `mindb###` 相同数字属于同一人，每对保留 `mindb`，移除对应 `mindo` 的数据和活动 ID。该规则覆盖 50 对；保留的 `mindb` 均对应更高的记录年龄和升级后的 UHP 扫描仪。

| 内容 | 整理前 | 整理后 |
| --- | ---: | ---: |
| 有影像的受试者 ID | 259 | **209** |
| CN / MCI | 210 / 49 | **160 / 49** |
| T1 MRI | 506 | **406** |
| 静息态 BOLD | 258 | **208** |
| MRI 总数 | 764 | **614** |
| 初步自动 QC 候选 | 73 | **56** |

仅处理跨 ID 的重复人；同一保留 ID 下的 mrs / placebo 两次 T1 均保留。影像内容、原始文件名及 SHA-256 不变。标签取保留 ID 的原记录，例如保留 `mindb278` 的 MCI 标签。原参与者表中不属于现有影像子集的 30 个 ID 也已从活动表中移除。

## 当前文件结构

```text
dataset_Mi/
├── README.md, GUIDE.md
├── download_dataset.py           # 下载当前整理版本
├── dataset_manifest.json         # 仅包含整理版本应还原的文件
├── subjects.csv                  # 209 人全体清单、标签、session 和路径
├── cohort.csv                    # 56 人初步 QC 候选；不是最终训练队列
├── ids/
│   ├── CN.txt                    # 160 个 ID
│   └── MCI.txt                   # 49 个 ID
├── rawdata/
│   ├── participants.tsv          # 与影像一致的 209 行
│   ├── participants.json
│   ├── dataset_description.json
│   └── sub-*/ses-*/anat|func/     # 下载后生成 MRI + 匹配 JSON
├── qc/
│   ├── all_candidates.csv
│   ├── subject_review.csv
│   ├── file_audit.csv
│   └── motion/sub-*/             # 下载后生成 motion/censor 表
└── provenance/
    ├── removed_ids.csv            # 50 对删除→保留映射，仅供审计
    └── selection.json             # 来源、处理规则及数量
```

## 下载整理后的数据

需要 Python 3.8+，只使用标准库。下载**本目录当前版本**的 `download_dataset.py`；`dataset_manifest.json` 可一并保存于脚本旁，未保存时脚本会自动获取并核对固定 SHA-256。

```powershell
python download_dataset.py --output D:\MRI_project\dataset_Mi_deduplicated
```

macOS/Linux：

```bash
python3 download_dataset.py --output ./dataset_Mi_deduplicated
```

需要约 16.5 GB 的 MRI 空间，另有 JSON、QC 表格及约 56 MB 配套缓存；建议预留至少 20 GB。脚本逐文件验证大小和 SHA-256，再次运行会跳过校验一致的文件。若下载目录含旧 ID 或不同内容的旧清单，脚本会停止；请使用新目录。

只查看整理后的配套表格、JSON 和运动记录，可运行：

```powershell
python download_dataset.py --output D:\MRI_project\dataset_Mi_metadata --support-only
```

此选项不下载 MRI，也不会将配套文件下载完成误报为影像下载完成。

**原 Release 保留为历史来源。** 当前下载器复用其中被保留的原始附件，只提取清单允许的 JSON 和 QC 文件；不会还原已删除 ID 或旧 `_work` 历史文件。请使用本目录下载器；旧 Release 附带的旧下载器仍会还原旧版 259 个 ID。GitHub 的 Source code ZIP 包含当前清单和脚本，不包含 614 份 MRI 本体。

## 数据状态

本次完成身份去重、标签同步和目录整理，未重新进行 MRI 预处理或人工影像 QC。56 人仍是初步自动候选，不能视为最终训练队列；现有 `training_ready` 均为 False。4 人仅能跨 session 配对，`mindm300` 仅有 T1；详情见 [GUIDE.md](GUIDE.md)。

来源：[OpenNeuro ds007857 v1.0.1](https://openneuro.org/datasets/ds007857/versions/1.0.1)。本目录是项目的 CN/MCI T1 + 静息态子集，源数据声明 CC0；引用原数据集及相关研究。被删 ID 的映射仅保留在审计文件中，不进入参与者表、分类 ID 清单或活动影像目录。
