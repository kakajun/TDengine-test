import re

def parse_query_slots(user_query):
    slots = {"station_code": None, "equ_codes": [], "date_start": None, "date_end": None, "metrics": [], "agg": None}
    m = re.findall(r"\b([a-z]{4,})\b", user_query, flags=re.I)
    if m:
        slots["station_code"] = m[0]
    eq = re.findall(r"\bF\d{2}\b", user_query)
    if eq:
        slots["equ_codes"] = eq
    d = re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", user_query)
    if d:
        day = d[0]
        slots["date_start"] = f"{day} 00:00:00"
        slots["date_end"] = f"{day} 23:59:59"
    if "一整天" in user_query or "全天" in user_query:
        if slots["date_start"] and slots["date_end"]:
            pass
    if "平均" in user_query:
        slots["agg"] = "avg"
    if "最大" in user_query:
        slots["agg"] = "max"
    if "最小" in user_query:
        slots["agg"] = "min"
    return slots

def merge_with_memory(slots, dialog_state, persistent_memory):
    ctx = {}
    ctx["station_code"] = slots.get("station_code") or dialog_state.get("station_code") or persistent_memory.get("station_code")
    ctx["equ_codes"] = slots.get("equ_codes") or dialog_state.get("equ_codes") or persistent_memory.get("equ_codes") or []
    ctx["date_start"] = slots.get("date_start") or dialog_state.get("date_start") or persistent_memory.get("date_start")
    ctx["date_end"] = slots.get("date_end") or dialog_state.get("date_end") or persistent_memory.get("date_end")
    ctx["metrics"] = slots.get("metrics") or dialog_state.get("metrics") or persistent_memory.get("metrics") or []
    ctx["agg"] = slots.get("agg") or dialog_state.get("agg") or persistent_memory.get("agg")
    return ctx
