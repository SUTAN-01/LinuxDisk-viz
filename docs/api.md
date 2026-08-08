# REST API

Base URL: `http://<host>:8765`
认证：所有请求需 `Authorization: Bearer <token>` 或 query `?token=<token>`。
- **read-token**：可读所有端点。
- **write-token**：可读写所有端点；写操作另需 `confirm_token`（= `sha256(write-token)` 的 hex）。

## health

| Method | Path       | Token | 说明             |
|--------|------------|-------|------------------|
| GET    | `/health`  | read  | `{"status":"ok"}` |

## scan

| Method | Path                | Token | Body / Query                    | 说明                          |
|--------|---------------------|-------|---------------------------------|-------------------------------|
| POST   | `/scan`             | read  | `{"root":"/var","workers":8}`   | 启动扫描，返回 `{"scan_id"}`   |
| GET    | `/scan/{scan_id}`   | read  | —                               | 查状态（finished/last_progress）|
| DELETE | `/scan/{scan_id}`   | write | —                               | 取消扫描                       |
| WS     | `/ws/scan/{scan_id}`| read  | `?token=`                        | 实时推送 progress/warn/done 帧 |

## tree

| Method | Path                | Token | Query                    | 说明                  |
|--------|---------------------|-------|--------------------------|-----------------------|
| GET    | `/tree/{scan_id}`   | read  | `path=&depth=&limit=`    | 下钻查询某路径子条目  |

## file

| Method | Path                          | Token | Query     | 说明                  |
|--------|-------------------------------|-------|-----------|-----------------------|
| GET    | `/file/{scan_id}`             | read  | `path=`   | 文件 metadata         |
| GET    | `/file/{scan_id}/content`     | read  | `path=`   | 流式下载文件内容      |

## ops（写操作，需 write-token + confirm_token）

| Method | Path            | Body                                                | 说明            |
|--------|-----------------|-----------------------------------------------------|-----------------|
| POST   | `/ops/delete`   | `{paths, mode:"permanent"\|"trash", confirm_token}` | 删除            |
| POST   | `/ops/move`     | `{src_paths, dst_dir, confirm_token}`               | 移动            |
| POST   | `/ops/rename`   | `{path, new_name, confirm_token}`                   | 重命名          |
| POST   | `/ops/mkdir`    | `{path, confirm_token}`                             | 新建目录        |

## archive

| Method | Path                          | Token | Body / 说明                              |
|--------|-------------------------------|-------|------------------------------------------|
| POST   | `/archive/pack`               | write | `{paths, format:"tar.gz"\|"zip", confirm_token}` → `{job_id}` |
| GET    | `/archive/{job_id}`           | read  | 查打包状态                                |
| GET    | `/archive/{job_id}/download`  | read  | 下载打包结果                              |

## upload（tus-like）

| Method | Path                              | Header / 说明                              |
|--------|-----------------------------------|--------------------------------------------|
| POST   | `/upload?path=`                   | `Upload-Length` 头 → `{upload_id}`         |
| PATCH  | `/upload/{upload_id}`             | `Upload-Offset` 头 + body 分片             |
| POST   | `/upload/{upload_id}/complete?filename=` | rename tmp → 目标                  |

## reports

| Method | Path                                       | 说明                          |
|--------|--------------------------------------------|-------------------------------|
| GET    | `/reports/top-large/{scan_id}?limit=&min_size=` | 大文件排行               |
| POST   | `/reports/duplicates/{scan_id}`            | 触发去重任务 → `{job_id}`     |
| GET    | `/reports/duplicates/{scan_id}/{job_id}`   | 查去重任务状态                |
| GET    | `/reports/export/{scan_id}?format=csv\|json` | 导出                      |

## 错误码

| 状态 | 含义                          |
|------|-------------------------------|
| 401  | token 缺失/无效/权限不足      |
| 403  | confirm_token 缺失/错误       |
| 400  | 路径不安全（保护路径/越界）   |
| 404  | scan_id 或路径不存在          |
