# 自动发布流程

推送 `vX.Y.Z` 标签后，`Release package` 工作流自动测试、构建 QPKG，并上传安装包、源码和 SHA-256 校验文件。

**标签是发布版本的唯一来源，无需先修改 `qpkg.cfg`。** 工作流仅在临时源码副本中将 `QPKG_VER` 写成标签版本；Git 提交和标签本身保持不变。

## 发布新版本

在包含最新工作流的提交上打标签，例如：

```sh
make test lint
git push origin main
git tag v1.0.1
git push origin v1.0.1
```

只接受 `v数字.数字.数字`，去掉 `v` 后不超过 QNAP 版本字段的 10 字符限制。自动新建的 Release 仍标记为测试版，因为尚未完成 NAS 实机验收。已有 Release 的标题、正文和稳定版/测试版设置保持不变。

包装器版本不会自动更新 Peach 镜像。更新 Peach 仍需核对上游并修改 `shared/image.txt` 的固定摘要。

## 为已有标签补发（不移动标签）

旧标签可能指向修复前的工作流，直接点击 Re-run 仍会执行旧代码。请打开 **Actions → Release package → Run workflow**：

- 选择包含修复的 `main` 分支。
- `tag` 填写现有标签，如 `v1.0.0`。
- 勾选 `publish`。

构建工具使用所选分支，但被打包的应用源码来自现有标签提交。生成的源码归档包含写入标签版本后的 `qpkg.cfg`、`RELEASE_BUILD.json`（原始源码和构建工具提交）、以及实际使用的 `release-tools/`。这些记录用于说明生成过程，标签不被改写。

如果已有公开 Release 尚无这些附件，工作流会补传；若任何同名附件已存在，工作流会在上传前报错，绝不覆盖公开附件。新 Release 先以草稿创建，全部上传成功才公开；失败后可重跑未公开草稿。

## 只验证构建

手动运行时不勾选 `publish`，则构建所选分支，不创建标签或 Release。版本仍来自输入的 `tag`，无需该标签实际存在。产物保存在本次运行 Artifact 中 14 天。

本地 Linux 安装 `build-essential rsync shellcheck`，在干净的已提交工作树运行：

```sh
make test lint
make release TAG=v1.0.1
# 或用当前工具构建一个旧标签：
bash scripts/build-release.sh v1.0.0 refs/tags/v1.0.0
```

产物位于 `dist/<tag>/`。输出目录已存在时会拒绝构建，避免混入旧文件。

## 自动检查与权限

流程校验标签格式、QDK 源码 SHA-256、QPKG 包尾和执行权限，以及包内配置/脚本与生成源码的逐字节一致性。旧标签恢复还会运行该标签的测试。错误会显示在日志和 GitHub Actions 的 Error annotation 中。

工作流使用仓库提供的 `GITHUB_TOKEN`，无需额外 PAT；仓库/组织须允许 Actions 和发布 job 的 `contents: write` 权限。

自动构建成功不等价于 NAS 实机安装、重启、媒体播放或硬件转码验证。
