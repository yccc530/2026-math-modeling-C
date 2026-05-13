"""Geometry helpers for orthogonal 3D packing."""

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

from typing import Iterable, Tuple

EPS = 1e-7


def interval_overlap(a0: float, a1: float, b0: float, b1: float, *, closed: bool = False) -> bool:
    if closed:
        return min(a1, b1) >= max(a0, b0) - EPS
    return min(a1, b1) > max(a0, b0) + EPS


def overlap_length(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def box_bounds(item) -> Tuple[float, float, float, float, float, float]:
    return item.x, item.x + item.length, item.y, item.y + item.width, item.z, item.z + item.height


def boxes_overlap(a, b) -> bool:
    ax0, ax1, ay0, ay1, az0, az1 = box_bounds(a)
    bx0, bx1, by0, by1, bz0, bz1 = box_bounds(b)
    return (
        interval_overlap(ax0, ax1, bx0, bx1)
        and interval_overlap(ay0, ay1, by0, by1)
        and interval_overlap(az0, az1, bz0, bz1)
    )


def boxes_closed_intersect(a, b) -> bool:
    ax0, ax1, ay0, ay1, az0, az1 = box_bounds(a)
    bx0, bx1, by0, by1, bz0, bz1 = box_bounds(b)
    return (
        interval_overlap(ax0, ax1, bx0, bx1, closed=True)
        and interval_overlap(ay0, ay1, by0, by1, closed=True)
        and interval_overlap(az0, az1, bz0, bz1, closed=True)
    )


def volume_cm3(length: float, width: float, height: float) -> float:
    return length * width * height


def volume_m3_from_cm3(v: float) -> float:
    return v / 1_000_000.0


def item_volume_m3(item) -> float:
    return volume_m3_from_cm3(item.length * item.width * item.height)


def xy_overlap_area_cm2(a, b) -> float:
    ax0, ax1, ay0, ay1, _, _ = box_bounds(a)
    bx0, bx1, by0, by1, _, _ = box_bounds(b)
    return overlap_length(ax0, ax1, bx0, bx1) * overlap_length(ay0, ay1, by0, by1)


def xy_overlap_area_m2(a, b) -> float:
    return xy_overlap_area_cm2(a, b) / 10_000.0


def center_x(item) -> float:
    return item.x + item.length / 2.0


def center_y(item) -> float:
    return item.y + item.width / 2.0


def center_z(item) -> float:
    return item.z + item.height / 2.0


def weighted_x_cg(items: Iterable) -> float:
    items = list(items)
    weight = sum(i.weight for i in items)
    if weight <= EPS:
        return 0.0
    return sum(i.weight * center_x(i) for i in items) / weight


def total_weight(items: Iterable) -> float:
    return sum(i.weight for i in items)


def total_volume_cm3(items: Iterable) -> float:
    return sum(i.length * i.width * i.height for i in items)


def lifo_blocks(later_item, earlier_item) -> bool:
    """Return True when later_item blocks earlier_item from sliding to +X."""

    return (
        later_item.x + later_item.length > earlier_item.x + EPS
        and interval_overlap(later_item.y, later_item.y + later_item.width, earlier_item.y, earlier_item.y + earlier_item.width)
        and interval_overlap(later_item.z, later_item.z + later_item.height, earlier_item.z, earlier_item.z + earlier_item.height)
    )


def support_area_cm2(item, placed_items) -> float:
    if item.z <= EPS:
        return item.length * item.width
    area = 0.0
    for other in placed_items:
        if other is item:
            continue
        if abs(other.z + other.height - item.z) <= 1e-5:
            area += xy_overlap_area_cm2(item, other)
    return area

