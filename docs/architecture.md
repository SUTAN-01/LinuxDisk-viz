# Architecture

diskviz 是一个三层解耦的 Linux 磁盘占用可视化与文件管理工具，目标：1TB / 100 万文件首扫 < 15s。

## 三层结构

```
┌─────────────┐   NDJSON(stdout)   ┌──────────────────┐   HTTP/WS    ┌─────────────┐
│ C++ scanner │ ─────────────────▶ │ Python FastAPI    │ ───────────▶ │ React/Canvas │
│  (CLI 独立)  │                    │  subprocess 编排   │              │  前端 SPA    │
└─────────────┘                    └──────────────────┘              └─────────────┘
        │                                  │
        └──── SQLite WAL (缓存/结果) ◀──────┘
```

### 1. scanner/ — C++ 扫描核心（独立 CLI）

- **遍历**：`fts_read` 单线程读目录，避免多线程 `readdir` 引发的磁头寻道风暴。
- **stat**：`statx` 线程池（moodycamel::ConcurrentQueue 分发路径），并发采集 size/mtime/inode 等。
- **缓存**：SQLite WAL 模式，按 `(dev, inode, mtime, size)` 命中即跳过 stat。
- **输出**：NDJSON 流式 stdout（每帧一行 JSON），由 webapp 解析。
- **去重**：`hash` 子命令用 xxhash64（先 partial 4KB，再 full）按需计算。
- **可独立运行**：`disk-scanner --root /var --ndjson --workers 8`，无需 webapp。

### 2. webapp/ — Python FastAPI Web 层

- **subprocess 编排**：`ScanManager` spawn scanner 进程，pump stdout 解析 NDJSON 帧，写入 `ScanStore`。
- **结果存储**：每个 scan 一个独立 SQLite（`scans_dir/scan-<id>.sqlite`），WAL + `synchronous=NORMAL`。
- **双 token 认证**：read-token 浏览，write-token 操作；写操作再需 `confirm_token`（= sha256(write-token)）。
- **WebSocket**：`/ws/scan/{id}` 实时推送 progress/warn/done 帧。
- **文件操作**：`file_ops` 服务做 `safe_path` 校验（拦截 `/proc /sys /etc /boot` 等保护路径 + 拒绝扫描根外路径）。
- **审计**：所有写操作记录到 jsonl 审计日志。
- **清理**：`cleanup_expired_scans` 协程定期删除过期 SQLite。

### 3. frontend/ — React + Canvas 前端

- **三栏布局**：左栏（视图切换/报告/历史）+ 中栏（Treemap 为主视图）+ 右栏（详情/操作）。
- **Treemap**：Canvas + squarified 算法，按扩展名着色，点击下钻，hover tooltip。
- **条形排行**：虚拟列表（仅渲染可见窗口 + overscan），按 size 降序。
- **状态**：Zustand（token/scanId/selectedEntry）+ `useUrlState`（view/path 同步到 URL）。
- **写操作二次确认**：`ConfirmDialog` 要求重输 write-token，计算 sha256 作为 confirm_token。
- **错误处理**：`ApiClient` 401→清 token 回登录，403→重输 write-token，WS 断线→红条 ErrorBanner。

## 通信协议

- scanner → webapp：NDJSON（见 [ndjson-protocol.md](./ndjson-protocol.md)）。
- webapp → frontend：REST + WebSocket（见 [api.md](./api.md)）。

## 性能要点

| 瓶颈点         | 方案                                              |
|----------------|---------------------------------------------------|
| 目录遍历寻道   | fts_read 单线程                                   |
| stat 并发      | statx 线程池 + ConcurrentQueue                    |
| 重复 stat      | SQLite WAL 缓存（mtime+size 未变即命中）          |
| 大目录查询     | entries 表 parent 索引 + LIMIT                    |
| 前端渲染       | Canvas（非 DOM）+ 虚拟列表                        |
