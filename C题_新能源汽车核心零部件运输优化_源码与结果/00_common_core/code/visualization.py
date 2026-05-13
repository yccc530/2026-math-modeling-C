# -*- coding: utf-8 -*-
"""Plot helpers for packing and comparison results."""

from __future__ import annotations
try:
    from bootstrap_paths import configure_paths as _configure_organized_paths
except ModuleNotFoundError:
    import sys as _organized_sys
    from pathlib import Path as _OrganizedPath
    _organized_root = next((p for p in _OrganizedPath(__file__).resolve().parents if (p / "00_common_core").is_dir()), None)
    if _organized_root is not None:
        _organized_sys.path.insert(0, str(_organized_root))
    from bootstrap_paths import configure_paths as _configure_organized_paths
_configure_organized_paths(__file__)

import csv
from pathlib import Path
from typing import Dict, List

from data_config import PLOTS_DIR, TRUCK_TYPES, ensure_directories


def _try_import_matplotlib():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection

        return plt, Poly3DCollection
    except Exception:
        return None, None


def _cuboid_faces(x, y, z, l, w, h):
    p = [
        (x, y, z),
        (x + l, y, z),
        (x + l, y + w, z),
        (x, y + w, z),
        (x, y, z + h),
        (x + l, y, z + h),
        (x + l, y + w, z + h),
        (x, y + w, z + h),
    ]
    return [
        [p[i] for i in [0, 1, 2, 3]],
        [p[i] for i in [4, 5, 6, 7]],
        [p[i] for i in [0, 1, 5, 4]],
        [p[i] for i in [2, 3, 7, 6]],
        [p[i] for i in [1, 2, 6, 5]],
        [p[i] for i in [0, 3, 7, 4]],
    ]


def plot_loading(csv_path: Path, output_path: Path, title: str = "3D loading", max_vehicles: int = 3) -> None:
    ensure_directories()
    plt, Poly3DCollection = _try_import_matplotlib()
    if plt is None:
        output_path.with_suffix(".txt").write_text("matplotlib unavailable; plot skipped\n", encoding="utf-8")
        return
    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        output_path.with_suffix(".txt").write_text("no rows to plot\n", encoding="utf-8")
        return
    vehicles = []
    seen = set()
    for r in rows:
        tid = r["trip_id"]
        if tid not in seen:
            seen.add(tid)
            vehicles.append(tid)
        if len(vehicles) >= max_vehicles:
            break
    fig = plt.figure(figsize=(6 * len(vehicles), 5))
    colors = {"I": "#d95f02", "II": "#1b9e77", "III": "#7570b3", "IV": "#66a61e", "V": "#e7298a"}
    for idx, trip_id in enumerate(vehicles, start=1):
        ax = fig.add_subplot(1, len(vehicles), idx, projection="3d")
        sub = [r for r in rows if r["trip_id"] == trip_id]
        truck = TRUCK_TYPES[sub[0]["truck_type"]]
        for r in sub:
            x, y, z = float(r["x"]), float(r["y"]), float(r["z"])
            l, w, h = float(r["length"]), float(r["width"]), float(r["height"])
            faces = _cuboid_faces(x, y, z, l, w, h)
            poly = Poly3DCollection(faces, alpha=0.45, linewidths=0.25, edgecolor="black")
            poly.set_facecolor(colors.get(r["category"], "#999999"))
            ax.add_collection3d(poly)
        ax.set_xlim(0, truck.length)
        ax.set_ylim(0, truck.width)
        ax.set_zlim(0, truck.height)
        ax.set_xlabel("X cm")
        ax.set_ylabel("Y cm")
        ax.set_zlabel("Z cm")
        ax.set_title(f"{title}\n{trip_id}")
        ax.view_init(elev=22, azim=-58)
    plt.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_q3_comparison(comparison_csv: Path, output_path: Path) -> None:
    ensure_directories()
    plt, _ = _try_import_matplotlib()
    if plt is None:
        return
    with comparison_csv.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    labels = [r["strategy"] for r in rows]
    costs = [float(r["total_cost"]) for r in rows]
    vehicles = [float(r["vehicle_count"]) for r in rows]
    fig, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(labels, costs, color=["#4c78a8", "#f58518"], alpha=0.8)
    ax1.set_ylabel("Total cost")
    ax2 = ax1.twinx()
    ax2.plot(labels, vehicles, color="#54a24b", marker="o")
    ax2.set_ylabel("Vehicle count")
    ax1.set_title("Q3 strategy comparison")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)


def plot_q3_sensitivity(sensitivity_csv: Path, output_path: Path) -> None:
    ensure_directories()
    plt, _ = _try_import_matplotlib()
    if plt is None:
        return
    with sensitivity_csv.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    xs = list(range(len(rows)))
    costs = [float(r["total_cost"]) for r in rows]
    labels = [f"{r['eta']}/{r['mu']}" for r in rows]
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(xs, costs, marker="o", color="#e45756")
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("Flexible total cost")
    ax.set_xlabel("eta / mu")
    ax.set_title("Q3 relocation penalty sensitivity")
    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    plt.close(fig)

