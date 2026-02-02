import taosws

try:
    conn = taosws.connect("taosws://root:taosdata@localhost:6041")
    cursor = conn.cursor()
    cursor.execute("USE station_data")
    
    # 查询不同的 equ_code
    print("Executing query: SELECT DISTINCT equ_code FROM stable_gtjjlfgdzf")
    cursor.execute("SELECT DISTINCT equ_code FROM stable_gtjjlfgdzf")
    data = cursor.fetchall()
    
    print(f"\nFound {len(data)} distinct equ_code values:")
    equ_codes = [row[0] for row in data]
    # 排序以便查看
    equ_codes.sort()
    print(equ_codes)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
