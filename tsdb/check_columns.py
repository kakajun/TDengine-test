import taosws

try:
    conn = taosws.connect("taosws://root:taosdata@192.168.2.110:6041")
    cursor = conn.cursor()
    cursor.execute("USE station_data")
    cursor.execute("DESCRIBE stable_gtjjlfgdzf")
    data = cursor.fetchall()
    cols = [row[0] for row in data]
    print(cols)

except Exception as e:
    print(f"Error: {e}")
