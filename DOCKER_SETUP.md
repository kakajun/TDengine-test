# TDengine Docker 安装指南 (Windows)

本指南介绍如何在 Windows 环境下使用 Docker 加载离线镜像并启动 TDengine 企业版。

## 1. 前置条件

*   已安装 **Docker Desktop** 并启动。
*   已获取镜像文件：`tdengine-tsdb-enterprise-docker-3.4.0.1-linux-x64.tar.gz`。
*   **重要**：确保本地没有运行其他的 TDengine 服务（占用 6041 端口）。

## 2. 加载镜像 (Load)

打开 PowerShell，进入镜像文件所在的目录，执行：

```powershell
docker load -i tdengine-tsdb-enterprise-docker-3.4.0.1-linux-x64.tar.gz
```

加载完成后，可以使用以下命令确认：
```powershell
docker images
# 应该能看到 tdengine/tsdb-ee-amd64 或类似的镜像名
```

## 3. 启动容器 (Run)

直接复制以下命令在 PowerShell 中执行（已适配 Windows 路径格式）：

```powershell
docker run -d --name taosdb-ee --restart always -p 6030:6030 -p 6048:6048 -p 6041-6047:6041-6047 -v E:\taodb\data:/var/lib/taos -v E:\taodb\cfg:/etc/taos tdengine/tsdb-ee-amd64:3.4.0.1
```

### 参数说明：
*   `-d`: 后台运行。
*   `--restart always`: 开机自启，挂了自动重启。
*   `-p 6041-6047:6041-6047`: 映射 RESTful API 和 WebSocket 端口（本项目使用 6041）。
*   `-v E:\taodb\data:/var/lib/taos`: **数据持久化**。将容器内的数据保存在 E 盘，防止删除容器后数据丢失。
    *   *如果您的电脑没有 E 盘，请改为 C 盘或其他路径，例如 `C:\taodb\data`。*

## 4. 验证运行

查看容器日志：
```powershell
docker logs -f taosdb-ee
```

如果看到类似 `TDengine is initialized successfully` 的提示，说明启动成功。

此时，您可以运行项目中的 `check_env.py` 脚本来验证连接：
```powershell
python check_env.py
```
