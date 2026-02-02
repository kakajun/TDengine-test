import json
import os

def load_mapping():
    primary = "column_mapping.json"
    backup = "db_column_mapping.json"
    mapping = {}
    if os.path.exists(primary):
        try:
            with open(primary, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except:
            mapping = {}
    if not mapping and os.path.exists(backup):
        try:
            with open(backup, "r", encoding="utf-8") as f:
                mapping = json.load(f)
        except:
            mapping = {}
    return mapping

SYNONYMS_TO_KEYS = {
    "发电机有功功率": ["dc"],
    "有功功率": ["dc"],
    "有功": ["dc"],
    "功率": ["dc"]
}

def tokenize(text):
    return list(set([c for c in text.lower() if c.strip()]))

def get_relevant_columns(user_query, context, mapping, k=40):
    descs = mapping
    tokens = []
    q = user_query
    for s in SYNONYMS_TO_KEYS.keys():
        if s in q:
            tokens.append(s)
    metrics_keys = []
    for s, ks in SYNONYMS_TO_KEYS.items():
        if s in q:
            metrics_keys.extend(ks)
    scores = {}
    for col, desc in descs.items():
        s = 0
        for t in tokens:
            if t in str(desc):
                s += 1
        scores[col] = s
    sorted_cols = sorted(descs.keys(), key=lambda c: scores.get(c, 0), reverse=True)
    result = []
    if "ts" not in result:
        result.append("ts")
    for mk in metrics_keys:
        if mk in descs and mk not in result:
            result.append(mk)
    for c in sorted_cols:
        if c not in result:
            result.append(c)
        if len(result) >= k:
            break
    lines = []
    for c in result:
        if c == "ts":
            lines.append("      - ts (TIMESTAMP): 时间戳")
        else:
            lines.append(f"      - {c} (DOUBLE): {descs.get(c, '')}")
    return result, "\n".join(lines)
