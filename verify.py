"""Verify every LP endpoint with feasible witnesses and dual bounds, without an optimizer."""

import csv
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ERROR = 2e-6
ITEMS = "TTM TSR TIR TML TPA TAR TNLG TPVSG".split()
SIZES = {"GE10", "10-49", "50-249", "GE250"}
MODES = {"all_published_counts", "without_multi_use_counts"}


def records(name):
    with (ROOT / "results" / name).open() as file:
        return list(csv.DictReader(file))


def source_values():
    data = json.loads((ROOT / "data/eurostat.json").read_bytes())
    dimensions = [
        [
            v
            for v, _ in sorted(
                data["dimension"][d]["category"]["index"].items(), key=lambda pair: pair[1]
            )
        ]
        for d in data["id"]
    ]
    output = {}
    for offset, coordinates in enumerate(itertools.product(*dimensions)):
        if str(offset) in data["value"]:
            point = dict(zip(data["id"], coordinates))
            key = point["size_emp"], point["time"], point["indic_is"][5:]
            output[key] = data["value"][str(offset)]
    expected = {
        (s, y, i)
        for s in SIZES
        for y in ("2024", "2025")
        for i in ITEMS + ["TANY", "TGE2", "TGE3"]
        if y == "2025" or i != "TPVSG"
    }
    assert set(output) == expected and len(output) == 84
    saved = {
        (r["size"], r["year"], r["indicator"]): float(r["pct"]) for r in records("source_cells.csv")
    }
    assert saved == output
    return output


def indicators(bits, codes):
    count = bits.count("1")
    result = dict(zip(ITEMS, (int(x) for x in bits)))
    result.update(TANY=int(count >= 1), TGE2=int(count >= 2), TGE3=int(count >= 3))
    return {code: result[code] for code in codes}


def check_witness(values, year, size, mode, proof):
    items = ITEMS if year == "2025" else ITEMS[:-1]
    codes = items + ["TANY"] + (["TGE2", "TGE3"] if mode == "all_published_counts" else [])
    up, down = proof["upper_dual"], proof["lower_dual"]
    assert set(up) == set(down) == set(codes)
    assert all(y <= ERROR for y in list(up.values()) + list(down.values()))
    mass = proof["masses"]
    assert all(x >= 0 for x in mass.values()) and abs(sum(mass.values()) - 100) < ERROR
    assert all(len(bits) == len(items) and set(bits) <= {"0", "1"} for bits in mass)
    marginals = {c: 0.0 for c in codes}
    objective = 0.0
    sign = 1 if proof["endpoint"] == "low" else -1
    for entry in itertools.product("01", repeat=len(items)):
        bits = "".join(entry)
        column = indicators(bits, codes)
        weight = mass.get(bits, 0)
        common = int("1" in bits[:6])
        objective += weight * common
        for c in codes:
            marginals[c] += weight * column[c]
        dual_col = proof["total_dual"] + sum((up[c] - down[c]) * column[c] for c in codes)
        assert dual_col <= sign * common + ERROR
    assert all(abs(marginals[c] - values[size, year, c]) <= 0.005 + ERROR for c in codes)
    dual_value = 100 * proof["total_dual"] + sum(
        (values[size, year, c] + 0.005) * up[c] + (0.005 - values[size, year, c]) * down[c]
        for c in codes
    )
    assert abs(sign * dual_value - objective) < ERROR and abs(objective - proof["value"]) < ERROR
    return objective


def main():
    values = source_values()
    certs = json.loads((ROOT / "results/certificates.json").read_bytes())
    bounds = {}
    for row in certs:
        s, y, m = row["size"], row["year"], row["constraints"]
        assert [p["endpoint"] for p in row["endpoints"]] == ["low", "high"]
        assert (s, y, m) not in bounds
        bounds[s, y, m] = [check_witness(values, y, s, m, p) for p in row["endpoints"]]
    assert set(bounds) == set(itertools.product(SIZES, ["2024", "2025"], MODES))
    intervals = records("intervals.csv")
    assert {(r["size"], r["year"], r["constraints"]) for r in intervals} == set(bounds) and len(
        intervals
    ) == 16
    for r in intervals:
        s, y, m = r["size"], r["year"], r["constraints"]
        for actual, expected in zip([r["common_low_pct"], r["common_high_pct"]], bounds[s, y, m]):
            assert abs(float(actual) - expected) < ERROR
        assert float(r["headline_pct"]) == values[s, y, "TANY"]
    changes = records("changes.csv")
    assert {(r["size"], r["constraints"]) for r in changes} == set(itertools.product(SIZES, MODES))
    assert len(changes) == 8
    for r in changes:
        s, m = r["size"], r["constraints"]
        lo24, hi24 = bounds[s, "2024", m]
        lo25, hi25 = bounds[s, "2025", m]
        assert abs(lo25 - hi24 - float(r["common_low_pp"])) < ERROR
        assert abs(hi25 - lo24 - float(r["common_high_pp"])) < ERROR
        assert math.isclose(
            float(r["headline_change_pp"]), values[s, "2025", "TANY"] - values[s, "2024", "TANY"]
        )
    print(
        "Verified 84 Eurostat cells, 32 optimal endpoint certificates and all 8 change intervals."
    )


if __name__ == "__main__":
    main()
