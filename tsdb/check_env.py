import taosws
import sys


def check_connection():
    print("正在尝试连接 TDengine 数据库...")
    dsn = "taosws://root:taosdata@localhost:6041"

    try:
        # 尝试连接
        conn = taosws.connect(dsn)
        print("\n✅ 连接成功！")
        print("-" * 30)
        # print(f"Server Info: {conn.server_info}") # 部分版本不支持

        # 简单查询测试
        cursor = conn.cursor()
        cursor.execute("SELECT server_version()")
        version = cursor.fetchone()[0]
        print(f"Server Version: {version}")

        cursor.close()
        conn.close()
        print("-" * 30)
        print("您的环境配置正确，可以进行下一步操作。")
        return True

    except Exception as e:
        print("\n❌ 连接失败")
        print("-" * 30)
        print(f"错误信息: {e}")
        print("-" * 30)
        print("排查建议：")
        print("1. 确保 TDengine 已经安装并启动 (尝试在命令行运行 'taos' 检查)")
        print("2. 确保 taosAdapter 服务已启动 (默认端口 6041)")
        print("3. 检查用户名密码是否为默认的 root/taosdata")
        return False


if __name__ == "__main__":
    success = check_connection()
    if not success:
        sys.exit(1)
