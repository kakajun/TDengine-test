import taosws
import random
import math
from datetime import datetime, timedelta

# 配置
DB_NAME = "solar_power"
DSN = "taosws://root:taosdata@localhost:6041"

def generate_solar_data():
    print(f"开始生成模拟数据，目标数据库: {DB_NAME}...")
    
    try:
        conn = taosws.connect(DSN)
        cursor = conn.cursor()
        
        # 1. 建库
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} PRECISION 'ms' KEEP 365")
        cursor.execute(f"USE {DB_NAME}")
        
        # 2. 建超级表
        # meters: 逆变器数据
        # tags: location (场站), model (型号)
        print("正在创建超级表 meters...")
        cursor.execute("""
            CREATE STABLE IF NOT EXISTS meters (
                ts TIMESTAMP,
                current FLOAT,
                voltage FLOAT,
                power FLOAT,
                energy_daily FLOAT
            ) TAGS (
                location BINARY(64),
                model BINARY(64)
            )
        """)
        
        # 3. 模拟设备和数据
        # 两个场站，每个场站 2 台逆变器
        devices = [
            {"name": "d1", "location": "Station_A", "model": "Huawei-2000"},
            {"name": "d2", "location": "Station_A", "model": "Huawei-2000"},
            {"name": "d3", "location": "Station_B", "model": "Sungrow-1500"},
            {"name": "d4", "location": "Station_B", "model": "Sungrow-1500"},
        ]
        
        # 生成过去 7 天的数据，每 15 分钟一个点
        end_time = datetime.now()
        start_time = end_time - timedelta(days=7)
        
        total_rows = 0
        
        for dev in devices:
            tb_name = f"dev_{dev['name']}"
            print(f"正在为设备 {tb_name} ({dev['location']}) 生成数据...")
            
            # 建子表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {tb_name} 
                USING meters TAGS ('{dev['location']}', '{dev['model']}')
            """)
            
            curr_time = start_time
            values_buffer = []
            
            # 基础参数
            max_power = 100.0 if dev['location'] == 'Station_A' else 80.0 # Station A 功率更大
            daily_energy = 0.0
            
            while curr_time <= end_time:
                # 模拟光伏曲线：6点到18点有光照
                hour = curr_time.hour + curr_time.minute / 60.0
                
                power = 0.0
                if 6 <= hour <= 18:
                    # 正弦波模拟光照强度 (6点=0, 12点=1, 18点=0)
                    intensity = math.sin((hour - 6) * math.pi / 12)
                    # 加入一些随机波动 (云遮挡)
                    noise = random.uniform(0.8, 1.0)
                    power = max_power * intensity * noise
                
                # 电压通常比较稳定 (e.g., 220V 或 380V)
                voltage = 220.0 + random.uniform(-5, 5)
                # 电流 = 功率 / 电压
                current = (power * 1000) / voltage if voltage > 0 else 0
                
                # 累计发电量 (简单的累加模拟)
                # 这里简化处理：energy_daily 模拟当天的累计值
                if hour < 6.25: # 每天早上归零
                    daily_energy = 0
                else:
                    # 粗略积分：Power (kW) * 0.25h
                    daily_energy += power * 0.25
                
                # 格式化时间戳
                ts_str = curr_time.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                
                # 拼接 SQL 值部分
                # 注意：SQL 拼接效率较低，生产环境应使用 parameter binding 或 insert_many
                # 但 taos-ws-py 的 insert_many 写法需要注意版本，这里用最稳妥的逐批拼接 SQL
                values_buffer.append(
                    f"('{ts_str}', {current:.2f}, {voltage:.2f}, {power:.2f}, {daily_energy:.2f})"
                )
                
                if len(values_buffer) >= 100: # 每 100 条插入一次
                    sql = f"INSERT INTO {tb_name} VALUES " + " ".join(values_buffer)
                    cursor.execute(sql)
                    total_rows += len(values_buffer)
                    values_buffer = []
                
                curr_time += timedelta(minutes=15)
            
            # 插入剩余数据
            if values_buffer:
                sql = f"INSERT INTO {tb_name} VALUES " + " ".join(values_buffer)
                cursor.execute(sql)
                total_rows += len(values_buffer)
                
        print(f"\n🎉 数据生成完成！共插入 {total_rows} 条记录。")
        print("您现在可以运行 app.py 进行查询了。")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ 数据生成失败: {e}")

if __name__ == "__main__":
    generate_solar_data()
