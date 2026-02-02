import taosws
import pandas as pd

# TDengine 连接配置
TD_HOST = "localhost"
TD_PORT = "6041"
TD_USER = "root"
TD_PASS = "taosdata"
DATABASE = "station_data"

def get_db_connection():
    dsn = f"taosws://{TD_USER}:{TD_PASS}@{TD_HOST}:{TD_PORT}"
    return taosws.connect(dsn)

def fetch_dc_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 切换数据库
        cursor.execute(f"USE {DATABASE}")

        # 查询 stable_gtjjlfgdzf 表的 ts 和 dc 列，限制时间范围为 2026-01-28 全天
        sql = "SELECT ts, dc FROM stable_gtjjlfgdzf WHERE equ_code = 'F01' AND ts >= '2026-01-28 00:00:00' AND ts < '2026-01-29 00:00:00'"
        print(f"Executing SQL: {sql}")

        cursor.execute(sql)
        fields = [field[0] for field in cursor.description]
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        if not data:
            print("No data found.")
            return

        df = pd.DataFrame(data, columns=fields)

        # 保存为 CSV
        csv_filename = "stable_gtjjlfgdzf_dc.csv"
        df.to_csv(csv_filename, index=False, encoding='utf-8-sig')

        print(f"\nSuccess! Data saved to {csv_filename}")
        print(f"Total rows: {len(df)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_dc_data()
