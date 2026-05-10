# LDBC SNB SF0.1 — SchemaLens / MongoDB Benchmark Reproduction

This repository contains the reproducibility package for applying the SchemaLens methodology to the LDBC SNB dataset and benchmarking MongoDB candidate document configurations.

The goal is not to recommend one MongoDB schema directly. The goal is to reduce the MongoDB design space in an explainable way, using the conceptual schema and workload to activate a small family of candidate configurations, then benchmark those candidates.

---

## 1. What was implemented

This implementation applies the same methodology previously validated on IMDb and FIBEN to LDBC SNB.

The pipeline computes:

- selected root entity;
- conceptual relationship count `Rc`;
- required depth `D`;
- residual explicit traversal `Re`;
- `DeltaR`;
- `DeltaRratio`;
- semantic relationship profile;
- observed update volatility;
- observed sharedness;
- G0-G9 activation;
- MongoDB candidate configurations;
- primary, secondary affected, and control benchmark groups.

The benchmark output follows the same file format used in the FIBEN runner:

```text
execution.log
scale_db_initialization_summary.csv
candidate_load_summary.csv
benchmark_raw_results.csv
benchmark_aggregate_results.csv
benchmark_run_manifest.json
```

---

## 2. Dataset used

Dataset: LDBC SNB Interactive v1  
Scale factor used in this experiment: SF0.1  
Serializer used: `CsvMergeForeign-StringDateFormatter`

Expected local data layout:

```text
data/sf0.1/
├── social_network-sf0.1-CsvMergeForeign-StringDateFormatter/
│   ├── dynamic/
│   ├── static/
│   ├── updateStream_0_0_forum.csv
│   ├── updateStream_0_0_person.csv
│   └── updateStream.properties
├── social_network-sf0.1-numpart-1/
│   ├── updateStream_0_0_forum.csv
│   ├── updateStream_0_0_person.csv
│   └── updateStream.properties
└── substitution_parameters-sf0.1/
```

The raw CSV files are **not included** in this repository because they may be large. Download them from the official LDBC dataset repository using the same serializer and scale factor.

---

## 3. Recommended repository structure

```text
.
├── README.md
├── requirements.txt
├── docker-compose.yml
├── notebooks/
│   └── ldbc_snb_schema_lens_methodology.ipynb
├── scripts/
│   ├── run_ldbc_snb_mongo_benchmark.py
│   └── validate_ldbc_snb_results.py
├── benchmark_artifacts_dir/
│   ├── ldbc_snb_mongo_configurations/
│   │   ├── mongodb_candidate_specs_by_candidate_id.json
│   │   ├── mongodb_candidate_specs_overview.csv
│   │   ├── benchmark_execution_plan.csv
│   │   ├── benchmark_execution_plan_smoke.csv
│   │   ├── benchmark_manifest.json
│   │   ├── benchmark_plan_validation.csv
│   │   └── mongodb_candidate_validation.csv
│   ├── ldbc_snb_final_analytical_matrix_official/
│   │   ├── snb_final_analytical_matrix.csv
│   │   └── snb_final_matrix_validation.csv
│   ├── ldbc_snb_activation_official/
│   │   ├── snb_activation_matrix.csv
│   │   ├── snb_activation_summary.csv
│   │   └── activation_validation.csv
│   ├── ldbc_snb_structural_matrix_official/
│   │   ├── snb_structural_matrix_official.csv
│   │   ├── snb_rc_metrics.csv
│   │   └── snb_corrected_depth.csv
│   ├── ldbc_snb_update_volatility_official/
│   └── ldbc_snb_observed_sharedness_official/
└── results/
    └── ldbc_snb_sf0_1_full_fiben_format_clean/
        ├── benchmark_aggregate_results.csv
        ├── benchmark_raw_results.csv
        ├── candidate_load_summary.csv
        ├── scale_db_initialization_summary.csv
        ├── benchmark_run_manifest.json
        └── execution.log
```

---

## 4. Files that should be committed to GitHub

Commit these files:

```text
README.md
requirements.txt
docker-compose.yml
notebooks/ldbc_snb_schema_lens_methodology.ipynb
scripts/run_ldbc_snb_mongo_benchmark.py
scripts/validate_ldbc_snb_results.py
benchmark_artifacts_dir/ldbc_snb_mongo_configurations/*.json
benchmark_artifacts_dir/ldbc_snb_mongo_configurations/*.csv
benchmark_artifacts_dir/ldbc_snb_final_analytical_matrix_official/*.csv
benchmark_artifacts_dir/ldbc_snb_activation_official/*.csv
benchmark_artifacts_dir/ldbc_snb_structural_matrix_official/*.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/benchmark_aggregate_results.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/candidate_load_summary.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/scale_db_initialization_summary.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/benchmark_run_manifest.json
```

Optional but useful:

```text
results/ldbc_snb_sf0_1_full_fiben_format_clean/benchmark_raw_results.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/execution.log
```

Do **not** commit:

```text
data/
downloads/
*.tar.zst
*.tar.zst.*
*.duckdb
.venv/
__pycache__/
mongo_data/
```

---

## 5. Environment setup

Create a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

Minimal `requirements.txt`:

```text
pandas
numpy
pymongo
```

If running the methodology notebook, also install:

```text
duckdb
networkx
jupyterlab
```

---

## 6. MongoDB Docker setup

Use this `docker-compose.yml`:

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:8.0
    container_name: ldbc_mongodb
    restart: unless-stopped
    ports:
      - "27018:27017"
    environment:
      MONGO_INITDB_DATABASE: db_ldbc_snb
    volumes:
      - mongo_data:/data/db

volumes:
  mongo_data:
```

Start MongoDB:

```bash
docker compose up -d
```

Check the port:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

Expected:

```text
ldbc_mongodb   Up ...   0.0.0.0:27018->27017/tcp
```

Test MongoDB:

```bash
docker exec -it ldbc_mongodb mongosh --eval "db.adminCommand('ping')"
```

---

## 7. Run the smoke benchmark

Run this first:

```bash
python scripts/run_ldbc_snb_mongo_benchmark.py \
  --data-dir data/sf0.1 \
  --artifacts-dir benchmark_artifacts_dir/ldbc_snb_mongo_configurations \
  --results-dir results/ldbc_snb_sf0_1_smoke \
  --execution-plan benchmark_execution_plan_smoke.csv \
  --scale-label sf0.1 \
  --execution-db-prefix ldbc_snb_smoke \
  --mongo-host 127.0.0.1 \
  --mongo-port 27018 \
  --batch-size 5000 \
  --repetitions 2 \
  --run-phase cold hot \
  --force-rebuild-db \
  --verbose
```

---

## 8. Run the full benchmark

The validated final execution used:

```bash
python scripts/run_ldbc_snb_mongo_benchmark.py \
  --data-dir data/sf0.1 \
  --artifacts-dir benchmark_artifacts_dir/ldbc_snb_mongo_configurations \
  --results-dir results/ldbc_snb_sf0_1_full_fiben_format_clean \
  --execution-plan benchmark_execution_plan.csv \
  --scale-label sf0.1 \
  --execution-db-prefix ldbc_snb_exec_clean \
  --mongo-host 127.0.0.1 \
  --mongo-port 27018 \
  --batch-size 5000 \
  --repetitions 10 \
  --run-phase cold hot \
  --force-rebuild-db \
  --verbose
```

Expected counts:

```text
64 candidates
10 repetitions
2 phases
1280 raw executions
128 aggregate rows
64 load rows
```

---

## 9. Validate the benchmark output

```bash
python - <<'PY'
import pandas as pd
from pathlib import Path

results_dir = Path("results/ldbc_snb_sf0_1_full_fiben_format_clean")

raw = pd.read_csv(results_dir / "benchmark_raw_results.csv")
agg = pd.read_csv(results_dir / "benchmark_aggregate_results.csv")
load = pd.read_csv(results_dir / "candidate_load_summary.csv")

print("Raw rows:", len(raw))
print("Aggregate rows:", len(agg))
print("Load rows:", len(load))

print("\nExecution status:")
print(raw["execution_status"].value_counts(dropna=False))

print("\nSuccess:")
print(raw["success"].value_counts(dropna=False))

print("\nLoad status:")
print(load["load_status"].value_counts(dropna=False))

print("\nFailed query executions:")
print(raw[raw["success"] == False].head(20))

print("\nFailed loads:")
print(load[load["load_status"] != "completed"].head(20))
PY
```

Expected final result:

```text
Raw rows: 1280
Aggregate rows: 128
Load rows: 64

Execution status:
completed    1280

Success:
True    1280

Load status:
completed    64
```

---

## 10. Important runner fixes

The runner includes three important fixes discovered during validation.

### 10.1 Duplicate LDBC relationship column names

In the raw CSV file `person_knows_person`, pandas may read the second `Person.id` as:

```text
Person.id.1
```

The runner must convert this to:

```text
person2_id
```

Otherwise IC1-IC5 return zero documents.

Correct loaded document:

```javascript
{
  person1_id: "...",
  person2_id: "...",
  creation_date: "..."
}
```

### 10.2 Semantic query parameter pool

The runner does not choose the first arbitrary `person_id`. It builds query-specific parameter pools:

- persons with friends for IC1/IS3;
- persons whose friends have messages for IC2/IC3;
- persons whose friends have tagged posts for IC4/IC6;
- persons whose friends are forum members for IC5;
- persons whose posts/comments have likes for IC7.

This avoids valid queries returning zero documents only because the selected person has no relevant paths.

### 10.3 FIBEN-style output format

The runner writes the same style of outputs used in the FIBEN benchmark:

```text
benchmark_raw_results.csv
benchmark_aggregate_results.csv
candidate_load_summary.csv
scale_db_initialization_summary.csv
benchmark_run_manifest.json
execution.log
```

---

## 11. Final SF0.1 results summary

Final valid execution:

```text
Raw rows: 1280
Aggregate rows: 128
Load rows: 64
Completed executions: 1280
Successful executions: 1280
Completed loads: 64
Failed loads: 0
Failed query executions: 0
```

Design-space reduction analysis on hot p95 latency:

```text
Average DSR: 0.7136
Top-1 preservation by activated family: 1.0
Mean activated regret: 0.0
Mean primary regret: 0.0253
```

Interpretation:

- the activated family preserved the best observed configuration for all benchmarked queries;
- the activated configurations reduced the G0-G9 design space by about 71.4% on average;
- primary configurations were best for most queries;
- secondary affected configurations were important for IC5, IC7, and IS2;
- no control configuration was the best observed candidate.

Representative secondary-affected wins:

```text
IC5 -> G7 containment_baseline
IC7 -> G4 explicit_edge_collection
IS2 -> G6 referenced_or_reverse_indexed_edges
```

---

## 12. Analyze reduction metrics

Use this code after a full benchmark:

```python
import pandas as pd
import numpy as np
from pathlib import Path

results_dir = Path("results/ldbc_snb_sf0_1_full_fiben_format_clean")
agg = pd.read_csv(results_dir / "benchmark_aggregate_results.csv")

agg["official_id"] = agg["query_name"].str.extract(r"^(IC\d+|IS\d+|INS\d+)")
hot = agg[agg["run_phase"] == "hot"].copy()

rows = []

for query_name, grp in hot.groupby("query_name"):
    best_all = grp.loc[grp["p95_latency_ms"].idxmin()]
    activated = grp[grp["final_benchmark_group"] != "control"]
    primary = grp[grp["final_benchmark_group"] == "primary"]

    best_activated = activated.loc[activated["p95_latency_ms"].idxmin()]

    if len(primary) > 0:
        best_primary = primary.loc[primary["p95_latency_ms"].idxmin()]
        primary_regret = (
            best_primary["p95_latency_ms"] - best_all["p95_latency_ms"]
        ) / best_all["p95_latency_ms"]
    else:
        best_primary = None
        primary_regret = np.nan

    n_C = 10
    n_A = activated["candidate_id"].nunique()
    dsr = 1 - (n_A / n_C)

    rows.append({
        "official_id": best_all["official_id"],
        "query_name": query_name,
        "n_tested_configs": grp["candidate_id"].nunique(),
        "n_activated_configs": n_A,
        "DSR": dsr,
        "best_config": best_all["g_class"],
        "best_group": best_all["final_benchmark_group"],
        "best_design_pattern": best_all["design_pattern"],
        "best_p95_ms": best_all["p95_latency_ms"],
        "top1_preserved_by_activated": (
            best_activated["candidate_id"] == best_all["candidate_id"]
        ),
        "activated_regret": (
            best_activated["p95_latency_ms"] - best_all["p95_latency_ms"]
        ) / best_all["p95_latency_ms"],
        "best_primary_config": None if best_primary is None else best_primary["g_class"],
        "best_primary_p95_ms": None if best_primary is None else best_primary["p95_latency_ms"],
        "primary_regret": primary_regret,
    })

analysis_df = pd.DataFrame(rows).sort_values("official_id")

print("Average DSR:", analysis_df["DSR"].mean())
print("Top-1 preservation:", analysis_df["top1_preserved_by_activated"].mean())
print("Mean activated regret:", analysis_df["activated_regret"].mean())
print("Mean primary regret:", analysis_df["primary_regret"].dropna().mean())

analysis_df.to_csv(results_dir / "schemalens_reduction_analysis.csv", index=False)
```

---

## 13. How to reproduce with other scale factors

For another scale factor, for example `sf1`, `sf3`, or `sf10`, repeat the same process with the corresponding LDBC files.

Recommended data layout:

```text
data/sf1/
├── social_network-sf1-CsvMergeForeign-StringDateFormatter/
├── social_network-sf1-numpart-1/
└── substitution_parameters-sf1/
```

Then run the same runner, changing only:

```text
--data-dir
--results-dir
--scale-label
--execution-db-prefix
```

Example for SF1:

```bash
python scripts/run_ldbc_snb_mongo_benchmark.py \
  --data-dir data/sf1 \
  --artifacts-dir benchmark_artifacts_dir/ldbc_snb_mongo_configurations \
  --results-dir results/ldbc_snb_sf1_full_fiben_format_clean \
  --execution-plan benchmark_execution_plan.csv \
  --scale-label sf1 \
  --execution-db-prefix ldbc_snb_sf1_exec_clean \
  --mongo-host 127.0.0.1 \
  --mongo-port 27018 \
  --batch-size 5000 \
  --repetitions 10 \
  --run-phase cold hot \
  --force-rebuild-db \
  --verbose
```

For larger scale factors, start with smoke:

```bash
python scripts/run_ldbc_snb_mongo_benchmark.py \
  --data-dir data/sf1 \
  --artifacts-dir benchmark_artifacts_dir/ldbc_snb_mongo_configurations \
  --results-dir results/ldbc_snb_sf1_smoke \
  --execution-plan benchmark_execution_plan_smoke.csv \
  --scale-label sf1 \
  --execution-db-prefix ldbc_snb_sf1_smoke \
  --mongo-host 127.0.0.1 \
  --mongo-port 27018 \
  --batch-size 5000 \
  --repetitions 2 \
  --run-phase cold hot \
  --force-rebuild-db \
  --verbose
```

### Methodologically correct route for other SFs

If the goal is only to compare runtime under the same activated configurations, reuse:

```text
benchmark_artifacts_dir/ldbc_snb_mongo_configurations/
```

and change the data directory.

If the goal is to fully reapply the methodology per scale factor, rerun the notebook blocks that depend on observed data:

```text
data validation and row counts
update volatility extraction
observed sharedness extraction
final analytical matrix
G0-G9 activation
MongoDB candidate generation
benchmark plan export
```

The schema and official workload definitions can usually be reused because the conceptual model is the same. However, observed sharedness and update volatility should be recomputed because their values may change with scale.

---

## 14. Notes for larger scale factors

For larger SFs:

- use `--batch-size 5000` first;
- keep MongoDB on a dedicated port, e.g. `27018`;
- ensure enough disk space for MongoDB databases;
- run smoke first;
- monitor memory with `free -h`;
- monitor Docker with `docker stats ldbc_mongodb`;
- do not use very large batch sizes such as `300000`, because they may cause MongoDB connection resets.

Recommended initial full-run settings:

```text
SF0.1: batch-size 5000, repetitions 10
SF1:   batch-size 5000, repetitions 10
SF3+:  batch-size 2000 or 5000, repetitions 5 or 10 depending on time
```

---

## 15. Citation note

If this repository is used in a paper, cite the methodology as the SchemaLens workflow: EER/workload analytical matrix, semantic activation of G0-G9 MongoDB configuration families, and side-effect-aware evaluation using primary, secondary affected, and control query groups.
