"""Save the scoped JSON-stat response from Eurostat without changing its bytes."""
import hashlib
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent
BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_eb_ai"
params = [("lang", "EN"), ("geo", "EU27_2020"), ("unit", "PC_ENT"),
          ("freq", "A"), ("nace_r2", "C10-S951_X_K"), ("time", "2024"), ("time", "2025")]
params.extend(("size_emp", size) for size in ("GE10", "10-49", "50-249", "GE250"))
items = "TTM TSR TIR TML TPA TAR TNLG TPVSG TANY TGE2 TGE3".split()
params.extend(("indic_is", "E_AI_" + item) for item in items)
URL = BASE + "?" + urlencode(params)


def main():
    with urlopen(URL, timeout=90) as response:
        raw = response.read()
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    target = data / "eurostat.json"
    if target.exists() and raw != target.read_bytes():
        raise ValueError("The live response changed. Preserve this snapshot and review the revision.")
    target.write_bytes(raw)
    print(hashlib.sha256(raw).hexdigest(), target.name)


if __name__ == "__main__":
    main()
