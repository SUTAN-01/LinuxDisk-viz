# diskviz

Linux 磁盘占用可视化与文件管理 Web 工具。目标：1TB / 100 万文件首扫 < 15s。

## 特性

- **快速扫描**：C++ 扫描核心（fts_read + statx 线程池 + SQLite 缓存）
- **可视化**：Treemap（squarified 算法）+ 条形排行 + 目录下钻
- **文件管理**：查看 / 导航 / 删除 / 打包 / 下载 / 上传 / 移动 / 重命名 / 大文件与重复文件报告 / 导出
- **安全**：双 token 认证（read 浏览 / write 操作）+ 写操作二次确认 + safe_path 路径校验 + 审计日志
- **Web UI**：浏览器访问，SSH 隧道部署

## Quick Start

```bash
make build          # 构建 C++ scanner + 前端
make run            # 启动服务 http://localhost:8765
make test           # 跑全部单测
```

开发 token：`dev-read` / `dev-write`（见 `Makefile`）。

## 架构

三层解耦：

```
C++ scanner (CLI)  ──NDJSON──▶  Python FastAPI  ──HTTP/WS──▶  React/Canvas
                                   + SQLite 缓存
```

详见 [docs/architecture.md](./docs/architecture.md)。

## 部署

```bash
./scripts/package.sh                 # 打包 tar.gz
sudo ./scripts/install.sh dist/*.tar.gz   # 安装到目标机（systemd）
ssh -L 8765:127.0.0.1:8765 user@server    # SSH 隧道访问
```

详见 [docs/deployment.md](./docs/deployment.md)。

## 文档

- [架构](./docs/architecture.md)
- [REST API](./docs/api.md)
- [NDJSON 协议](./docs/ndjson-protocol.md)
- [部署](./docs/deployment.md)

## 目录结构

```
diskviz/
├── scanner/      # C++ 扫描核心（独立 CLI）
├── webapp/       # Python FastAPI Web 层
├── frontend/     # React + Canvas 前端
├── scripts/      # 构建 / 打包 / 安装 / 测试脚本
└── docs/         # 文档
```
