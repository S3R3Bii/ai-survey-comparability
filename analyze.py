"""Bound the common-item union over all joint distributions consistent with Eurostat."""

import csv
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parent
SOURCE_HASH = "eb0f28c433d3f9ed1dc0639e19bc0acd82979491e09220f8e2400b2fee657371"
COMMON = ("TTM", "TSR", "TIR", "TML", "TPA", "TAR")
TOL = 0.005  # half a reporting unit on the published percentage scale


def read_table():
    raw = (ROOT / "data/eurostat.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_HASH:
        raise ValueError("Unexpected Eurostat snapshot")
    data = json.loads(raw)
    values = {}
    for flat, value in data["value"].items():
        indices = np.unravel_index(int(flat), data["size"])
        key = {}
        for dim, index in zip(data["id"], indices):
            labels = data["dimension"][dim]["category"]["index"]
            (key[dim],) = (code for code, pos in labels.items() if pos == index)
        assert (key["geo"], key["unit"], key["freq"], key["nace_r2"]) == (
            "EU27_2020",
            "PC_ENT",
            "A",
            "C10-S951_X_K",
        )
        assert not data.get("status", {}).get(flat)
        cell = (key["size_emp"], key["time"], key["indic_is"].removeprefix("E_AI_"))
        assert cell not in values and 0 <= value <= 100
        values[cell] = value
    return values


def solve(values, year, size, include_counts):
    items = COMMON + ("TNLG",) + (("TPVSG",) if year == "2025" else ())
    patterns = np.array(list(itertools.product((0, 1), repeat=len(items))))
    # All quantities are percentage points of eligible enterprises.
    totals = patterns.sum(axis=1)
    codes = list(items) + ["TANY"]
    rows = [*patterns.T, totals >= 1]
    if include_counts:
        codes.extend(["TGE2", "TGE3"])
        rows.extend([totals >= 2, totals >= 3])
    observed = np.array([values[size, year, code] for code in codes])
    matrix = np.array(rows, dtype=float)
    inequalities = np.vstack([matrix, -matrix])
    bounds = np.r_[observed + TOL, -observed + TOL]
    common = patterns[:, : len(COMMON)].any(axis=1).astype(float)
    evidence = []
    for label, sign in (("low", 1), ("high", -1)):
        fit = linprog(
            sign * common,
            A_ub=inequalities,
            b_ub=bounds,
            A_eq=[np.ones(len(common))],
            b_eq=[100],
            method="highs",
        )
        if not fit.success:
            raise ValueError(f"{size} {year} {label}: {fit.message}")
        evidence.append(
            dict(
                endpoint=label,
                value=round(sign * fit.fun, 8),
                masses={
                    "".join(map(str, p)): round(float(x), 9)
                    for p, x in zip(patterns, fit.x)
                    if x > 1e-9
                },
                upper_dual=dict(zip(codes, np.round(fit.ineqlin.marginals[: len(codes)], 9))),
                lower_dual=dict(zip(codes, np.round(fit.ineqlin.marginals[len(codes) :], 9))),
                total_dual=round(float(fit.eqlin.marginals[0]), 9),
            )
        )
    return evidence


def write_csv(path, records):
    with path.open("w", newline="", encoding="utf-8") as dest:
        writer = csv.DictWriter(dest, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main():
    values = read_table()
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    cells = [
        dict(size=size, year=year, indicator=code, pct=value)
        for (size, year, code), value in sorted(values.items())
    ]
    write_csv(out / "source_cells.csv", cells)
    intervals, changes, certificates = [], [], []
    for size in ("GE10", "10-49", "50-249", "GE250"):
        for mode in ("all_published_counts", "without_multi_use_counts"):
            years = {}
            for year in ("2024", "2025"):
                proof = solve(values, year, size, mode == "all_published_counts")
                lo, hi = [p["value"] for p in proof]
                years[year] = (lo, hi)
                intervals.append(
                    dict(
                        size=size,
                        constraints=mode,
                        year=year,
                        common_low_pct=lo,
                        common_high_pct=hi,
                        headline_pct=values[size, year, "TANY"],
                    )
                )
                certificates.append(dict(size=size, year=year, constraints=mode, endpoints=proof))
            low = round(years["2025"][0] - years["2024"][1], 8)
            high = round(years["2025"][1] - years["2024"][0], 8)
            changes.append(
                dict(
                    size=size,
                    constraints=mode,
                    common_low_pp=low,
                    common_high_pp=high,
                    headline_change_pp=round(
                        values[size, "2025", "TANY"] - values[size, "2024", "TANY"], 4
                    ),
                )
            )
    write_csv(out / "intervals.csv", intervals)
    write_csv(out / "changes.csv", changes)
    (out / "certificates.json").write_bytes((json.dumps(certificates, indent=2) + "\n").encode())


if __name__ == "__main__":
    main()
