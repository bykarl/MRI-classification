# FreeSurfer 软件安装与患者处理分开验收

新增 `scripts/install_freesurfer_software.py` 仅安装和检查固定的官方 FreeSurfer 8.2.0 软件，不挂载 Drive、不读取患者影像、不初始化 subject、不启动 recon-all。它不替代原 `freesurfer_pilot.py` 的完整患者输入预检。

使用前：本人已接受软件许可，个人 `license.txt` 位于 `/content/license.txt`；已运行 notebook P1，固定源码快照和哈希检查通过。脚本再次检查固定快照、Ubuntu/架构/AVX、有效内存及本地磁盘。许可内容不会输出、写入结果或提交 Git。

```bash
python install_freesurfer_software.py \
  --code-root /content/FYP_MRI_2C_Code_d8bdfa7a125c \
  --output /content/FYP_MRI_LiYang/software_install/NEW_UNIQUE_RUN \
  --license-accepted
```

结果保存在指定运行目录的 `state.json`，只有安装、版本、关键共享库、mri_convert 版本及 fsaverage 检查均通过才产生 `completed.json`。下载使用快照内官方 URL，先核对官网 MD5，再记录 SHA-256，通过 apt 安装；不自动运行可变补丁脚本。

Colab 的实际软件安装可用子进程写独立日志，使内核能够检查进度。不重复启动同一安装，不删除已有锁、失败记录、MRI 或检查点。当前 notebook 的安装专用格和状态格不包含私人许可内容，原 P5 默认关闭，勿重复点击两套安装入口。

软件验收通过不等于 2C 重建完成。重建前仍须用原流程确认患者输入 SHA、个人许可、相同软件配方与完整预检，并分别运行 C1/C2/C3；输出 82 项体积和 eTIV 仍需真实计算与人工 QC。

## 本次真实状态

- 已从用户附件上传许可到 Colab 文件面板；内核实测文件存在且非空；8 CPU/50.99 GiB/约225.7 GiB空闲检查通过。
- Drive 最终授权点击被自动安全审查拒绝，未授予额外账号权限。只读展开页面显示 Drive 全文件/文档读写删除、相册读取及用户信息等九项权限，继续此授权需用户明确确认。没有以其他工具或间接方式访问被拦截的 Drive。
- 因软件安装不需要患者数据，独立软件安装于 2026-11-10T15:33:57Z 启动。实际安装源码 SHA-256：`9cf3a2a1da845193dd221d9305d6fc467fef46d9f77d08dbdd4751cbbc5b3ca9`。首次进度检查显示正在下载官方 Ubuntu24 包，尚未报告安装通过。
- 未运行 C1/C2/C3、真实 FreeSurfer 分割、体积提取、编码器或训练；未完成的结果不得写成通过。
