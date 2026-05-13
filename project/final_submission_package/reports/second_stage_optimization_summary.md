# Second Stage Optimization Summary

## Result

SECOND STAGE OPTIMIZATION RESULT: PASS

## Baseline To Final

| Metric | Baseline | Final | Change |
|---|---:|---:|---:|
| Q1 loaded_count | 126 | 138 | 12 |
| Q1 volume_utilization | 0.791667 | 0.795228 | 0.003561 |
| Q1 weight_utilization | 0.8975 | 0.9275 | 0.030000 |
| Q2 vehicle_count | 4 | 4 | 0 |
| Q2 total_cost | 3003.7795 | 3003.7795 | 0.000000 |
| Q3 flexible_total_cost | 2770.781835 | 2770.781835 | 0.000000 |

## Concrete Algorithms Used

### Q1 Algorithms

1. Extreme/corner-point three-dimensional packing: candidate positions are generated from floor corners, box faces, top faces and grid-refined X/Y points.
2. Bottom-left-back placement scoring: candidates are prioritized by low Z, route/CG target distance, low Y and low X.
3. Legal-orientation enumeration: category I/II keep Z-up; III/IV/V enumerate orthogonal rotations.
4. Class-aware ordering: category priority I -> III -> IV -> V -> II protects battery floor placement and places fragile category II late.
5. Multi-seed perturbation: category-first order was rerun over seeds [0,1,2,3,4,5,6,7,8,9,10,20,42,66,88,100,2026,4096].
6. Lexicographic objective: loaded_count first, then loaded_volume, loaded_weight, CG offset and safety margins. This replaced the older weighted score, so the solver no longer sacrifices item count for volume alone.
7. Pareto archive: top feasible starts are written to `results/q1_best_solutions.csv`; the final incumbent is seed=5 with 138 items.

Improvement source: multi-seed category-first perturbation found a feasible 138-item packing. The previous incumbent had 126 items. Validator remained PASS.

### Q2 Algorithms

1. Candidate route pool: single, double and triple station routes are considered through station subset/route generation.
2. Validation-gated candidate trips: each candidate must pass coordinate, payload, CG and strict LIFO checks before selection.
3. Station batching fallback: oversized station demand is split into feasible batches so no item is omitted.
4. Cross-station merge local search: low-load batches are merged into multi-stop trips only when strict LIFO remains feasible and cost improves.
5. Multi-vehicle replacement: HeavyEV and LightEV are compared during candidate construction and final merges.
6. Dominance/pruning ledger: feasible selected candidates are exported to `results/q2_candidate_trips.csv`; pruning notes and lower-bound gap are reported.

Improvement source retained from first-stage repair: the final plan has a LightEV multi-stop trip Depot->S2->S3->Depot, 4 vehicles, cost 3003.7795, and zero LIFO violations.

### Q3 Algorithms

1. Fair generated-data audit over fixed seeds; seed 2026 is retained with balanced station/class coverage.
2. Strict LIFO baseline: four strict multi-stop clusters, all validator PASS.
3. Block loading strategy: explicit X-route blocks and Y-lane separation, output as `result_q3_loading_block.csv` and `result_q3_trips_block.csv`.
4. Flexible/block LIFO strategy: larger route blocks are allowed while validator converts blocking into relocation statistics; final relocation ratio is 0.
5. Sensitivity grid over eta/mu and Pareto outputs for cost, vehicle count, relocation volume and utilization.

Improvement source: flexible/block strategy uses 3 vehicles versus strict 4, with cost 2770.781835 versus 3575.798550; saving ratio 0.225129.

### Q4 Algorithms

1. Independent validator with pairwise geometry, support, pressure, class, CG, duplicate/missing and LIFO checks.
2. Adversarial tests: 12 hand-built cases cover boundary contact, micro-overlap, V-II contact, fragile top, battery floor, III stack, LIFO positive/negative, flexible relocation, CG, pressure units and duplicate/missing ids.
3. Result traceability table links report claims to source CSV/JSON rows.
4. Paper risk audit checks global-optimality overclaim, return_to_depot, and heuristic limitations.

## Final Incumbents

- Q1: loaded_count=138, volume_utilization=0.795228, weight_utilization=0.9275, Xcg=356.2646.
- Q2: vehicle_count=4, total_cost=3003.7795, total_distance=415.0, LIFO violations=0.
- Q3: strict/block/flexible comparison is in `results/result_q3_comparison.csv`; flexible saving ratio=0.225129, relocation ratio=0.0.
- Q4: validator adversarial tests PASS; audit PASS.

## Remaining Limitations

The search is heuristic and uses relaxed bounds; it cannot prove global optimality. The current results are the best validation-passing incumbents found under the implemented multi-start, local-merge, block-loading and adversarial-verification workflow.
