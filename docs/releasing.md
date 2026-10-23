# 自动发布流程

推送 `vX.Y.Z` 标签后，`Release package` 工作流会依次完成：

1. 校验标签格式、QNAP 的 10 字符版本限制，以及 `qpkg.cfg` 中的 `QPKG_VER`。
2. 运行全部 Python 测试、ShellCheck 和 shell 语法检查。
3. 校验内置 QDK 源码的 SHA-256，在 Ubuntu 上编译 QDK 的校验工具并构建 x86-64 QPKG。
4. 校验安装包的包尾、执行权限，以及包内配置和脚本与源码的一致性。
5. 从同一个提交生成源码归档（包含 QDK 源码和许可证），生成 SHA256SUMS.txt。
6. 上传 Actions Artifact，然后创建 GitHub Pre-release 并附上 `.qpkg`、`-source.tar.gz` 和校验文件。

## 发布新版本

例如发布包装器 0.1.1（这不会自动更新 Peach 镜像）：

```sh
# 先将 qpkg.cfg 中 QPKG_VER 改成 "0.1.1"，并更新 CHANGELOG.md
make test lint
git add qpkg.cfg CHANGELOG.md
git commit -m "Release 0.1.1"
git push origin main
git tag v0.1.1
git push origin v0.1.1
```

必须在包含 `release.yml` 的提交上打标签。旧的 v0.1.0 标签不会自动获得新工作流，也无需删除或移动。只接受 `v数字.数字.数字`；当前所有自动 Release 都标记为测试版，因为 NAS 实机验收尚未完成。

更新 Peach 本身需要单独核对上游版本并更新 `shared/image.txt` 的固定摘要。发布记录会列出实际镜像摘要和源码提交。

## 只验证构建，不发布

在 GitHub Actions 中打开 **Release package → Run workflow**，选择目标分支，填写与该分支 `QPKG_VER` 相同的标签形式版本。手动运行不会创建标签或 Release；产物保存在本次运行的 Artifact 中 14 天。

本地 Linux 可安装 `build-essential rsync`，在干净的已提交工作树中运行：

```sh
make test lint
make release TAG=v0.1.0
```

产物位于 `dist/v0.1.0/`。同一输出目录已存在时会报错，避免混入旧文件；需要重建时先自行清理这一生成目录。

## 失败与重跑

版本不一致、测试或构建失败时不发布。上传附件前先创建草稿，全部上传成功才公开。失败后可以重跑尚未公开的草稿版本；已经公开的 Release 会被保护，工作流不会覆盖其附件。

不需要额外设置 PAT，工作流使用仓库自动提供的 `GITHUB_TOKEN`。仓库/组织必须允许 Actions 及发布 job 的 `contents: write` 权限。

真实 NAS 安装、重启、升级、媒体权限和卸载仍需实机验证；自动构建成功不等价于设备兼容性认证。
