# Peach QNAP

将 [Peach](https://github.com/peach-mitao/peach) 包装为 QNAP App Center 可手动安装的 QPKG，通过 Container Station 运行。

**非官方测试项目，尚未经过 NAS 实机验证。** 当前版本为包装器 `0.1.0`，固定使用 Peach `0.46.1` 镜像摘要，不自动追踪 `edge`。

## 支持范围

| 项目 | 当前要求或状态 |
| --- | --- |
| CPU | x86-64；以 TS-453Dmini / Intel J4125 为适配目标 |
| 系统 | QTS >= 5.2.0；目标配置为 QTS 5.2.10.3577 |
| 容器 | Container Station >= 3.1.2；目标配置为 3.1.2.1742 |
| 媒体 | 可选的单个本地共享目录，只读挂载 |
| 数据 | 独立 Docker 命名卷，卸载 QPKG 时保留 |
| 硬件转码 | 未启用，尚未验证 |

以上是包内检查和适配目标，不是已验证兼容设备清单。

## 安装

1. 从 [Releases](https://github.com/fatelei/peach-qnap/releases) 下载测试版 `.qpkg`，按附带 SHA-256 文件校验。
2. 启动 Container Station，在 App Center 选择「手动安装」。本包未签名，可能需要允许安装无有效数字签名的应用。
3. 等待镜像拉取完成，在 Container Station 确认 `peach-qnap` 为 `healthy`，访问 `http://NAS局域网IP:8900`。
4. 在容器终端执行 `peach token` 取得初始口令，登录后设置密码。
5. 按[安装说明](docs/installation.zh-CN.md)配置实际媒体目录；默认不挂载任何 NAS 文件夹。

首次启动需要联网访问 Docker Hub。默认监听所有 IPv4 接口，仅用于可信局域网；可通过 `BindAddress` 限制到 NAS 的局域网地址。

## 开发与构建

```sh
make test                 # Python 3；模拟 QNAP / Docker 命令
make lint                 # 需要 ShellCheck
make build                # Linux / QNAP，需安装 QNAP QDK 2.5.3
make release TAG=v0.1.0    # Linux，从内置 QDK 源码构建完整发布附件
```

详见 [BUILD.md](BUILD.md)、[验证记录](docs/validation.zh-CN.md)和[发布流程](docs/releasing.md)。已有测试覆盖启动失败、同名资源保护和卸载保留数据等行为，不等价于 NAS 安装或媒体播放测试。

推送新的 `vX.Y.Z` 标签会自动测试、构建并发布 Pre-release。标签版本必须与 `qpkg.cfg` 的 `QPKG_VER` 一致；Actions 中手动运行 `Release package` 只构建并保存产物，不发布。详见[发布流程](docs/releasing.md)。

## 项目结构

```text
config/                 QPKG 默认配置
shared/                 安装到 NAS 的启动脚本、镜像锁定文件及许可证
qpkg.cfg                QPKG 元数据和依赖要求
package_routines        安装检查及卸载保护
scripts/                发布构建、版本及包校验工具
tests/                  启动脚本和发布检查测试
docs/                   安装、验证及发布文档
LICENSES/               原包装代码及第三方许可证
vendor/                 对应版本 QDK 源码及来源说明
.github/                CI、Issue 和 PR 模板
dist/                   本地构建产物，不提交到 Git
```

## 贡献与安全

欢迎提交复现步骤、实机测试结果和改进 PR，见 [CONTRIBUTING.md](CONTRIBUTING.md)。涉及口令或鉴权的问题按 [SECURITY.md](SECURITY.md)处理，不要公开上传数据库、凭据或未脱敏日志。

## 许可证与来源

保留仓库初始的 [Apache-2.0](LICENSE) 许可；首次交付的包装代码继续按 [MIT](LICENSES/MIT.txt) 提供。QDK 源码和衍生补丁保留其 GPL 许可，Peach 镜像由上游按 AGPL-3.0-or-later 提供。本仓库不重新许可这些组件，具体文件范围、版本和来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

本项目不隶属于 QNAP 或 Peach 官方。
