import math
import pandas as pd

TEMP_FACTOR = {5:1.15, 10:1.10, 15:1.05, 20:1.00, 25:0.95,
               30:0.90, 35:0.85, 40:0.80}          # Table 1  :contentReference[oaicite:2]{index=2}:contentReference[oaicite:3]{index=3}
TRENCH_FACTOR = {1:1.00, 2:0.90, 3:0.85, 4:0.80, 5:0.75, 6:0.70}  # Table 2

def apparent_power(p_kw: float, q_kvar: float) -> complex:
    return complex(p_kw, q_kvar)

def line_current(s: complex, v_ll: float) -> float:
    """|I| = |S| / (√3 · V_LL)  (S in kVA, V in V, I in A)"""
    return abs(s) * 1000 / (math.sqrt(3) * v_ll)

def required_capacity(i_load: float, temp: int, n_circuits: int,
                      cable_type: str) -> float:
    """Reverse‑engineer the *min* 20 °C rating you need."""
    # single‑core counts as 3 cables per circuit for capacity derating
    n_cables = n_circuits * (3 if cable_type == "single" else 1)
    cap = i_load / (TEMP_FACTOR[temp] * TRENCH_FACTOR[n_cables])
    return cap

def col_by_keyword(df: pd.DataFrame, *keywords):
    for col in df.columns:
        name = col.lower()
        if all(k.lower() in name for k in keywords):
            return col
    raise KeyError(f"No column with keywords {keywords}")

def smart_filter(df, v_level, cap_needed, cable_type, placement):
    out = df.copy()

    voltage_col = col_by_keyword(out, "voltage", "level")
    code_col    = col_by_keyword(out, "cable", "code")
    current_col = col_by_keyword(out, "current", "capacity", "20")

    

    # 1) voltage match
    out = out[out[voltage_col].astype(str) == v_level]
    

    # 2) cable type
    if cable_type == "3-core":
        out = out[out[code_col].astype(str).str.contains("3x")]
    else:
        out = out[out[code_col].astype(str).str.contains("1x")]
    

     # 3) current‑rating  (look at *all* capacity columns)
    cap_cols = [c for c in out.columns if 'current capacity' in c.lower()]
    caps = out[cap_cols].apply(pd.to_numeric, errors='coerce')
    out = out[caps.max(axis=1) >= cap_needed]

    

    return out.reset_index(drop=True)
