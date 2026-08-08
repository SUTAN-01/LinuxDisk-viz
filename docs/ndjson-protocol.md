# NDJSON Protocol

scanner 通过 stdout 输出 NDJSON（Newline-Delimited JSON）：每帧一行 JSON，以 `\n` 结尾。
webapp 的 `ScanManager._handle_frame` 按 `type` 字段分发。

## 帧类型

### scan.start — 扫描开始

```json
{"type":"scan.start","root":"/var","started_at":1786097000,"scan_id":"scan-12345","workers":16}
```

### entry — 单个文件/目录条目

```json
{"type":"entry","path":"/var/log/syslog","size":6120234,"kind":"file","ext":"log",
 "mode":33188,"mtime":1786096000,"inode":1234,"uid":0,"gid":0,"nlink":1,"cached":false}
```

- `kind`：`file` / `dir` / `link`（注意：字段名是 `kind`，不是 `type`，避免与帧 type 冲突）。
- 目录额外含 `children` 计数。
- `cached`：true 表示该条目来自 SQLite 缓存命中（未重新 stat）。

### progress — 进度（每 N 个条目一次）

```json
{"type":"progress","scanned":12345,"dirs":100,"bytes_so_far":104857600,"elapsed_ms":5000,"eta_ms":1500}
```

### warn — 警告（stat 失败、权限拒绝等）

```json
{"type":"warn","path":"/root/secret","code":"EACCES","msg":"permission denied"}
```

### scan.end — 扫描结束

```json
{"type":"scan.end","scan_id":"scan-12345","total_entries":999,"total_bytes":4096,
 "elapsed_ms":3000,"cache_hits":10,"cache_misses":989,"cancelled":false}
```

## webapp 转发

`/ws/scan/{id}` WebSocket 向前端转发帧，但 `scan.end` 会被改写为：

```json
{"type":"done", ...scan.end 字段}
```

即 `type` 由 `scan.end` 变为 `done`，其余字段（total_entries/total_bytes/elapsed_ms 等）保留。

## 转义

scanner 的 `NdjsonWriter.escape_json` 处理 `"` `\\` `\n` `\r` `\t` `\b` `\f` 及 `< 0x20` 控制字符（`\u00XX`）。
路径中的中文、引号、换行均可安全传输。

## hash 子命令输出

`disk-scanner hash` 子命令从 stdin 读路径列表，输出重复组 NDJSON：

```json
{"type":"dup","size":4096,"hash_partial":"...","hash_full":"...","paths":["/a","/b"]}
```
