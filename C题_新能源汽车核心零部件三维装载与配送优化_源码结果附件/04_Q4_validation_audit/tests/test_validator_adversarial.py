# -*- coding: utf-8 -*-
"""Adversarial tests for validator.py.

Run from project root:
    python tests/test_validator_adversarial.py
"""

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

from pathlib import Path
from types import SimpleNamespace
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from validator import validate_items


def item(
    item_id,
    category="IV",
    x=0,
    y=0,
    z=0,
    l=10,
    w=10,
    h=10,
    weight=10,
    dest="",
    route=None,
    code="T",
):
    return SimpleNamespace(
        scenario="test",
        mode="strict",
        trip_id="T1",
        vehicle_id="T1",
        truck_type="HeavyEV",
        route=route or [],
        destination=dest,
        item_id=item_id,
        cargo_code=code,
        category=category,
        x=float(x),
        y=float(y),
        z=float(z),
        length=float(l),
        width=float(w),
        height=float(h),
        weight=float(weight),
        original_length=float(l),
        original_width=float(w),
        original_height=float(h),
        orientation="test",
    )


def has(report, violation_type):
    return any(v["violation_type"] == violation_type for v in report["violations"])


def run_tests():
    tests = []

    r = validate_items([item("A"), item("B", x=10)], mode="strict")
    tests.append(("边界接触不判定为空间重叠", not has(r, "overlap")))

    r = validate_items([item("A"), item("B", x=9.999)], mode="strict")
    tests.append(("微小正重叠能够被检测", has(r, "overlap")))

    r = validate_items([item("V", "V"), item("II", "II", x=10, y=10)], mode="strict")
    tests.append(("类别 V 与类别 II 的点、线、面接触被判定为违规", has(r, "category_V_II_contact")))

    r = validate_items([item("II", "II", l=20, w=20, h=10), item("U", "IV", z=10, l=20, w=20, h=10)], mode="strict")
    tests.append(("类别 II 上方存在货物时被判定为违规", has(r, "category_II_top")))

    r = validate_items([item("I", "I", z=1, l=120, w=80, h=40, weight=350)], mode="strict")
    tests.append(("类别 I 货物 z>0 被判定为违规", has(r, "category_I")))

    r = validate_items(
        [
            item("M1", "III", l=80, w=60, h=60, weight=50),
            item("M2", "III", z=60, l=80, w=60, h=60, weight=50),
            item("M3", "III", z=120, l=80, w=60, h=60, weight=50),
        ],
        mode="strict",
    )
    tests.append(("类别 III 三层连续堆叠能够被检测", has(r, "category_III_stack")))

    r = validate_items(
        [
            item("EARLY", "IV", x=260, y=0, z=0, l=80, w=80, h=40, dest="S1", route=["S1", "S2"]),
            item("LATE", "IV", x=360, y=0, z=0, l=80, w=80, h=40, dest="S2", route=["S1", "S2"]),
        ],
        mode="strict",
    )
    tests.append(("严格 LIFO 阻挡能够被检测", has(r, "lifo_block")))

    r = validate_items(
        [
            item("EARLY", "IV", x=260, y=0, z=0, l=80, w=80, h=40, dest="S1", route=["S1", "S2"]),
            item("LATE", "IV", x=360, y=100, z=0, l=80, w=80, h=40, dest="S2", route=["S1", "S2"]),
        ],
        mode="strict",
    )
    tests.append(("LIFO 在 Y 方向错开的反例能够通过", not has(r, "lifo_block")))

    r = validate_items(
        [
            item("EARLY", "IV", x=260, y=0, z=0, l=80, w=80, h=40, dest="S1", route=["S1", "S2"]),
            item("LATE", "IV", x=360, y=0, z=0, l=80, w=80, h=40, dest="S2", route=["S1", "S2"]),
        ],
        mode="flexible",
        relocation_volume_limit=1.0,
    )
    tests.append(("柔性 LIFO 能够将阻挡转化为倒箱统计", r["relocation_count"] == 1 and r["hard_violation_count"] == 0))

    r = validate_items([item("CG", "IV", x=200, l=80, w=80, h=40, weight=100)], mode="strict")
    tests.append(("重心位于边界时被接受", not has(r, "center_of_gravity")))

    r = validate_items([item("LOW", "IV", l=100, w=100, h=10, weight=10), item("UP", "IV", z=10, l=100, w=100, h=10, weight=401)], mode="strict")
    tests.append(("kg/m2 承重单位换算违规能够被检测", has(r, "bearing")))

    r = validate_items([item("DUP"), item("DUP", x=20)], mode="strict", expected_item_ids=["DUP", "MISS"])
    tests.append(("重复和遗漏货物编号能够被检测", has(r, "duplicate_item") and has(r, "missing_item")))

    failed = [name for name, ok in tests if not ok]
    report = ROOT / "reports" / "validator_adversarial_report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# 验证器对抗测试报告\n\n"]
    for name, ok in tests:
        lines.append(f"- {'通过' if ok else '未通过'}：{name}。\n")
    report.write_text("".join(lines), encoding="utf-8-sig")
    if failed:
        raise SystemExit("对抗测试未通过：" + "，".join(failed))
    print(f"通过：{len(tests)} 个验证器对抗测试")


if __name__ == "__main__":
    run_tests()
