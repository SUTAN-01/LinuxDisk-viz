# Deployment

diskviz 部署在目标 Linux 机器上，单进程，通过 SSH 隧道访问。

## 前置依赖

- Ubuntu 22.04+ / Debian 12+ / CentOS 9+
- build essentials（gcc/g++ ≥ 11，cmake ≥ 3.16）
- Python 3.10+
- Node.js 18+（仅构建前端时需要）

## 1. 构建（在有源码的机器上）

```bash
./scripts/build.sh
```

构建产物：
- `scanner/build/disk-scanner` — C++ 二进制
- `webapp/diskviz_api/static/` — 前端静态资源

## 2. 打包

```bash
./scripts/package.sh
# → dist/diskviz-<version>-linux-<arch>.tar.gz
```

## 3. 安装到目标机

把 tar.gz 拷到目标机，然后：

```bash
sudo ./install.sh dist/diskviz-*.tar.gz
```

安装脚本会：
- 解压到 `/opt/diskviz`
- `pip install -e` 安装 webapp（生成 `diskviz-serve` 命令）
- 拷贝 systemd unit 到 `/etc/systemd/system/diskviz.service`
- 生成随机 read/write token 到 `/etc/diskviz/env`（权限 600）
- `systemctl enable --now diskviz`

## 4. 访问（SSH 隧道）

服务默认绑定 `127.0.0.1:8765`（仅本机）。通过 SSH 隧道访问：

```bash
ssh -L 8765:127.0.0.1:8765 user@server
# 本机浏览器打开 http://localhost:8765
```

登录时输入 `/etc/diskviz/env` 中的 token：
- read-token：浏览
- write-token：文件操作

## 5. 配置

环境变量（`/etc/diskviz/env`）：

| 变量                    | 默认        | 说明                          |
|-------------------------|-------------|-------------------------------|
| `DISKVIZ_READ_TOKEN`    | —           | 只读 token（必填）            |
| `DISKVIZ_WRITE_TOKEN`   | —           | 写 token（必填）              |
| `DISKVIZ_SCANNER_BINARY`| —           | disk-scanner 路径             |
| `DISKVIZ_SCANS_DIR`     | —           | scan SQLite 存放目录          |
| `DISKVIZ_BIND_HOST`     | 127.0.0.1   | 监听地址                      |
| `DISKVIZ_BIND_PORT`     | 8765        | 监听端口                      |
| `DISKVIZ_SCAN_TTL_SECONDS` | 86400    | scan 结果保留时长（秒）       |

改完 `systemctl restart diskviz`。

## 6. 运维

```bash
systemctl status diskviz        # 状态
journalctl -u diskviz -f        # 日志
systemctl restart diskviz       # 重启
```

scan 结果 SQLite 存于 `DISKVIZ_SCANS_DIR`，过期（超过 `SCAN_TTL`）会被自动清理。

## 7. 验证（smoke test）

```bash
./scripts/smoke_test.sh
```

跑通 C++/Python/前端单测 + 完整构建 + curl `/health` 和 `/scan`。
