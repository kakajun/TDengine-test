import taosws
import pandas as pd

def get_db_connection(td_host, td_port, td_user, td_pass):
    dsn = f"taosws://{td_user}:{td_pass}@{td_host}:{td_port}"
    return taosws.connect(dsn)

def execute_query(sql, td_host, td_port, td_user, td_pass, database, column_mapping):
    conn = get_db_connection(td_host, td_port, td_user, td_pass)
    cur = conn.cursor()
    cur.execute(f"USE {database}")
    cur.execute(sql)
    fields = [f[0] for f in cur.description]
    data = cur.fetchall()
    cur.close()
    conn.close()
    df = pd.DataFrame(data, columns=fields)
    if column_mapping:
        rename = {k: v for k, v in column_mapping.items() if k in df.columns}
        if rename:
            df = df.rename(columns=rename)
    return df
