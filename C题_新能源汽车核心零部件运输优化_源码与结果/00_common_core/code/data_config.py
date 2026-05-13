# -*- coding: utf-8 -*-
"""Static data and shared data structures for Problem C.

The project intentionally keeps the data layer dependency free.  All
dimensions are stored in cm, weights in kg, and distances in km.
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

from dataclasses import dataclass, field
from itertools import permutations
from pathlib import Path
import csv
import math
import random
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


_THIS_FILE = Path(__file__).resolve()
ROOT = next((p for p in _THIS_FILE.parents if (p / "00_common_core").is_dir()), _THIS_FILE.parent)
RESULTS_DIR = ROOT / "results"
PLOTS_DIR = ROOT / "plots"
REPORTS_DIR = ROOT / "reports"

SEEDS = [0, 1, 2, 3, 4, 5, 10, 20, 42, 100, 2026]


@dataclass(frozen=True)
class CargoType:
    code: str
    category: str
    length: float
    width: float
    height: float
    weight: float
    quantity: int
    destination: Optional[str] = None

    @property
    def volume_cm3(self) -> float:
        return self.length * self.width * self.height


@dataclass(frozen=True)
class CargoItem:
    item_id: str
    cargo_code: str
    category: str
    length: float
    width: float
    height: float
    weight: float
    destination: Optional[str] = None

    @property
    def volume_cm3(self) -> float:
        return self.length * self.width * self.height


@dataclass(frozen=True)
class TruckType:
    name: str
    length: float
    width: float
    height: float
    max_payload: float
    empty_weight: float
    fixed_cost: float
    dynamic_coeff: float

    @property
    def volume_cm3(self) -> float:
        return self.length * self.width * self.height


@dataclass
class PlacedItem:
    item: CargoItem
    truck_type: str
    vehicle_id: str
    trip_id: str
    route: List[str]
    x: float
    y: float
    z: float
    length: float
    width: float
    height: float
    orientation: str = ""

    @property
    def destination(self) -> Optional[str]:
        return self.item.destination

    @property
    def item_id(self) -> str:
        return self.item.item_id

    @property
    def cargo_code(self) -> str:
        return self.item.cargo_code

    @property
    def category(self) -> str:
        return self.item.category

    @property
    def weight(self) -> float:
        return self.item.weight

    @property
    def volume_cm3(self) -> float:
        return self.length * self.width * self.height

    @property
    def original_length(self) -> float:
        return self.item.length

    @property
    def original_width(self) -> float:
        return self.item.width

    @property
    def original_height(self) -> float:
        return self.item.height

    @property
    def x_max(self) -> float:
        return self.x + self.length

    @property
    def y_max(self) -> float:
        return self.y + self.width

    @property
    def z_max(self) -> float:
        return self.z + self.height


@dataclass(frozen=True)
class Route:
    stops: Tuple[str, ...]
    return_to_depot: bool = True

    def label(self) -> str:
        tail = ["Depot"] if self.return_to_depot else []
        return "->".join(["Depot", *self.stops, *tail])


@dataclass
class VehiclePlan:
    trip_id: str
    vehicle_id: str
    truck_type: TruckType
    route: Route
    placed_items: List[PlacedItem]
    cost: float
    route_distance: float
    mode: str = "strict"
    relocation_count: int = 0
    relocation_volume_m3: float = 0.0
    extra: Dict[str, float] = field(default_factory=dict)

    @property
    def load_weight(self) -> float:
        return sum(p.weight for p in self.placed_items)

    @property
    def load_volume_cm3(self) -> float:
        return sum(p.volume_cm3 for p in self.placed_items)

    @property
    def volume_utilization(self) -> float:
        return self.load_volume_cm3 / self.truck_type.volume_cm3 if self.truck_type.volume_cm3 else 0.0

    @property
    def weight_utilization(self) -> float:
        return self.load_weight / self.truck_type.max_payload if self.truck_type.max_payload else 0.0


TRUCK_TYPES: Dict[str, TruckType] = {
    "HeavyEV": TruckType(
        name="HeavyEV",
        length=720,
        width=240,
        height=260,
        max_payload=12000,
        empty_weight=8000,
        fixed_cost=800,
        dynamic_coeff=0.05,
    ),
    "LightEV": TruckType(
        name="LightEV",
        length=420,
        width=200,
        height=200,
        max_payload=4500,
        empty_weight=3500,
        fixed_cost=400,
        dynamic_coeff=0.04,
    ),
}


SCENARIO_A_TYPES: List[CargoType] = [
    CargoType("G1", "I", 120, 80, 40, 350, 12),
    CargoType("G2", "II", 60, 50, 40, 25, 40),
    CargoType("G3", "III", 80, 60, 60, 120, 30),
    CargoType("G4", "IV", 100, 80, 60, 30, 80),
    CargoType("G5", "V", 40, 40, 50, 40, 50),
]


SCENARIO_B_TYPES: List[CargoType] = [
    CargoType("B1", "I", 120, 80, 40, 350, 8, "S1"),
    CargoType("B2", "I", 120, 80, 40, 350, 10, "S3"),
    CargoType("B3", "II", 60, 50, 40, 25, 30, "S2"),
    CargoType("B4", "III", 80, 60, 60, 120, 20, "S1"),
    CargoType("B5", "III", 80, 60, 60, 120, 25, "S3"),
    CargoType("B6", "IV", 100, 80, 60, 30, 60, "S2"),
    CargoType("B7", "IV", 100, 80, 60, 30, 50, "S3"),
]


BASE_DISTANCE_MATRIX: Dict[Tuple[str, str], float] = {
    ("Depot", "S1"): 30,
    ("Depot", "S2"): 45,
    ("Depot", "S3"): 60,
    ("S1", "S2"): 20,
    ("S2", "S3"): 40,
    ("S1", "S3"): 50,
}


def ensure_directories() -> None:
    for folder in (RESULTS_DIR, PLOTS_DIR, REPORTS_DIR):
        folder.mkdir(parents=True, exist_ok=True)


def symmetric_distance_matrix(base: Dict[Tuple[str, str], float]) -> Dict[Tuple[str, str], float]:
    out: Dict[Tuple[str, str], float] = {}
    nodes = set()
    for (a, b), d in base.items():
        out[(a, b)] = float(d)
        out[(b, a)] = float(d)
        nodes.add(a)
        nodes.add(b)
    for n in nodes:
        out[(n, n)] = 0.0
    return out


DISTANCE_MATRIX = symmetric_distance_matrix(BASE_DISTANCE_MATRIX)


def expand_cargo_types(types: Sequence[CargoType], prefix: str = "") -> List[CargoItem]:
    items: List[CargoItem] = []
    for cargo in types:
        for idx in range(1, cargo.quantity + 1):
            item_id = f"{prefix}{cargo.code}_{idx:03d}"
            items.append(
                CargoItem(
                    item_id=item_id,
                    cargo_code=cargo.code,
                    category=cargo.category,
                    length=cargo.length,
                    width=cargo.width,
                    height=cargo.height,
                    weight=cargo.weight,
                    destination=cargo.destination,
                )
            )
    return items


def expand_scenario_a_items() -> List[CargoItem]:
    return expand_cargo_types(SCENARIO_A_TYPES)


def expand_scenario_b_items() -> List[CargoItem]:
    return expand_cargo_types(SCENARIO_B_TYPES)


def cargo_type_lookup() -> Dict[str, CargoType]:
    lookup: Dict[str, CargoType] = {}
    for cargo in [*SCENARIO_A_TYPES, *SCENARIO_B_TYPES]:
        lookup[cargo.code] = cargo
    q3_path = RESULTS_DIR / "generated_cargo_q3.csv"
    if q3_path.exists():
        for cargo in load_q3_cargo_types(q3_path):
            lookup[cargo.code] = cargo
    return lookup


def legal_orientations(item: CargoItem) -> List[Tuple[float, float, float, str]]:
    l, w, h = item.length, item.width, item.height
    if item.category == "I":
        return [(l, w, h, "fixed")]
    if item.category == "II":
        orientations = [(l, w, h, "xy0")]
        if abs(l - w) > 1e-9:
            orientations.append((w, l, h, "xy90"))
        return orientations
    dims = (l, w, h)
    seen = set()
    out: List[Tuple[float, float, float, str]] = []
    for perm in permutations(dims, 3):
        if perm in seen:
            continue
        seen.add(perm)
        out.append((perm[0], perm[1], perm[2], f"perm{len(out)}"))
    return out


def generate_q3_cargo_types(seed: int = 2026) -> List[CargoType]:
    """Generate a moderate, repeatable 8-station/20-SKU data set.

    The generator keeps all physical fields in the scenario-A min/max range and
    deliberately caps category-I quantities so station loads remain packable.
    """

    rng = random.Random(seed)
    categories = ["I", "II", "III", "IV", "V"]
    destinations = [f"S{i}" for i in range(1, 9)]
    types: List[CargoType] = []

    for i in range(20):
        category = categories[i % len(categories)]
        dest = destinations[i % len(destinations)]
        if category == "I":
            length = rng.choice([90, 100, 110, 120])
            width = rng.choice([60, 70, 80])
            height = rng.choice([40, 45])
            weight = rng.choice([220, 260, 300, 330])
            qty = rng.randint(1, 3)
        elif category == "II":
            length = rng.choice([50, 60, 70])
            width = rng.choice([40, 50, 60])
            height = rng.choice([40, 45])
            weight = rng.choice([25, 35, 45, 55])
            qty = rng.randint(3, 7)
        elif category == "III":
            length = rng.choice([60, 70, 80, 90])
            width = rng.choice([50, 60, 70])
            height = rng.choice([50, 60])
            weight = rng.choice([90, 110, 130, 160])
            qty = rng.randint(3, 6)
        elif category == "IV":
            length = rng.choice([80, 90, 100, 110, 120])
            width = rng.choice([60, 70, 80])
            height = rng.choice([40, 50, 60])
            weight = rng.choice([25, 30, 40, 50])
            qty = rng.randint(6, 11)
        else:
            length = rng.choice([40, 50, 60])
            width = rng.choice([40, 50])
            height = rng.choice([40, 50, 60])
            weight = rng.choice([35, 45, 60, 80])
            qty = rng.randint(2, 5)
        types.append(CargoType(f"Q3_{i+1:02d}", category, length, width, height, weight, qty, dest))

    # Add a second destination pass for variety while keeping every station nonempty.
    for idx, cargo in enumerate(types):
        if idx >= 8 and rng.random() < 0.45:
            types[idx] = CargoType(
                cargo.code,
                cargo.category,
                cargo.length,
                cargo.width,
                cargo.height,
                cargo.weight,
                cargo.quantity,
                rng.choice(destinations),
            )
    return types


def expand_q3_items(types: Sequence[CargoType]) -> List[CargoItem]:
    return expand_cargo_types(types)


def generate_q3_distance_matrix(seed: int = 2026) -> Dict[Tuple[str, str], float]:
    """Generate an S1-S8 metric matrix while preserving the six fixed distances."""

    rng = random.Random(seed)
    nodes = ["Depot", *[f"S{i}" for i in range(1, 9)]]
    coords = {
        "Depot": (0.0, 0.0),
        "S1": (30.0, 0.0),
        "S2": (42.5, 15.6),
        "S3": (55.0, -24.0),
    }
    # These coordinates roughly agree with the fixed distances; the fixed
    # matrix below remains authoritative for S1-S3 edges.
    for i in range(4, 9):
        radius = rng.uniform(35, 135)
        angle = rng.uniform(-math.pi * 0.85, math.pi * 0.85)
        coords[f"S{i}"] = (radius * math.cos(angle), radius * math.sin(angle))

    matrix: Dict[Tuple[str, str], float] = {}
    for a in nodes:
        for b in nodes:
            if a == b:
                matrix[(a, b)] = 0.0
            else:
                ax, ay = coords[a]
                bx, by = coords[b]
                matrix[(a, b)] = round(math.hypot(ax - bx, ay - by), 2)

    fixed = symmetric_distance_matrix(BASE_DISTANCE_MATRIX)
    for edge, dist in fixed.items():
        matrix[edge] = float(dist)

    # Metric closure on edges involving new stations only.  Fixed edges among
    # Depot/S1/S2/S3 are restored after each Floyd-Warshall pass.
    for _ in range(2):
        for k in nodes:
            for i in nodes:
                for j in nodes:
                    if (i, j) in fixed:
                        continue
                    alt = matrix[(i, k)] + matrix[(k, j)]
                    if alt + 1e-9 < matrix[(i, j)]:
                        matrix[(i, j)] = round(alt, 2)
        for edge, dist in fixed.items():
            matrix[edge] = float(dist)

    for s in nodes:
        if s == "Depot":
            continue
        d = matrix[("Depot", s)]
        if d < 15 or d > 150:
            # Pull new stations into range without touching fixed S1-S3.
            if s not in {"S1", "S2", "S3"}:
                clamped = min(150.0, max(15.0, d))
                matrix[("Depot", s)] = clamped
                matrix[(s, "Depot")] = clamped
    return matrix


def write_cargo_types_csv(types: Sequence[CargoType], path: Path) -> None:
    ensure_directories()
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "cargo_code",
                "category",
                "length",
                "width",
                "height",
                "weight",
                "quantity",
                "destination",
            ],
        )
        writer.writeheader()
        for c in types:
            writer.writerow(
                {
                    "cargo_code": c.code,
                    "category": c.category,
                    "length": c.length,
                    "width": c.width,
                    "height": c.height,
                    "weight": c.weight,
                    "quantity": c.quantity,
                    "destination": c.destination or "",
                }
            )


def load_q3_cargo_types(path: Path) -> List[CargoType]:
    if not path.exists():
        return []
    out: List[CargoType] = []
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            out.append(
                CargoType(
                    row["cargo_code"],
                    row["category"],
                    float(row["length"]),
                    float(row["width"]),
                    float(row["height"]),
                    float(row["weight"]),
                    int(float(row["quantity"])),
                    row.get("destination") or None,
                )
            )
    return out


def write_distance_matrix_csv(matrix: Dict[Tuple[str, str], float], path: Path) -> None:
    nodes = sorted({a for a, _ in matrix.keys()}, key=lambda x: (x != "Depot", x))
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["from_to", *nodes])
        for a in nodes:
            writer.writerow([a, *[matrix[(a, b)] for b in nodes]])


def read_distance_matrix_csv(path: Path) -> Dict[Tuple[str, str], float]:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    nodes = rows[0][1:]
    matrix: Dict[Tuple[str, str], float] = {}
    for row in rows[1:]:
        a = row[0]
        for b, value in zip(nodes, row[1:]):
            matrix[(a, b)] = float(value)
    return matrix


LOADING_FIELDS = [
    "scenario",
    "mode",
    "trip_id",
    "vehicle_id",
    "truck_type",
    "route",
    "destination",
    "item_id",
    "cargo_code",
    "category",
    "x",
    "y",
    "z",
    "length",
    "width",
    "height",
    "weight",
    "original_length",
    "original_width",
    "original_height",
    "orientation",
]


def placed_item_to_row(p: PlacedItem, scenario: str, mode: str) -> Dict[str, object]:
    return {
        "scenario": scenario,
        "mode": mode,
        "trip_id": p.trip_id,
        "vehicle_id": p.vehicle_id,
        "truck_type": p.truck_type,
        "route": "->".join(p.route),
        "destination": p.item.destination or "",
        "item_id": p.item.item_id,
        "cargo_code": p.item.cargo_code,
        "category": p.item.category,
        "x": round(p.x, 6),
        "y": round(p.y, 6),
        "z": round(p.z, 6),
        "length": round(p.length, 6),
        "width": round(p.width, 6),
        "height": round(p.height, 6),
        "weight": round(p.item.weight, 6),
        "original_length": p.item.length,
        "original_width": p.item.width,
        "original_height": p.item.height,
        "orientation": p.orientation,
    }


def write_loading_csv(placed: Sequence[PlacedItem], path: Path, scenario: str, mode: str) -> None:
    ensure_directories()
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=LOADING_FIELDS)
        writer.writeheader()
        for p in placed:
            writer.writerow(placed_item_to_row(p, scenario, mode))


def items_by_destination(items: Iterable[CargoItem]) -> Dict[str, List[CargoItem]]:
    grouped: Dict[str, List[CargoItem]] = {}
    for item in items:
        grouped.setdefault(item.destination or "", []).append(item)
    return grouped
