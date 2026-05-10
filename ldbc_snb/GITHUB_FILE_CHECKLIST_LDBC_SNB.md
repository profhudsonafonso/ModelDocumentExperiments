# GitHub File Checklist — LDBC SNB SchemaLens Reproduction

## Commit these files

```text
README.md
requirements.txt
docker-compose.yml
notebooks/ldbc_snb_schema_lens_methodology.ipynb
scripts/run_ldbc_snb_mongo_benchmark.py
scripts/validate_ldbc_snb_results.py
benchmark_artifacts_dir/ldbc_snb_mongo_configurations/
benchmark_artifacts_dir/ldbc_snb_final_analytical_matrix_official/
benchmark_artifacts_dir/ldbc_snb_activation_official/
benchmark_artifacts_dir/ldbc_snb_structural_matrix_official/
results/ldbc_snb_sf0_1_full_fiben_format_clean/benchmark_aggregate_results.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/candidate_load_summary.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/scale_db_initialization_summary.csv
results/ldbc_snb_sf0_1_full_fiben_format_clean/benchmark_run_manifest.json
```

## Do not commit

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

## Optional

Commit `benchmark_raw_results.csv` only if it is small enough and useful for reproducibility.
For larger scale factors, keep raw results outside GitHub or publish them as a release artifact.
