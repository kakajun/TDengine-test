import taosws
import json

try:
    # Get DB columns
    conn = taosws.connect("taosws://root:taosdata@localhost:6041")
    cursor = conn.cursor()
    cursor.execute("USE station_data")
    cursor.execute("DESCRIBE stable_gtjjlfgdzf")
    data = cursor.fetchall()
    db_cols = set([row[0] for row in data])

    # Load full mapping
    with open('d:\\git\\TDengine-test\\column_mapping.json', 'r', encoding='utf-8') as f:
        full_mapping = json.load(f)

    # Filter
    final_mapping = {}
    for col, desc in full_mapping.items():
        if col in db_cols:
            final_mapping[col] = desc

    # Save filtered mapping
    with open('d:\\git\\TDengine-test\\db_column_mapping.json', 'w', encoding='utf-8') as f:
        json.dump(final_mapping, f, ensure_ascii=False, indent=2)

    print(
        f"Filtered mapping saved. {len(final_mapping)} columns matched out of {len(db_cols)} in DB.")

except Exception as e:
    print(f"Error: {e}")
