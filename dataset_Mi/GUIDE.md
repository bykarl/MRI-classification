# 整理后的 MiND 数据说明

本目录按用户确认的身份规则整理：相同数字、不同 `mindo` / `mindb` 前缀属于同一人。50 对各保留 `mindb`，对应 `mindo` 的全部影像、JSON、活动标签与 QC 行均不再纳入。所有保留的 `mindb` 在原表中年龄更大，扫描仪为升级后的 UHP；这是一条固定的选择规则，不代表重新评估过影像质量。

当前为 **209 个唯一编号：CN 160、MCI 49**。保留 ID 内全部原有 session，因此有 **406 份 T1 + 208 份静息态 BOLD，共 614 份 MRI**。T1 与 BOLD 是不同模态；本次没有删除保留 ID 内的第二次 T1。影像与对应 JSON 的原内容和 SHA-256 保持不变。

`subjects.csv` 是全体 209 人的入口；`cohort.csv` 是筛选后的 **56 人初步自动 QC 候选**（CN 47、MCI 9），不是全体受试者清单或最终训练队列。`ids/` 与 `rawdata/participants.tsv` 仅列实际保留的 209 个 ID；原表中无本子集影像的 30 行不再出现在活动表中。

## 下载后的目录

```text
dataset_Mi/
├── GUIDE.md
├── subjects.csv                  # 全体受试者、标签及影像路径
├── cohort.csv                    # 保留 ID 中的初步 QC 候选
├── ids/CN.txt, MCI.txt            # 分类 ID 清单
├── rawdata/
│   ├── participants.tsv, participants.json, dataset_description.json
│   └── sub-*/ses-*/anat|func/     # 614 份原始 MRI 与 614 份匹配 JSON
├── qc/
│   ├── all_candidates.csv, subject_review.csv, file_audit.csv
│   └── motion/sub-*/motion.tsv, censor.tsv
└── provenance/
    ├── removed_ids.csv            # 50 对删除/保留映射，仅供审计
    └── selection.json             # 规则、来源、前后数量和限制
```

Git 目录存放清单、表格与下载脚本；体积较大的 MRI、JSON 和逐帧运动表由脚本按清单从原 Release 还原。脚本不会展开旧版全部 `_work/`，因此不会把被删 ID、旧清单或过期统计重新放回数据目录。原 Release 保留为历史来源；使用当前目录的下载器和清单获取本次整理版本。

## 标签和配对

- CN=0、MCI=1。保留 ID 的年龄、性别、诊断标签与该 ID 的原表一致，不移用被删除时间点的标签。
- `sub-mindo278` 为 CN，已移除；保留 `sub-mindb278` 的 MCI 标签。
- 4 人只能跨 session 配对：sub-mindm388, sub-mindo114, sub-mindo172, sub-mindo238。`sub-mindm300` 只有 T1，没有 BOLD。不要将这些人标成同次完整配对。
- `primary_t1_path` 优先指向 placebo，与已有 BOLD 同 session；缺失时指向 mrs。其他 T1 继续保留。

## 质量记录与使用

本次只完成身份去重、清单同步和结构整理，没有重新下载读取 614 份 MRI、重跑运动校正或进行新的人工影像 QC。`qc/file_audit.csv` 继承原快照的完整性及几何检查；逐帧 motion/censor 保留原记录。当前训练就绪人数仍为 0。

空间信息、扫描仪批次和 fMRI 预处理问题仍需复核。初步候选中同扫描仪子集为 43 人；没有因为此次去重重新放宽 QC 阈值。原始 BOLD 没有实际删帧或去噪。训练/验证/测试须按人划分，所有 session 和模态保持同组。

数据来源：OpenNeuro ds007857 v1.0.1，源数据声明 CC0。引用原数据集及相关研究，原图像许可及来源说明保留在 `rawdata/dataset_description.json`。
