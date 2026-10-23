# Peach for QNAP：测试安装包

目标设备：TS-453Dmini（Intel J4125 / x86-64），适配目标系统为 QTS 5.2.10.3577、Container Station 3.1.2.1742。

这是非官方容器型 QPKG。安装器版本由发布标签生成，上游应用版本 Peach 0.46.1。安装包不包含容器镜像，首次启动需要 NAS 能连接第三方镜像代理 `docker.1ms.run`。代理地址只改变下载来源，固定 SHA256 摘要与上游一致。镜像约 260 MB 压缩下载，解压和运行还需额外空间；图片缓存会随使用增长。

## 安装

1. 确认 Container Station 已启动，NAS 的 8900 端口未被其他应用占用。
2. 在 App Center 中选择「手动安装」，选择从 Releases 下载的 `PeachQNAP_<版本>_x86_64.qpkg`。
3. 本包没有 QNAP 数字签名。如果系统阻止安装，需要在 App Center 设置中允许安装无有效数字签名的应用；是否保留该选项由你决定。
4. 首次启动会拉取固定镜像，耗时取决于网络。打开 Container Station，确认 `peach-qnap` 容器进入 `healthy` 状态。
5. 在同一浏览器登录 QTS 管理员账号，点击 App Center 的 Peach 图标，打开访问设置页。
6. 输入两次新密码并保存，点击「进入 Peach」登录。已有密码也可由 QTS 管理员在此重置，无需 SSH。升级本身不会修改现有密码。

管理页位于 QTS 管理端口的 `/cgi-bin/peach-qnap.cgi`，不是 8900 端口。QTS 会话过期或不是管理员时会拒绝访问。请使用与 QTS 登录一致的主机名/IP；推荐通过 QTS HTTPS 访问。若图标仍缓存旧入口，刷新 QTS 页面或重新登录。QTS 管理页注册失败时，原来的 `http://NAS局域网IP:8900` 仍可用于登录 Peach。

如管理页暂时无法验证 QTS 会话，也可在 NAS 的 SSH 终端执行以下命令取得初始口令（口令只应在你自己的终端查看）：

```sh
/etc/init.d/peach-qnap.sh token
```

初始配置监听所有 IPv4 接口。仅在可信局域网中使用，不要做公网端口转发。可在下述配置文件中把 `BindAddress` 改为 NAS 的局域网 IPv4 地址，以限制监听接口。

## 添加影片目录

为了让安装者自行选择影片目录，默认不挂载任何 NAS 媒体。首次打开可以登录，但还不能扫描影片。

通过 NAS SSH 以管理员权限执行以下命令，把示例 `/share/Multimedia` 换成**实际已存在的影片目录**：

```sh
APP_DIR=$(/sbin/getcfg PeachQNAP Install_Path -f /etc/config/qpkg.conf)
/sbin/setcfg PeachQNAP MediaPath '/share/Multimedia' -f "$APP_DIR/peach-qnap.conf"
/etc/init.d/peach-qnap.sh restart
```

然后在 Peach 网页的媒体目录设置中填写 `/media`，或其中的子目录，例如 `/media/Movies`。

容器按上游默认的 UID/GID 1000 运行；NAS 的目录及文件权限需要允许该用户读取和遍历。不要为排查问题对整个共享目录执行 `chmod 777` 或递归改属主。媒体挂载为只读，因此不能通过此安装包整理、移动或删除源文件。

目录包含空格可以使用；逗号和换行不支持。这里只支持普通本地媒体目录，CloudDrive2 后续动态挂载传播未适配。

若要修改端口，例如 18900：

```sh
APP_DIR=$(/sbin/getcfg PeachQNAP Install_Path -f /etc/config/qpkg.conf)
/sbin/setcfg PeachQNAP Port 18900 -f "$APP_DIR/peach-qnap.conf"
/etc/init.d/peach-qnap.sh restart
```

## 启停、卸载与数据

- App Center 的启用/停止控制容器；容器使用 `unless-stopped` 策略，手动停止后不会因 Docker 重启而自行启动。
- 配置、数据库和缓存保存在 Docker 命名卷 `peach-qnap-data`，不在媒体目录中。
- 卸载 QPKG 会删除它管理的容器，但**保留数据卷和镜像**。重新安装会复用数据。QPKG 自身的媒体目录/端口配置在卸载时删除，重装后需要重新填写。
- 不要在 Container Station 中删除 `peach-qnap-data`；删除会丢失馆藏数据库、配置和凭据。
- QPKG 升级保留 `peach-qnap.conf`。当前包固定镜像摘要，不随 `edge` 自动更新。升级上游 Peach 前须先停机备份整个数据卷；数据库迁移需按上游说明处理。
- 如果 Container Station 停止，先恢复它再停用或卸载 Peach，避免留下仍可能启动的容器。

## 故障排查和测试边界

在 Container Station 查看 `peach-qnap` 的日志；也可执行：

```sh
/etc/init.d/peach-qnap.sh status
```

镜像下载失败：检查 NAS 到 `docker.1ms.run` 的连接及代理的访问或限流要求。已有同名容器或同名数据卷且没有本包标记时，安装脚本会拒绝接管；它不会删除你的其他部署。

没有开启 GPU 设备透传，也没有补装 J4125 所需的 Intel VAAPI 驱动。硬件转码尚未验证；浏览器能直接播放的媒体可直接播放，转码负载取决于实际片源。

此包尚未在用户的 NAS 上安装验证。QNAP App Center 安装、开机启动、NAS 共享目录 ACL 和真实影片播放，都需要实机验收。具体已完成的本机检查见[验证记录](validation.zh-CN.md)。

## 来源与版本

- [Peach 项目](https://github.com/peach-mitao/peach)，[Docker 部署说明](https://github.com/peach-mitao/peach/blob/master/docs/DOCKER.md)
- 容器：`longmeidao/peach:0.46.1`
- 固定摘要：`sha256:8b949a03460a41952a3c7e5c8394145dd04a063d2759de4243c0487337fbfe16`
- [QNAP QDK](https://github.com/qnap-dev/QDK)，构建使用 2.5.3，提交 `b7b5f4c86ebe95b10a62d64725515e7cdcf4bb35`
- 包装脚本源码位于 [仓库根目录](../)。脚本为 MIT；Peach 镜像由上游提供，适用 AGPL-3.0-or-later。QDK 安装框架适用其 GPL 许可证。
