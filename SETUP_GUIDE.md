# TDengine Windows 安装与配置指南

为了运行本项目，您需要在本地安装 TDengine 数据库。请按照以下步骤操作：

## 1. 下载 TDengine

1.  访问 TDengine 官方下载页面: [https://docs.taosdata.com/get-started/package/](https://docs.taosdata.com/get-started/package/)
2.  找到 **Windows** 版本。
3.  下载 **TDengine-server-3.x.x.x-Windows-x64.exe** (建议下载最新稳定版)。
    *   *注意：请确保下载的是 Server 版，而不是仅 Client 版。*

## 2. 安装

1.  双击下载的 `.exe` 安装包。
2.  在安装向导中：
    *   点击 **Install**。
    *   接受许可协议。
    *   保持默认安装路径即可。
    *   安装完成后，点击 **Finish**。

## 3. 启动服务 (重要)

安装完成后，服务可能不会自动启动。请务必手动启动一次：

1.  打开文件资源管理器，进入 `C:\TDengine` 目录。
2.  找到 **`start-all.bat`** 文件。
3.  右键点击该文件，选择 **“以管理员身份运行”**。
4.  等待几个黑框弹出并执行完毕。

## 4. 验证安装

安装完成后，TDengine 服务应该会自动启动。我们可以通过以下方式验证：

1.  按下 `Win + R` 键，输入 `cmd` 或 `powershell`，然后回车打开命令行。
2.  在命令行中输入以下命令并回车：
    ```bash
    taos
    ```
3.  如果您看到类似以下的欢迎信息，说明数据库安装成功并已启动：
    ```text
    Welcome to the TDengine shell from Linux, Client Version:3.x.x.x
    Copyright (c) 2022 by TAOS Data, Inc. All rights reserved.

    taos>
    ```
4.  输入 `exit` 并回车退出 TDengine 命令行。

## 4. 关键组件说明

本项目使用 WebSocket 协议连接数据库，依赖于 TDengine 的 `taosAdapter` 组件。
*   在 Windows 安装版中，`taosAdapter` 通常会自动随系统服务启动。
*   如果您后续运行 Python 脚本时提示“无法连接”，请检查服务是否开启（任务管理器 -> 服务 -> `taosd` 和 `taosadapter`）。

---
**准备就绪！**
确认以上步骤完成后，您就可以继续运行 Python 代码了。
