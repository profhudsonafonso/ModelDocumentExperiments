# IMDb SchemaLens Artifact

This folder contains the IMDb artifact used in the paper *Explainable Design-Space Reduction for Workload-Aware Document Schema Selection*. The artifact supports the reproduction of the IMDb methodology inputs, MongoDB benchmark execution, and aggregate results used in the paper.

## Folder structure

```text
imdb/
  README.md
  requirements.txt
  docs/
    IMDB_SCALE_0_25_0_50_1_SETUP.pdf
  inputs/
    document_variable_matrix.csv
    mongo_experiment_catalog.csv
    benchmark_execution_template.csv
  notebooks/
    IMDB_sf_commented_english.ipynb
    Implementation_framework.ipynb
  scripts/
    benchmark/
      run_mongo_benchmark_option_b_incremental.py
    analysis/
  results/
    sf0_25/
      benchmark_results/
    sf0_5/
      benchmark_results/
    sf1/
      benchmark_results/
  article_outputs/



Dataset

The raw IMDb TSV files are not included in this repository because of size and licensing constraints. The experiments use the IMDb non-commercial dataset files:

name.basics.tsv
title.akas.tsv
title.basics.tsv
title.crew.tsv
title.episode.tsv
title.principals.tsv
title.ratings.tsv

The scale-factor folders used by the benchmark runner are expected to contain these TSV files.

Default paths used in the benchmark script:

sf0.25 -> /home/hudson/Documents/framework_test/imdb/data/sf_025
sf0.5  -> /home/hudson/Documents/framework_test/imdb/data/sf_050
sf1    -> /home/hudson/Documents/framework_test/imdb/data/sf_1

If your local paths are different, update the IMDB_SF_PATHS dictionary in:

scripts/benchmark/run_mongo_benchmark_option_b_incremental.py
Environment

The benchmark was executed with:

MongoDB 8.0.20
Docker container
Ubuntu 24.04.4 LTS
Intel Core i7 CPU
62 GB RAM
1 TB Lexar NM620 NVMe SSD

Python dependencies are listed in:

requirements.txt

Install them with:

pip install -r requirements.txt
Inputs

The main input files are:

inputs/document_variable_matrix.csv
inputs/mongo_experiment_catalog.csv
inputs/benchmark_execution_template.csv

Their roles are:

document_variable_matrix.csv: analytical matrix produced by the SchemaLens methodology.
mongo_experiment_catalog.csv: MongoDB candidate configurations generated from the activated families.
benchmark_execution_template.csv: benchmark execution plan containing query names, query groups, run phases, and repetitions.
Running the benchmark

The benchmark script is:

scripts/benchmark/run_mongo_benchmark_option_b_incremental.py

Example command for one scale factor:

python scripts/benchmark/run_mongo_benchmark_option_b_incremental.py \
  --catalog-csv inputs/mongo_experiment_catalog.csv \
  --template-csv inputs/benchmark_execution_template.csv \
  --results-dir results/sf0_25/benchmark_results \
  --scale-label sf0.25 \
  --run-phase cold hot \
  --batch-size 10000 \
  --force-rebuild-scale-db

For Windows, run the same command from the imdb/ folder using python and Windows paths if needed.

The benchmark uses 10 cold-run and 10 hot-run repetitions per candidate/query pair, as specified in the execution template.

Existing benchmark results

The repository includes aggregate and raw benchmark results for the three IMDb scale factors:

results/sf0_25/benchmark_results/
results/sf0_5/benchmark_results/
results/sf1/benchmark_results/

Each scale folder contains:

benchmark_aggregate_results.csv
benchmark_raw_results.csv
collection_swap_summary.csv
scale_db_initialization_summary.csv

The aggregate results include:

average latency
median latency
p95 latency
p99 latency
minimum and maximum latency
standard deviation
average documents returned
average documents written
Reproducing paper results

The paper tables for the IMDb case study can be checked from the aggregate result files:

Table 9 uses the hot-run results for QG6_EpisodesOfSeries across sf0.25, sf0.5, and sf1.
Tables 10 and 11 use the containment-family trade-off results for G7, G8, and G9.
The IMDb rows of Table 12 use the representative cases for containment, association, and associative patterns.

The article_outputs/ folder is reserved for final CSV/LaTeX exports used directly in the paper.

Notes

This artifact focuses on the IMDb portion of the SchemaLens evaluation. FIBEN and LDBC SNB follow the same organization pattern in their corresponding folders.


