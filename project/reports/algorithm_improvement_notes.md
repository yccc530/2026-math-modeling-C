# Algorithms Used and What Improved

| Problem | First-stage algorithm | Second-stage upgrade | Why it can improve | Observed effect |
|---|---|---|---|---|
| Q1 | Weighted score multi-start EP packing | Lexicographic objective, top-20 feasible archive, Pareto/frontier analysis | Prevents high-volume but low-count solutions from beating the stated primary goal | Q1 now selects by loaded count first, then volume/weight/CG |
| Q2 | Feasibility-first split and merge | Candidate trip ledger, validation-gated cross-station merge, lower-bound report, utilization plots | Keeps only strict-LIFO feasible trips and accepts merges only when cost improves | Final plan has multi-model fleet and a multi-stop LightEV trip |
| Q3 | Strict vs flexible two-point comparison | Strict/block/flexible three-strategy comparison, sensitivity grid, Pareto outputs, dataset audit | Separates physical block loading from flexible LIFO and records fairness checks | Flexible uses 3 vehicles vs strict 4 on submitted dataset |
| Q4 | Validator on final CSVs | Adversarial unit tests, traceability table, paper-risk audit | Tests the checker itself and links claims to source files | 12 adversarial tests pass |
