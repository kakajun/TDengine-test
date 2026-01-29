# TDengine 数据导入操作记录

本文档记录了将 `test.tar.gz` 数据包导入到 Docker 容器 `taosdb-ee` 中的完整过程。

## 1. 环境信息
- **源数据文件**: `test.tar.gz` (包含 `taosdump` 导出的数据和 SQL)
- **目标容器**: `taosdb-ee`
- **TDengine 版本**: Enterprise 3.4.0.1 (容器镜像 `tdengine/tsdb-ee-amd64:3.4.0.1`)

## 2. 操作步骤

### 第一步：将数据包复制到容器
将宿主机上的压缩包传输到容器的临时目录：

```bash
docker cp test.tar.gz taosdb-ee:/tmp/test.tar.gz
```

### 第二步：解压数据
在容器内部创建目录并解压文件：

```bash
docker exec taosdb-ee bash -c "mkdir -p /tmp/restore_data && tar -xzf /tmp/test.tar.gz -C /tmp/restore_data"
```

解压后的数据目录结构通常为：`/tmp/restore_data/test`

### 第三步：执行数据恢复
使用容器内置的 `taosdump` 工具进行数据恢复。
*注意：在该容器版本中，`taosdump` 位于 `/usr/bin/taosdump`。*

```bash
docker exec taosdb-ee /usr/bin/taosdump -u root -p taosdata -i /tmp/restore_data/test
```

**命令参数说明：**
- `-u root -p taosdata`: 指定数据库用户名和密码（默认为 root/taosdata）。
- `-i /tmp/restore_data/test`: 指定输入目录（即包含 dump 数据的文件夹）。

### 第四步：验证结果
执行成功后，控制台会输出 `OK: XXXXX row(s) dumped in!`。
可以通过 CLI 查看导入的数据库：

```bash
docker exec taosdb-ee taos -s "SHOW DATABASES;"
```

## 3. 故障排查笔记
- **找不到命令**: 如果直接运行 `taosdump` 报错，尝试使用绝对路径 `/usr/bin/taosdump`。
- **输入路径**: `taosdump -i` 后的路径必须是包含 `dbs.sql` 和数据文件夹的**父目录**（在本例中是解压出的 `test` 文件夹）。
