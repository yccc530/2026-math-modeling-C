# Optimization Dashboard

|iter|module|strategy|Q1 count|Q2 cost|Q3 flex cost|audit|best|notes|
|---:|---|---|---:|---:|---:|---|---|---|
|0|baseline|first-stage incumbent|126|3003.7795|2770.781835|True|True|baseline before second-stage artifacts|
|1|q1/q2/q3/q4|lexicographic Q1 + candidate Q2 + strict/block/flexible Q3 + adversarial Q4|126|3003.7795|2770.781835|True|True|second-stage enhanced incumbent|
|2|q1_solver.py|category full-seed lexicographic incumbent; seed=5 accepted|138|3003.7795|2770.781835|True|True|Q1 improved 126->138 after full category seed search|
