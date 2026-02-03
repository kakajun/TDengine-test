import taosws
import pandas as pd
from datetime import datetime

# TDengine 连接配置
TD_HOST = "192.168.2.110"
TD_PORT = "6041"
TD_USER = "root"
TD_PASS = "taosdata"
DATABASE = "station_data"

def get_db_connection():
    dsn = f"taosws://{TD_USER}:{TD_PASS}@{TD_HOST}:{TD_PORT}"
    return taosws.connect(dsn)

def fetch_data_days():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(f"USE {DATABASE}")

        # 使用 first(ts) 显式获取每个时间窗口的第一条记录的时间戳
        # 这样可以确保返回结果的第一列是时间，第二列是数量
        sql = "SELECT first(ts), count(*) FROM stable_gtjjlfgdzf INTERVAL(1d)"
        print(f"Executing SQL: {sql}")

        cursor.execute(sql)
        data = cursor.fetchall()

        # 打印列名辅助调试
        if cursor.description:
            fields = [field[0] for field in cursor.description]
            print(f"Columns: {fields}")

        cursor.close()
        conn.close()

        if not data:
            print("No data found.")
            return

        print(f"\nRaw data rows (first 3): {data[:3]}") # 调试用：打印前3行原始数据

        valid_days = []
        for row in data:
            # 此时 row 应该是 (ts, count)
            # 过滤掉没有数据的行（如果有）
            if len(row) >= 2:
                count = row[1]
                if count > 0:
                    valid_days.append(row[0])
            elif len(row) == 1:
                # 极端情况 fallback
                valid_days.append(row[0])

        print(f"\nTotal days with data: {len(valid_days)}")

        if valid_days:
            print("Dates with data (YYYY-MM-DD):")
            for ts_val in valid_days:
                date_str = "Unknown"
                try:
                    if isinstance(ts_val, str):
                        # 处理字符串格式，如 "2026-01-28 00:00:00.000"
                        if 'T' in ts_val:
                            dt = datetime.fromisoformat(ts_val.replace('Z', '+00:00'))
                        else:
                            # 尝试解析普通空格分隔的时间字符串
                            try:
                                dt = datetime.strptime(ts_val.split('.')[0], "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                # 如果解析失败，直接截取前10位
                                dt = None
                                date_str = ts_val[:10]

                        if dt:
                            date_str = dt.strftime("%Y-%m-%d")

                    elif isinstance(ts_val, datetime):
                        date_str = ts_val.strftime("%Y-%m-%d")

                    elif isinstance(ts_val, int):
                        # 处理时间戳
                        # TDengine 可能是 ms 或 us
                        if ts_val > 1000000000000000: # 微秒
                            dt = datetime.fromtimestamp(ts_val / 1000000.0)
                        elif ts_val > 1000000000000: # 毫秒
                            dt = datetime.fromtimestamp(ts_val / 1000.0)
                        else: # 秒
                            dt = datetime.fromtimestamp(ts_val)
                        date_str = dt.strftime("%Y-%m-%d")
                    else:
                        date_str = str(ts_val)[:10]

                    print(f"- {date_str}")

                except Exception as e:
                    print(f"- Raw: {ts_val} (Parse Error: {e})")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    fetch_data_days()
